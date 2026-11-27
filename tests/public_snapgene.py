"""Offline interoperability check against Biopython's published SnapGene fixtures."""
import argparse
import hashlib
import json
import tempfile
from pathlib import Path

from openpyxl import Workbook
from playwright.sync_api import expect
from file_replay import choose_file
from desktop_replay import run
from antibody_insight import imports, project


def verify(directory,output,executable=None):
    sample=directory/"sample-d.dna"
    packet=imports.parse_file(sample)
    assert packet["sha"]=="9f2b69c06c2a49f23bd41d02672fbd4ee037ce8b575e754be79bac9834130fa3"
    record,=packet["records"]
    # Intervals and arrow attributes checked against the raw source XML.
    expected=[[[500,700,None]],[[50,150,1]],[[701,720,None]],[[721,740,None]]]
    assert [f["parts"] for f in record["features"]]==expected
    assert record["topology"]=="linear" and len(record["sequence"])==1000
    circles={}
    for name,intervals in [("looped_feature",[(3,10),(1,2)]),("looped_feature_origin",[(1,10)])]:
        p=imports.parse_file(directory/(name+".dna"))
        item,=p["records"]
        assert item["topology"]=="circular"
        assert [tuple(part[:2]) for part in item["features"][0]["parts"]]==intervals
        circles[name]=dict(sha256=p["sha"],ranges=intervals)
    with tempfile.TemporaryDirectory() as tmp:
        db=Path(tmp)/"Format comparison.ais"
        project.create_project(db)
        sheet=Path(tmp)/"Source length.xlsx"
        workbook=Workbook()
        workbook.active.append(imports.OBS_COLUMNS)
        workbook.active.append(["Sample","DNA length",1000,"nt","Computed","","","Published sample D fixture",""])
        workbook.save(sheet)

        def exercise(page,pid):
            for path in (sample,sheet):
                page.locator("#import").click()
                page.locator("#chooseFile").click()
                choose_file(pid,path)
                expect(page.locator("#preview")).to_contain_text(path.name)
                if path==sample:
                    page.locator("#preview summary").click()
                    expect(page.locator("#preview")).to_contain_text("500–700 (direction unspecified)")
                    expect(page.locator("#preview")).to_contain_text("50–150 (+)")
                page.locator("#confirm").click()
                expect(page.locator("#importDialog")).not_to_be_visible()
            page.locator("#tree .part").click()
            expect(page.locator("#identity")).to_contain_text("Sample / sample-d")
            page.locator("#metric").select_option(index=0)
            expect(page.locator("#plot .point")).to_have_count(1)
            page.get_by_text("Annotations (4)",exact=True).click()
            page.get_by_role("button",name="FeatureA · promoter").click()
            expect(page.locator("#pos")).to_have_value("50")
            overview=project.summary(db)
            assert len(overview["candidates"])==len(overview["components"])==len(overview["observations"])==1
            actual=project.component_detail(db,overview["components"][0]["id"])
            assert actual["seq"]==record["sequence"] and actual["hash"]==packet["sha"]
            assert overview["observations"][0]["value"]==len(actual["seq"])
            page.screenshot(path=str(output.with_suffix(".png")))
        result=run(db,output.parent,False,executable,exercise)
        result.update(source="Biopython 1.88 test files",sha256=packet["sha"],length=1000,
                      sequence_sha256=hashlib.sha256(record["sequence"].encode()).hexdigest(),
                      features=expected,circular=circles,spreadsheet="Independently entered sequence length, no assay")
        output.write_text(json.dumps(result,indent=2),encoding="utf-8")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory",type=Path)
    parser.add_argument("output",type=Path)
    parser.add_argument("--executable",type=Path)
    args=parser.parse_args()
    verify(args.directory,args.output,args.executable)
