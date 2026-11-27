"""Replay the actual WebView2 window using a temporary synthetic project (Windows)."""
import argparse
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from antibody_insight import example, project

def run(path, out, restart, executable=None, exercise=None):
    with socket.socket() as sock:
        sock.bind(("127.0.0.1",0))
        port=sock.getsockname()[1]
    code=("import sys,webview; from antibody_insight.desktop import launch; "
          "webview.settings['REMOTE_DEBUGGING_PORT']=int(sys.argv[1]); launch(sys.argv[2])")
    env=os.environ.copy()
    if executable:
        env["WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS"]=f"--remote-debugging-port={port}"
    command=[str(executable.resolve()),str(path)] if executable else [sys.executable,"-c",code,str(port),str(path)]
    child=subprocess.Popen(command,cwd=path.parent if executable else ROOT,env=env)
    try:
        with sync_playwright() as pw:
            deadline=time.monotonic()+40
            while time.monotonic()<deadline and child.poll() is None:
                try:
                    with socket.create_connection(("127.0.0.1",port),timeout=.4): break
                except OSError:time.sleep(.2)
            browser=pw.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
            context=browser.contexts[0]
            page=context.pages[0] if context.pages else context.wait_for_event("page")
            errors=[]
            page.on("pageerror",lambda err:errors.append(str(err)))
            if exercise is None:
                expect(page.locator("#coordinate")).to_contain_text("Chain A",timeout=20000)
            if exercise is not None:
                exercise(page,child.pid)
            elif restart:
                assert "10A" in page.locator("#coordinate").inner_text()
                page.locator("#note").click()
                assert page.locator("#noteText").input_value()=="Retain original sample A."
            else:
                page.locator(".base").nth(1).click()
                assert "10A" in page.locator("#coordinate").inner_text()
                assert page.locator("#molecule canvas").count()>0
                page.screenshot(path=str(out/"workspace.png"))
                page.get_by_role("button",name="Example plasmid",exact=False).click()
                expect(page.locator("#codonIdentity")).to_contain_text("Stop codon")
                page.locator('[data-base="8"]').click()
                expect(page.locator("#codonIdentity")).to_have_text("Translation 2 · A · GCT · DNA 9, 8, 4")
                assert page.locator(".in-codon").count()==3
                page.screenshot(path=str(out/"cds-coordinates.png"))
                page.get_by_role("button",name="Inspect Peptide").click()
                expect(page.locator("#coordinate")).to_contain_text("10A · sequence 2")
                page.get_by_role("button",name="Go to source codon").click()
                expect(page.locator("#pos")).to_have_value("9")
                page.locator('[data-base="6"]').click()
                expect(page.locator("#codonIdentity")).to_contain_text("outside")
                assert page.get_by_role("button",name="Inspect Peptide").count()==0
                page.locator("#translationPosition").fill("3")
                page.locator("#translationPosition").press("Enter")
                expect(page.locator("#codonIdentity")).to_contain_text("Stop codon")
                assert page.get_by_role("button",name="Inspect Peptide").count()==0
                page.get_by_role("button",name="Annotated precursor",exact=False).click()
                expect(page.locator("#translationPosition")).to_be_visible()
                assert page.locator(".mature-region").count()==0
                page.locator('[data-base="10"]').click()
                expect(page.locator(".mature-region")).to_contain_text("position 2")
                expect(page.locator("#codonIdentity")).to_contain_text("Translation 4 · A")
                page.get_by_role("button",name="Inspect Peptide · mature 2",exact=True).click()
                expect(page.locator("#coordinate")).to_contain_text("10A · sequence 2")
                page.locator('[data-base="1"]').click()
                page.get_by_role("button",name="Go to source codon").click()
                expect(page.locator("#pos")).to_have_value("7")
                expect(page.locator(".mature-region")).to_contain_text("position 1")
                page.screenshot(path=str(out/"mature-coordinates.png"))
                page.locator("#tree .part").first.click()
                expect(page.locator("#identity")).to_contain_text("Reporter")
                assert "No coordinates" in page.locator("#coordinate").inner_text()
                select_ref=page.locator("#reference")
                select_ref.select_option(index=1)
                page.wait_for_selector(".base.diff")
                assert page.locator(".base.diff").count()==2
                page.locator("#tree .part").nth(1).click()
                expect(page.locator("#coordinate")).to_contain_text("Chain A")
                page.locator(".base").nth(1).click()
                page.locator("#note").click()
                page.locator("#noteText").fill("Retain original sample A.")
                page.locator("#saveNote").click()
                page.locator("#noteDialog").wait_for(state="hidden")
                page.locator("#plot .point").first.wait_for()
            assert not errors,errors
            return {"pass":True,"webview":browser.version,"errors":errors}
    finally:
        child.terminate()
        child.wait(timeout=15)

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("output",type=Path)
    parser.add_argument("--executable",type=Path)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp)/"Synthetic comparison.ais"
        project.create_project(path);example.populate(path)
        result=[run(path,args.output,r,args.executable) for r in (False,True)]
        (args.output/"desktop.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
        print(result)
