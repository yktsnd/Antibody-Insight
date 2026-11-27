"""Build indexed source in an empty directory and launch its Windows executable."""
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT=Path(__file__).resolve().parents[1]


def verify(output):
    with tempfile.TemporaryDirectory(prefix="antibody-insight-clean-") as temporary:
        checkout=Path(temporary)/"source"
        checkout.mkdir()
        subprocess.run(["git","checkout-index","--all","--prefix="+checkout.as_posix()+"/"],
                       cwd=ROOT,check=True)
        subprocess.run([sys._base_executable,"-m","venv",checkout/".venv"],check=True)
        python=checkout/".venv/Scripts/python.exe"

        def run(*args):
            result=subprocess.run(args,cwd=checkout,capture_output=True)
            if result.returncode:
                sys.stdout.buffer.write(result.stdout[-6000:]+result.stderr[-6000:])
                result.check_returncode()
            return result.stdout.decode("utf-8",errors="replace")

        print("Installing dependencies in a fresh environment",flush=True)
        run(python,"-m","pip","--disable-pip-version-check","install","-r","requirements-dev.txt")
        run(python,"-m","pip","check")
        tested=run(python,"-m","pytest","-q").splitlines()[-1]
        print(tested,flush=True)
        run("powershell","-NoProfile","-ExecutionPolicy","Bypass","-File",checkout/"build.ps1")
        out=checkout/"verification"
        binary=checkout/"dist/AntibodyInsight/AntibodyInsight.exe"
        run(python,"tests/desktop_replay.py",out,"--executable",binary)
        run(python,"tests/camera_replay.py",out/"camera","--executable",binary)
        run(python,"tests/representative_replay.py",out/"representative.json","--executable",binary)
        with (checkout/"dist/AntibodyInsight-Windows-x64.zip").open("rb") as archive:
            digest=hashlib.file_digest(archive,"sha256").hexdigest()
        receipt=dict(source="Git index in empty directory",python=sys.version.split()[0],
                     fresh_venv=True,pip_check=True,pytest=tested,packaged=True,
                     desktop=json.loads((out/"desktop.json").read_bytes()),
                     camera=json.loads((out/"camera/camera-state.json").read_bytes())["comparison"],
                     representative=json.loads((out/"representative.json").read_bytes()),
                     fresh_archive_sha256=digest,same_operating_system=True)
        output.write_text(json.dumps(receipt,indent=2),encoding="utf-8")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output",type=Path)
    verify(parser.parse_args().output.resolve())
