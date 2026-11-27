"""Replay a substitution after an indel and an ambiguous alignment in the desktop app."""
import argparse
import json
import tempfile
from pathlib import Path

from desktop_replay import run
from playwright.sync_api import expect
from antibody_insight import imports, project, structures


def verify(output, executable=None):
    with tempfile.TemporaryDirectory() as tmp:
        directory=Path(tmp)
        db=directory/"Synthetic sequence comparison.ais"
        project.create_project(db)
        table=directory/"sequences.csv"
        table.write_text("candidate,component,kind,sequence\nVariant,Variant protein,AA,MGSK\nReference,Reference protein,AA,MAGTK\nRepeat A,Long repeat,AA,AAAA\nRepeat B,Short repeat,AA,AAA\n")
        project.commit(db,imports.parse_file(table))
        parts={c["label"]:c["id"] for c in project.summary(db)["components"]}
        pdb=directory/"synthetic-reference.pdb"
        residues=[("MET",10," "),("ALA",11," "),("GLY",12," "),("THR",12,"A"),("LYS",13," ")]
        records=[f"ATOM  {i:5d}  CA  {aa} R{n:4d}{ins}   {i*3.4:8.3f}{0:8.3f}{0:8.3f}  1.00  0.00           C" for i,(aa,n,ins) in enumerate(residues,1)]
        pdb.write_text("\n".join(records)+"\nEND   \n")
        ref=project.component_detail(db,parts["Reference protein"])
        structures.save(db,structures.preview(pdb,ref),"R","Reference")
        def exercise(page,_pid):
            page.get_by_role("button",name="Variant protein",exact=False).click()
            page.locator("#reference").select_option(parts["Reference protein"])
            page.get_by_role("button",name="Align sequences",exact=True).click()
            page.locator("#pos").fill("3")
            page.locator("#pos").press("Enter")
            expect(page.locator("#sequenceBody")).to_contain_text("Query 3 S → reference 4 T")
            expect(page.locator("#sequenceBody")).to_contain_text("3/4 paired columns")
            page.get_by_role("button",name="Inspect aligned reference",exact=True).click()
            expect(page.locator("#referenceScope")).to_contain_text("Reference coordinates for Variant / Variant protein")
            expect(page.locator("#coordinate")).to_have_text("Chain R · 12A · sequence 4")
            page.screenshot(path=str(output.parent/"aligned-reference.png"))
            page.get_by_role("button",name="Return to aligned candidate").click()
            expect(page.locator("#pos")).to_have_value("3")
            expect(page.locator("#coordinate")).to_contain_text("No coordinates")
            page.get_by_role("button",name="Long repeat",exact=False).click()
            page.locator("#reference").select_option(parts["Short repeat"])
            page.get_by_role("button",name="Align sequences",exact=True).click()
            expect(page.locator("#sequenceBody")).to_contain_text("Multiple optimal alignments")
            assert page.get_by_role("button",name="Inspect aligned reference").count()==0
        result=run(db,output.parent,False,executable,exercise)
        result.update(query_position=3,reference_position=4,author="R 12A",ambiguous_transfer=False)
        output.write_text(json.dumps(result,indent=2),encoding="utf-8")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output",type=Path)
    parser.add_argument("--executable",type=Path)
    args=parser.parse_args()
    verify(args.output,args.executable)
