"""Measure project catalog and single component reads on reproducible synthetic data."""
import json
import platform
import statistics
import sys
import tempfile
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from antibody_insight import imports, project

def profile(size, root):
    path=root/f"{size}.ais"
    project.create_project(path)
    source=root/"input.csv"
    rows=[f"Candidate {i+1},Component,AA,{'ACDEFGHIKLMNPQRSTVWY'*10}" for i in range(size)]
    source.write_text("candidate,component,kind,sequence\n"+"\n".join(rows)+"\n")
    project.commit(path,imports.parse_file(source))
    summary_times=[];detail_times=[]
    for _ in range(10):
        start=time.perf_counter()
        data=project.summary(path)
        mid=time.perf_counter()
        detail=project.component_detail(path,data["components"][-1]["id"])
        end=time.perf_counter()
        assert len(detail["seq"])==200 and "seq" not in data["components"][0]
        summary_times.append(1000*(mid-start));detail_times.append(1000*(end-mid))
    return dict(candidates=size,catalog_bytes=len(json.dumps(data).encode()),
                catalog_ms=summary_times,detail_ms=detail_times,catalog_median_ms=statistics.median(summary_times),
                detail_median_ms=statistics.median(detail_times))

if __name__=="__main__":
    with tempfile.TemporaryDirectory() as tmp:
        result={"os":platform.platform(),"processor":platform.processor(),"python":platform.python_version(),
                "case":"200 aa per candidate; local temporary SQLite; OS cache uncontrolled; excludes GUI",
                "measurements":[profile(n,Path(tmp)) for n in (5,20,300)]}
    output=Path(sys.argv[1])
    output.write_text(json.dumps(result,indent=2),encoding="utf-8")
    for m in result["measurements"]: print(m["candidates"],m["catalog_median_ms"],m["detail_median_ms"])
