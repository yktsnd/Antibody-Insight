"""Recover an interrupted local import and inspect a project with WebView offline."""
import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import expect
from desktop_replay import run
from antibody_insight import example, imports, project


def interrupt_writer(db, source):
    packet=imports.parse_file(source)
    first,_second=packet["records"]

    def interrupted_input():
        yield first
        # The actual commit loop has saved the first row inside its transaction.
        os._exit(73)

    packet["records"]=interrupted_input()
    project.commit(db,packet)


def verify(output,executable):
    with tempfile.TemporaryDirectory() as tmp:
        db=Path(tmp)/"Recovery.ais"
        source=Path(tmp)/"Interrupted.csv"
        source.write_text("candidate,component,kind,sequence\nC,Part,AA,MA\nD,Part,AA,AA\n")
        project.create_project(db)
        example.populate(db)
        before=project.summary(db)
        child=subprocess.run([sys.executable,__file__,"--interrupt",db,source])
        assert child.returncode==73 and project.summary(db)==before
        packet=imports.parse_file(source)
        with project.connection(db) as conn:
            assert conn.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
            assert not conn.execute("SELECT 1 FROM source WHERE hash=?",(packet["sha"],)).fetchone()
        project.commit(db,packet)
        assert len(project.summary(db)["candidates"])==len(before["candidates"])+2
        remote=[]

        def offline(page,_pid):
            page.context.set_offline(True)
            page.on("request",lambda req: remote.append(urlsplit(req.url).scheme)
                    if urlsplit(req.url).scheme in {"http","https","ws","wss"} else None)
            page.reload()
            expect(page.locator("#coordinate")).to_contain_text("Chain A",timeout=20000)
            page.locator('[data-base="2"]').click()
            expect(page.locator("#coordinate")).to_contain_text("10A")
            expect(page.locator("#plot .point").first).to_be_visible()
            expect(page.locator("#molecule canvas").first).to_be_visible()
            page.locator("#note").click()
            page.locator("#noteText").fill("Offline observation at A 10A.")
            page.locator("#saveNote").click()
            expect(page.locator("#noteDialog")).not_to_be_visible()
            assert not remote
        result=run(db,output.parent,False,executable,offline)
        state=project.summary(db)["state"]
        assert state["note"]=="Offline observation at A 10A." and state["position"]==2
        result.update(interrupted_writer_exit=73,integrity_check="ok",partial_import_rows=0,
                      partial_source_retained=False,retry_candidates_added=2,remote_page_requests=remote,
                      offline_reload=True,persisted_position=2)
        output.write_text(json.dumps(result,indent=2),encoding="utf-8")


if __name__=="__main__":
    if sys.argv[1:2]==["--interrupt"]:
        interrupt_writer(Path(sys.argv[2]),Path(sys.argv[3]))
    else:
        parser=argparse.ArgumentParser(description=__doc__)
        parser.add_argument("output",type=Path)
        parser.add_argument("--executable",type=Path)
        args=parser.parse_args()
        verify(args.output,args.executable)
