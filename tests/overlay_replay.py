"""Compare two author chains in the public 1IGT deposition."""
import argparse
import base64
import json
import math
import tempfile
from pathlib import Path

import numpy as np
from Bio import SeqIO
from Bio.PDB.MMCIF2Dict import MMCIF2Dict
from playwright.sync_api import expect

from desktop_replay import run
from file_replay import choose_file
from antibody_insight import imports, project, structures


def deposited_ca(path,low=1,high=444):
    cif=MMCIF2Dict(str(path))
    fields="auth_asym_id label_seq_id label_atom_id label_alt_id occupancy Cartn_x Cartn_y Cartn_z"
    atoms={chain:{} for chain in ("B","D")}
    for chain,index,name,alt,occ,*xyz in zip(*(cif["_atom_site."+k] for k in fields.split())):
        if chain in atoms and index.isdecimal() and low<=int(index)<=high and name=="CA" and alt=="." and float(occ)>0:
            atoms[chain][int(index)]=tuple(round(float(v),3) for v in xyz)
    shared=sorted(atoms["B"].keys() & atoms["D"].keys())
    a,b=(np.array([atoms[chain][i] for i in shared]) for chain in ("B","D"))
    a-=a.mean(axis=0)
    b-=b.mean(axis=0)
    # Centered energy and signed singular values give RMSD independently of the applied transform.
    covariance=b.T@a
    singular=np.linalg.svd(covariance,compute_uv=False)
    floor=((a*a).sum()+(b*b).sum()-2*(sum(singular[:2])+np.sign(np.linalg.det(covariance))*singular[2]))/len(shared)
    return len(shared),math.sqrt(max(0,floor))


def verify(public,output,executable=None):
    cif=public/"1IGT.cif"
    count,rmsd=deposited_ca(cif)
    region_n,region_rmsd=deposited_ca(cif,1,110)
    with tempfile.TemporaryDirectory() as tmp:
        db=Path(tmp)/"Deposited chain overlay.ais"
        source=Path(tmp)/"Chain B and D.faa"
        ref=next(r for r in SeqIO.parse(public/"1IGT.faa","fasta") if len(r.seq)==444)
        source.write_text(">1IGT\n"+str(ref.seq)+"\n")
        project.create_project(db)
        project.commit(db,imports.parse_file(source),[{"candidate":"1IGT","component":"Heavy chain"}])
        key=project.summary(db)["components"][0]["id"]
        detail=project.component_detail(db,key)
        packet=structures.preview(cif,detail)
        for chain in ("B","D"):
            structures.save(db,packet,chain,"Experimental")
        keys=project.component_detail(db,key)["structures"]
        target=json.dumps([key,keys[1]["id"]],separators=(",",":"))
        caption=f"{count}/444 paired positions with Cα · RMSD {rmsd:.3f} Å"
        destination=Path(tmp)/"Overlay.png"
        expected_camera=[]
        def exercise(page,pid):
            page.get_by_role("button",name="Heavy chain",exact=False).click()
            page.locator("#style").select_option("Cartoon")
            page.locator("#movingModel").select_option(target)
            expect(page.locator("#fitSummary")).to_contain_text(caption,timeout=25000)
            page.locator("#pos").fill("53")
            page.locator("#pos").press("Enter")
            expect(page.locator("#coordinate")).to_have_text("Chain B · 52A · sequence 53")
            expect(page.locator("#fitSummary")).to_contain_text("Overlay D 52A")
            page.locator("#fit").click()
            page.screenshot(path=str(output.with_suffix(".png")))
            page.locator("#toggleOverlay").click()
            expect(page.locator("#toggleOverlay")).to_have_attribute("aria-pressed","false")
            page.locator("#toggleOverlay").click()
            expect(page.locator("#toggleOverlay")).to_have_attribute("aria-pressed","true")
            page.locator("#fitFirst").fill("1")
            page.locator("#fitLast").fill("110")
            page.locator("#overlayRange button").click()
            expect(page.locator("#fitSummary")).to_contain_text(f"{region_n}/110 paired positions with Cα · RMSD {region_rmsd:.3f} Å")
            page.locator("#fit").click()
            page.screenshot(path=str(output.with_name("overlay-region.png")))
            page.locator("#structureLayout").select_option("parallel")
            expect(page.locator("#overlayMolecule canvas")).to_be_visible()
            canvas=page.locator("#overlayMolecule canvas").bounding_box()
            page.mouse.move(canvas["x"]+canvas["width"]/3,canvas["y"]+canvas["height"]/2)
            before=page.evaluate("viewer.getView()")
            page.mouse.wheel(0,-200)
            page.wait_for_function("prior=>viewer.getView().some((v,i)=>Math.abs(prior[i]-v)>1e-6)",arg=before)
            assert np.allclose(page.evaluate("viewer.getView()"),page.evaluate("parallelViewer.getView()"),atol=1e-6)
            page.screenshot(path=str(output.with_name("overlay-parallel.png")))
            page.locator("#structureLayout").select_option("overlay")
            page.locator("#focusResidue").click()
            page.locator("#exportStructure").click()
            choose_file(pid,destination)
            expect(page.locator("#status")).to_contain_text("Structure image saved")
            pixels=page.evaluate("""async encoded=>{
              const image=new Image();image.src="data:image/png;base64,"+encoded;await image.decode();
              const canvas=document.createElement("canvas");canvas.width=image.width;canvas.height=image.height;
              const context=canvas.getContext("2d");context.drawImage(image,0,0);
              const values=context.getImageData(0,200,canvas.width,canvas.height-200).data;
              let colored=0;
              for(let i=0;i<values.length;i+=4)if(values[i]<180 && (values[i+1]>values[i]+12 || values[i+2]>values[i]+12))colored++;
              return colored;
            }""",base64.b64encode(destination.read_bytes()).decode())
            assert pixels>100,pixels
            output.with_name("overlay-export.png").write_bytes(destination.read_bytes())
            expected_camera.extend(page.evaluate("viewer.getView()"))
            page.locator("#bookmarks").click()
            page.locator("#bookmarkName").fill("Paired residue and fit range")
            page.locator("#addBookmark").click()
            expect(page.locator("#bookmarkStatus")).to_have_text("Observation saved.")
            page.locator("#addBookmark").click()
            expect(page.locator("#bookmarkStatus")).to_contain_text("already exists")
            page.locator("#bookmarkDialog .close").click()
            page.locator("#movingModel").select_option("")
            page.locator("#pos").fill("12")
            page.locator("#pos").press("Enter")
            page.locator("#note").click()
            page.locator("#noteText").fill("Later project note")
            page.locator("#saveNote").click()
            expect(page.locator("#noteDialog")).not_to_be_visible()
        result=run(db,output.parent,False,executable,exercise)
        def restored(page,_pid):
            expect(page.locator("#pos")).to_have_value("12")
            page.locator("#bookmarks").click()
            page.locator("#bookmarkList").select_option(label="Paired residue and fit range")
            page.locator("#openBookmark").click()
            expect(page.locator("#fitSummary")).to_contain_text(f"{region_n}/110 paired positions with Cα · RMSD {region_rmsd:.3f} Å",timeout=25000)
            expect(page.locator("#coordinate")).to_have_text("Chain B · 52A · sequence 53")
            actual=page.evaluate("viewer.getView()")
            assert len(actual)==len(expected_camera)==8 and np.allclose(actual,expected_camera,atol=1e-6,rtol=0)
            page.locator("#note").click()
            expect(page.locator("#noteText")).to_have_value("Later project note")
        result["restart"]=run(db,output.parent,True,executable,restored)
    result.update(entry="1IGT",fixed="B",moving="D",matched=count,reference_rmsd_angstrom=rmsd,
                  selected=["B 52A","D 52A"],region=[1,110],region_matched=region_n,region_rmsd_angstrom=region_rmsd,
                  bookmark_camera_restored=True,synchronized_side_by_side=True,
                  structure_export="PNG with rendered coordinates and context")
    output.write_text(json.dumps(result,indent=2),encoding="utf-8")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("public",type=Path)
    parser.add_argument("output",type=Path)
    parser.add_argument("--executable",type=Path)
    a=parser.parse_args()
    verify(a.public,a.output,a.executable)
