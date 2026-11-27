"""Offline structure check using public 1IGT coordinates and its separately downloaded FASTA."""
import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path

from Bio.PDB.MMCIF2Dict import MMCIF2Dict
from playwright.sync_api import expect

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from antibody_insight import imports, project, structures
from desktop_replay import run


def verify(directory, output, executable=None):
    cif, fasta = directory/"1IGT.cif", directory/"1IGT.faa"
    source = MMCIF2Dict(str(cif))
    # The product uses _atom_site. Read a different table as the coordinate oracle.
    names = ("pdb_strand_id","seq_id","auth_seq_num","pdb_ins_code")
    scheme = {}
    for chain,seq,author,ins in zip(*(source["_pdbx_poly_seq_scheme."+k] for k in names),strict=True):
        scheme[chain,int(seq)] = [int(author), "" if ins=="." else ins]
    metadata = {"entry":"1IGT","cif_sha256":hashlib.sha256(cif.read_bytes()).hexdigest(),
                "fasta_sha256": hashlib.sha256(fasta.read_bytes()).hexdigest(),"chain_positions":{}}
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp)/"MAb231.ais"
        project.create_project(path)
        packet = imports.parse_file(fasta)
        bindings = [{"candidate":"MAb231","component":r["component"].split("|")[0]} for r in packet["records"]]
        project.commit(path,packet,bindings)
        for comp in project.summary(path)["components"]:
            detail = project.component_detail(path,comp["id"])
            coordinates = structures.preview(cif,detail)
            assert coordinates["mappings"]
            for chain,positions in coordinates["mappings"].items():
                assert positions == [scheme[chain,n] for n in range(1,len(positions)+1)]
                metadata["chain_positions"][chain] = len(positions)
            if "B" in coordinates["mappings"]:
                assert detail["seq"][52]=="N" and coordinates["mappings"]["B"][52]==[52,"A"]
                structures.save(path,coordinates,"B","Experimental")
                selected = comp["id"]
        with project.connection(path) as db:
            db.execute("INSERT INTO meta VALUES('view',?)",(json.dumps({"component":selected,"style":"Cartoon"}),))
        def exercise(page, _pid):
            expect(page.locator("#coordinate")).to_contain_text("Chain B",timeout=30000)
            page.locator("#pos").fill("53")
            page.locator("#pos").press("Enter")
            expect(page.locator("#coordinate")).to_have_text("Chain B · 52A · sequence 53")
            assert page.locator('[data-base="53"]').inner_text()=="N"
            page.screenshot(path=str(output.parent/"public-structure.png"))
        metadata["desktop_replay"]=run(path,output.parent,False,executable,exercise)
    output.write_text(json.dumps(metadata,indent=2),encoding="utf-8")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory",type=Path)
    parser.add_argument("output",type=Path)
    parser.add_argument("--executable",type=Path)
    args=parser.parse_args()
    verify(args.directory,args.output,args.executable)
