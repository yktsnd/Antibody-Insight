"""Replay reported means and individual measurements through the desktop UI."""
import argparse
import csv
import io
import json
import math
import tempfile
from pathlib import Path

from playwright.sync_api import expect
from desktop_replay import ROOT, run
from antibody_insight import imports, project


def verify(output, executable=None):
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "Measurement comparison.ais"
        project.create_project(db)
        project.commit(db, imports.parse_file(ROOT / "examples/sequences.csv"))
        text = io.StringIO()
        with (ROOT / "examples/measurement-series.csv").open(newline="") as records:
            csv.writer(text, delimiter="\t").writerows(csv.reader(records))

        def exercise(page, _pid):
            def enter():
                page.locator("#import").click()
                page.locator("#manualEntry summary").click()

            enter()
            page.locator("#measurementText").fill(text.getvalue())
            page.locator("#reviewPaste").click()
            expect(page.locator("#preview")).to_contain_text("Submitted result")
            page.locator("#confirm").click()
            expect(page.locator("#importDialog")).not_to_be_visible()
            page.locator("#metric").select_option(index=0)
            expect(page.locator("#plotInfo")).to_contain_text("2 means")
            expect(page.locator("#plot .point")).to_have_count(2)
            expect(page.locator("#tree .candidate")).to_have_count(2)
            expect(page.locator("#tree summary").first).to_contain_text("2 AU")
            page.locator("#measureView").select_option("SEM")
            page.wait_for_function("Math.abs(document.querySelector('#plot').data[0].error_y?.array[0] - 0.5) < 1e-8")
            errors = page.locator("#plot").evaluate("el => el.data[0].error_y.array")
            assert sorted(errors) == [0.5, 2/math.sqrt(3)]
            page.screenshot(path=str(output.with_name("measurement-means.png")))
            page.locator("#measureView").select_option("individual")
            expect(page.locator("#plot .point")).to_have_count(3)
            page.locator("#tree .part").first.click()
            page.locator("#measurementDetails").click()
            expect(page.locator("#recordRows")).to_contain_text("Demo aliquot A4")
            expect(page.locator("#recordRows")).not_to_contain_text("Submitted result")
            page.screenshot(path=str(output.with_name("measurement-records.png")))
            page.locator("#recordsDialog .close").click()
            enter()
            form=page.locator("#measurementFields")
            for key,value in {"metric":"Input check","value":"9","unit":"AU","source":"Synthetic note"}.items():
                form.locator(f'[name="{key}"]').fill(value)
            form.locator('[name="statistic"]').select_option("Mean")
            page.locator("#reviewEntry").click()
            expect(page.locator("#preview")).to_contain_text("Entered measurement.tsv")
            page.locator("#confirm").click()
            expect(page.locator("#importDialog")).not_to_be_visible()
            rows=project.summary(db)
            assert len(rows["candidates"])==2 and len(rows["observations"])==6
            reported=next(r for r in rows["summaries"] if r["metric"]=="Input check")
            assert reported["origin"]=="Reported" and reported["value"]==9 and reported["n"] is None
        result=run(db,output.parent,False,executable,exercise)
        result.update(candidates=2,individual_points=3,calculated_mean=2,calculated_sd=2,
                      calculated_sem=2/math.sqrt(3),reported_sem=0.5,missing_observations=1)
        output.write_text(json.dumps(result,indent=2),encoding="utf-8")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output",type=Path)
    parser.add_argument("--executable",type=Path)
    args=parser.parse_args()
    verify(args.output,args.executable)
