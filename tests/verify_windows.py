"""Run desktop acceptance checks on a freshly extracted local Windows bundle."""
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT=Path(__file__).resolve().parents[1]


def digest(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source,"sha256").hexdigest()


def verify(archive,public,out):
    out.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="antibody-insight-package-") as temporary:
        root=Path(temporary).resolve()
        with zipfile.ZipFile(archive) as bundle:
            for member in bundle.infolist():
                if not (root/member.filename).resolve().is_relative_to(root/"AntibodyInsight"):
                    raise ValueError(f"Unexpected archive path: {member.filename}")
            bundle.extractall(root)
        binary=root/"AntibodyInsight/AntibodyInsight.exe"
        assets=binary.parent/"_internal/antibody_insight/ui"
        for path in (ROOT/"antibody_insight/ui").rglob("*"):
            if path.is_file():
                assert digest(assets/path.relative_to(ROOT/"antibody_insight/ui"))==digest(path)
        cases={
            "desktop_replay":[out], "measurement_replay":[out/"measurements.json"],
            "alignment_replay":[out/"aligned-reference.json"], "file_replay":[out/"native-files.json"],
            "public_cds":[public,out/"public-cds.json","--gui"],
            "public_structure":[public,out/"public-structure.json"],
            "public_snapgene":[public,out/"public-snapgene.json"], "camera_replay":[out/"camera"],
            "recovery_replay":[out/"recovery.json"],"circular_replay":[out/"circular.json"],
            "comparison_replay":[out/"comparison.json"],"comparison_load":[out/"comparison-load.json"],
            "overlay_replay":[public,out/"overlay.json"],"representative_replay":[out/"representative.json"],
            "numbering_replay":[public,out/"numbering.json"]
        }
        for script,args in cases.items():
            print(script,flush=True)
            subprocess.run([sys.executable,ROOT/"tests"/(script+".py"),*args,"--executable",binary],
                           check=True,stdout=subprocess.DEVNULL)
        receipt=dict(archive=archive.name,bytes=archive.stat().st_size,sha256=digest(archive),
                     executable_sha256=digest(binary),ui_matches_source=True,
                     verification=list(cases),environment="Local Windows x64, installed WebView2")
        (out/"bundle.json").write_text(json.dumps(receipt,indent=2),encoding="utf-8")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive",type=Path)
    parser.add_argument("public",type=Path)
    parser.add_argument("output",type=Path)
    args=parser.parse_args()
    verify(args.archive.resolve(),args.public.resolve(),args.output.resolve())
