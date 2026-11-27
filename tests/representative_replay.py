"""Verify the structure supplying candidate metrics is independent of the viewer."""
import argparse
import json
import tempfile
from pathlib import Path

from playwright.sync_api import expect
from desktop_replay import ROOT, run
from file_replay import choose_file
from antibody_insight import example,project,structures


def verify(output,executable=None):
    with tempfile.TemporaryDirectory() as temporary:
        root=Path(temporary)
        db=root/"Representative structure.ais"
        project.create_project(db)
        example.populate(db)
        catalog=project.summary(db)
        key=catalog["state"]["component"]
        part=project.component_detail(db,key)
        owner=part["candidate"]
        coords=(ROOT/"examples/synthetic-peptide.pdb").read_bytes()
        packet=structures.parse_coordinates(coords,"Second model.pdb",part)
        structures.save(db,packet,"A","Predicted")
        original,alternative=[r["id"] for r in project.component_detail(db,key)["structures"]]
        for name,value in (("First",2.4),("Second",7.1)):
            (root/(name+".csv")).write_text(
                f"metric,value,unit,region,conditions,source\nDemo distance,{value},angstrom,Two residues,Synthetic condition,Synthetic source\n")
        def exercise(page,pid):
            expect(page.locator("#coordinate")).to_contain_text("Chain A")
            for model,name,coordinate in [(original,"First","synthetic-peptide.pdb"),(alternative,"Second","Second model.pdb")]:
                page.locator("#model").select_option(model)
                expect(page.locator("#structureMetrics")).to_be_enabled()
                page.locator("#import").click()
                page.locator("#chooseFile").click()
                choose_file(pid,root/(name+".csv"))
                expect(page.locator("#preview")).to_contain_text(coordinate)
                page.locator("#confirm").click()
                expect(page.locator("#importDialog")).not_to_be_visible()
                expect(page.locator("#structureMetrics")).to_be_enabled()
            assert page.locator("#metric option").filter(has_text="Demo distance").count()==0
            page.locator("#model").select_option(original)
            page.locator("#structureMetrics").click()
            expect(page.locator("#structureRows")).to_contain_text("2.4")
            page.locator("#setRepresentative").click()
            expect(page.locator("#representativeStatus")).to_contain_text("This structure supplies")
            page.locator("#structureDialog .close").click()
            series=page.locator("#metric option").filter(has_text="Demo distance")
            page.locator("#metric").select_option(series.get_attribute("value"))
            page.locator("#model").select_option(alternative)
            page.locator("#structureMetrics").click()
            expect(page.locator("#structureRows")).to_contain_text("7.1")
            expect(page.locator("#representativeStatus")).to_contain_text("A different structure")
            expect(page.locator("#tree .candidate").filter(has_text="Example A").locator("summary")).to_contain_text("2.4 angstrom")
            assert page.locator("#plot").evaluate("el=>el.data[0].y[0]")==2.4
            page.screenshot(path=str(output.with_suffix(".png")))
            page.locator("#structureDialog .close").click()
            page.locator("#note").click()
            page.locator("#saveNote").click()
            expect(page.locator("#noteDialog")).not_to_be_visible()
        receipt=run(db,output.parent,False,executable,exercise)
        def restored(page,_pid):
            expect(page.locator("#model")).to_have_value(alternative)
            expect(page.locator("#tree .candidate").filter(has_text="Example A").locator("summary")).to_contain_text("2.4 angstrom")
            page.locator("#structureMetrics").click()
            expect(page.locator("#structureRows")).to_contain_text("7.1")
            page.locator("#setRepresentative").click()
            expect(page.locator("#representativeStatus")).to_contain_text("This structure supplies")
            expect(page.locator("#tree .candidate").filter(has_text="Example A").locator("summary")).to_contain_text("7.1 angstrom")
            page.wait_for_function("document.querySelector('#plot').data?.[0].y?.[0]===7.1")
        receipt["restart"]=run(db,output.parent,True,executable,restored)
        overview=project.summary(db)
        assert overview["representatives"][owner]==alternative
        obs=[r for r in overview["observations"] if r["kind"]=="Structure computed"]
        assert len(obs)==1 and obs[0]["structure_id"]==alternative and obs[0]["value"]==7.1
        receipt.update(initial_value=2.4,viewed_value=7.1,plotted_while_viewing_alternative=2.4,
                       plotted_after_explicit_change=7.1)
    output.write_text(json.dumps(receipt,indent=2),encoding="utf-8")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output",type=Path)
    parser.add_argument("--executable",type=Path)
    a=parser.parse_args()
    verify(a.output,a.executable)
