"""Exercise the Windows file dialogs owned by the synthetic test process."""
import argparse
import ctypes
from ctypes import wintypes
import json
import os
import sys
import tempfile
import time
from pathlib import Path

import clr
sys.path.append(str(Path(os.environ["WINDIR"])/"Microsoft.NET/Framework64/v4.0.30319/WPF"))
clr.AddReference("UIAutomationClient")
clr.AddReference("UIAutomationTypes")
clr.AddReference("System.Management")
from System import IntPtr
from System.Management import ManagementObjectSearcher
from System.Windows.Automation import (AutomationElement as Element, AndCondition, ControlType, InvokePattern,
                                       PropertyCondition, TreeScope, ValuePattern)
from playwright.sync_api import expect
from desktop_replay import ROOT, run
from antibody_insight import project


def choose_file(pid, path):
    user32 = ctypes.windll.user32
    # A Windows venv can delegate to its base python.exe, which then owns the window.
    children=ManagementObjectSearcher(f"SELECT ProcessId FROM Win32_Process WHERE ParentProcessId={int(pid)}")
    owned={pid,*(int(p["ProcessId"]) for p in children.Get())}
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HWND,wintypes.LPARAM)
    dialogs = []
    @callback_type
    def collect(handle, _):
        owner = wintypes.DWORD()
        user32.GetWindowThreadProcessId(handle,ctypes.byref(owner))
        if owner.value in owned:
            cls = ctypes.create_unicode_buffer(128)
            user32.GetClassNameW(handle,cls,len(cls))
            if cls.value=="#32770" and user32.IsWindowVisible(handle):
                dialogs.append(Element.FromHandle(IntPtr(handle)))
        return True
    seen = []
    deadline = time.monotonic()+15
    while time.monotonic()<deadline:
        dialogs.clear()
        user32.EnumWindows(collect,0)
        if len(dialogs)==1:
            dialog = dialogs[0]
            edits = dialog.FindAll(TreeScope.Descendants,PropertyCondition(Element.ControlTypeProperty,ControlType.Edit))
            fields = [e for e in edits if e.Current.AutomationId in {"1001","1148"} and e.Current.IsEnabled]
            confirm=AndCondition(PropertyCondition(Element.AutomationIdProperty,"1"),
                                 PropertyCondition(Element.ControlTypeProperty,ControlType.Button))
            ok = dialog.FindFirst(TreeScope.Descendants,confirm)
            seen = ([(e.Current.AutomationId,e.Current.IsEnabled) for e in fields],bool(ok))
            if len(fields)==1 and ok is not None:
                fields[0].GetCurrentPattern(ValuePattern.Pattern).SetValue(str(path.resolve()))
                ok.GetCurrentPattern(InvokePattern.Pattern).Invoke()
                return
        time.sleep(.15)
    raise AssertionError(f"No identifiable filename field in the test dialog: {seen}")


def verify(output, executable=None):
    with tempfile.TemporaryDirectory() as tmp:
        db=Path(tmp)/"Native dialogs.ais"
        project.create_project(db)
        dest=Path(tmp)/"export.fasta"
        def exercise(page,pid):
            expect(page.locator("#import")).to_be_enabled(timeout=20000)
            source=ROOT/"examples/processing-example.gb"
            def preview():
                page.locator("#import").click()
                page.locator("#chooseFile").click()
                choose_file(pid,source)
                expect(page.locator("#preview")).to_contain_text(source.name)
            preview()
            page.locator('#preview details summary').click()
            expect(page.locator("#preview")).to_contain_text("mat_peptide")
            expect(page.locator("#preview")).to_contain_text("MPMA")
            page.locator("#confirm").click()
            expect(page.locator("#importDialog")).not_to_be_visible()
            page.locator("#tree .part").click()
            page.locator('[data-base="10"]').click()
            page.get_by_role("button",name="Export mature FASTA…").click()
            choose_file(pid,dest)
            expect(page.locator("#status")).to_contain_text("exported")
            header,sequence=dest.read_text().splitlines()
            assert sequence=="MA" and "translation_positions=3-4" in header
            preview()
            page.locator("#confirm").click()
            expect(page.locator("#importError")).to_contain_text("already exists")
            assert len(project.summary(db)["components"])==1
        result=run(db,output.parent,False,executable,exercise)
        result.update(native_import="GenBank preview and confirmed save",native_export="Annotated mature FASTA, MA",
                      duplicate="Rejected, one component retained")
        output.write_text(json.dumps(result,indent=2),encoding="utf-8")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output",type=Path)
    parser.add_argument("--executable",type=Path)
    args=parser.parse_args()
    verify(args.output,args.executable)
