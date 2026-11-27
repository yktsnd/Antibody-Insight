"""Verify a hand-calculated correlation, click-through and an exported workbook."""
import argparse
import csv
import json
import math
import struct
import tempfile
from pathlib import Path

from openpyxl import load_workbook
from playwright.sync_api import expect
from desktop_replay import run
from file_replay import choose_file
from antibody_insight import imports, project


def verify(output,executable=None):
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp)
        db=root/"Candidate comparisons.ais"
        project.create_project(db)
        seq=root/"Sequences.csv"
        seq.write_text("candidate,component,kind,sequence\n"+"".join(f"{c},Chain,AA,MA\n" for c in "ABCDE"))
        project.commit(db,imports.parse_file(seq))
        data=root/"Synthetic series.csv"
        with data.open("w",newline="") as dest:
            writer=csv.writer(dest)
            writer.writerow(imports.OBS_COLUMNS)
            for c,x,y in [("A",0,1),("B",1,3),("C",2,2),("D","",8),("E",1,9)]:
                writer.writerow([c,"X input",x,"a.u.","Computed","","condition X","Synthetic X",""])
                writer.writerow([c,"Y readout",y,"mg","Measured","=Sample "+c,"condition Y","Synthetic Y",""])
            writer.writerow(["E","X input",2,"a.u.","Computed","","condition X","Synthetic X",""])
        project.commit(db,imports.parse_file(data))
        workbook=root/"Comparison.xlsx"
        def exercise(page,pid):
            expect(page.locator("#metric")).to_be_enabled()
            page.locator("#metric").select_option(label="Y readout · mg · Measured · condition Y · Synthetic Y")
            page.locator("#xMetric").select_option(label="X · X input · a.u. · Computed · condition X · Synthetic X")
            expect(page.locator("#plotInfo")).to_have_text("Pearson r 0.500 · 3 paired candidates · 2 excluded")
            points=page.locator("#plot .point")
            expect(points).to_have_count(3)
            # Plotly handles clicks on the drag layer, using the screen coordinates of the marker.
            box=points.nth(1).bounding_box()
            page.mouse.click(box["x"]+box["width"]/2,box["y"]+box["height"]/2)
            expect(page.locator("#identity")).to_have_text("B / Chain")
            page.screenshot(path=str(output.with_suffix(".png")))
            page.locator("#measurementDetails").click()
            expect(page.locator("#recordRows")).to_contain_text("Multiple values")
            expect(page.locator("#recordRows")).to_contain_text("=Sample B")
            page.locator("#recordsDialog .close").click()
            page.locator("#exportPlot").click()
            png=root/"Figure.png"
            choose_file(pid,png)
            expect(page.locator("#status")).to_contain_text("Plot image saved")
            figure=png.read_bytes()
            assert figure[:8]==b"\x89PNG\r\n\x1a\n" and struct.unpack(">II",figure[16:24])==(1920,1200)
            output.with_name("comparison-figure.png").write_bytes(figure)
            page.locator("#exportComparison").click()
            choose_file(pid,workbook)
            expect(page.locator("#status")).to_contain_text("workbook exported")
        result=run(db,output.parent,False,executable,exercise)
        book=load_workbook(workbook,read_only=True,data_only=False)
        try:
            assert book.sheetnames==["Comparison","Candidates","Source records"]
            pairs=list(book["Candidates"].values)[1:]
            assert [(p[1],p[2],p[4],p[6]) for p in pairs]==[
                ("A",0,1,True),("B",1,3,True),("C",2,2,True),("D",None,8,False),("E",None,9,False)]
            assert pairs[-2][3]=="Missing" and pairs[-1][3]=="Multiple values"
            method={r[0]:r[1] for r in book["Comparison"].values}
            assert math.isclose(method["Pearson r"],0.5) and method["Included candidates"]==3
            records=list(book["Source records"].rows)[1:]
            assert len(records)==11
            assert sum(row[10].data_type=="s" and str(row[10].value).startswith("=") for row in records)==5
            expected_hash=imports.parse_file(data)["sha"]
            assert all(row[-2].value==expected_hash and row[-1].value for row in records)
        finally:
            book.close()
        output.with_suffix(".xlsx").write_bytes(workbook.read_bytes())
        result.update(pearson_r=0.5,paired_candidates=3,excluded=["D: missing X","E: ambiguous X"],
                      selected_candidate="B",export_records=11,figure_pixels=[1920,1200])
        output.write_text(json.dumps(result,indent=2))


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output",type=Path)
    parser.add_argument("--executable",type=Path)
    args=parser.parse_args()
    verify(args.output,args.executable)
