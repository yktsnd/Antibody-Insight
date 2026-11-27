"""Time a real comparison request while sending two selection events in WebView2."""
import argparse
import csv
import json
import platform
import tempfile
from pathlib import Path

from playwright.sync_api import expect
from desktop_replay import run
from antibody_insight import imports, project


def verify(output,executable=None):
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp)
        db=root/"Candidate load check.ais"
        project.create_project(db)
        seq=root/"Sequences.csv"
        with seq.open("w",newline="") as handle:
            writer=csv.writer(handle)
            writer.writerow(imports.SEQ_COLUMNS)
            for i in range(300):
                writer.writerow([f"Bench {i:03}","Test chain","AA","MA"*100])
        project.commit(db,imports.parse_file(seq))
        readings=root/"Readings.csv"
        with readings.open("w",newline="") as handle:
            writer=csv.writer(handle)
            writer.writerow(imports.MEASUREMENT_COLUMNS)
            for i in range(300):
                for replicate in range(12):
                    writer.writerow([f"Bench {i:03}","Signal",i+replicate,"AU","Measured",f"Sample {i}-{replicate}",
                                     "Synthetic buffer","Fixture","","Set A","Individual","","",""])
        project.commit(db,imports.parse_file(readings))
        scalar=root/"Computed.csv"
        with scalar.open("w",newline="") as handle:
            writer=csv.writer(handle)
            writer.writerow(imports.OBS_COLUMNS)
            for i in range(300):
                writer.writerow([f"Bench {i:03}","Index",i,"AU","Computed","","","Fixture",""])
        project.commit(db,imports.parse_file(scalar))
        timings={}
        def exercise(page,_pid):
            expect(page.locator("#count")).to_have_text("300",timeout=45000)
            page.locator("#filter").fill("Bench 00")
            for label in ("Bench 001","Bench 002"):
                page.locator("#tree summary").filter(has_text=label).click()
            # Keep the real bridge invocation and response. Schedule normal click
            # handlers after it starts without introducing any delay into the computation.
            page.evaluate("""() => {
              const bridge=window.pywebview.api, original=bridge.compare_metrics;
              window.loadTimes={};
              bridge.compare_metrics=async(...args)=>{
                const start=performance.now(), result=original(...args);
                for(const [index,label] of ["Bench 001","Bench 002"].entries()){
                  const group=[...document.querySelectorAll("#tree details")].find(d=>d.querySelector("summary").textContent.startsWith(label));
                  setTimeout(()=>{
                    const live=document.querySelector('#tree details[data-key="'+group.dataset.key+'"] .part');
                    if(!live.getClientRects().length)throw Error("Hidden test control");
                    loadTimes[label]=performance.now()-start;
                    live.click();
                  },index*8);
                }
                const values=await result;
                loadTimes.comparison_response=performance.now()-start;
                return values;
              };
            }""")
            page.locator("#xMetric").select_option(index=1)
            expect(page.locator("#plotInfo")).to_have_text("Pearson r 1.000 · 300 paired candidates · 0 excluded",timeout=45000)
            expect(page.locator("#identity")).to_have_text("Bench 002 / Test chain",timeout=20000)
            expect(page.locator("#tree .part[aria-current=true]")).to_have_count(1)
            expect(page.locator("#plot .point")).to_have_count(300)
            timings.update(page.evaluate("window.loadTimes"))
            assert timings["Bench 001"]<timings["Bench 002"]<timings["comparison_response"],timings
            selected=page.locator("#plot").evaluate("el=>el.data[0].customdata.filter((p,i)=>el.data[0].marker.size[i]===12).map(p=>p[2])")
            assert selected==["Bench 002"],selected
        result=run(db,output.parent,False,executable,exercise)
        result.update(windows=platform.platform(),candidates=300,observation_rows=3900,
                      duration_ms=timings,selected_candidate="Bench 002",
                      protocol="Two timed clicks on visible controls during the actual local comparison; single run")
        output.write_text(json.dumps(result,indent=2))


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output",type=Path)
    parser.add_argument("--executable",type=Path)
    args=parser.parse_args()
    verify(args.output,args.executable)
