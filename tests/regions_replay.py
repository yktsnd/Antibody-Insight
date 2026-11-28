"""Compare three candidate regions and inspect a reverse feature in the Windows GUI."""
import argparse
import json
import tempfile
from hashlib import sha256
from pathlib import Path

from playwright.sync_api import expect
from openpyxl import load_workbook
from desktop_replay import ROOT, run
from file_replay import choose_file
from antibody_insight import example, imports, project, structures


def verify(output,executable=None):
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp)
        db=root/"Region comparison.ais"
        project.create_project(db)
        example.populate(db)
        path=root/"Additional regions.csv"
        path.write_text("candidate,component,kind,sequence\nExample B,Extended reporter,DNA,ATGGCTGTCTAA\n"
                        "Example C,Peptide,AA,MA\n")
        project.commit(db,imports.parse_file(path))
        feature=imports.parse_file(ROOT/"examples/coordinate-example.gb")
        project.commit(db,feature,[{"candidate":"Example C","component":"Annotated plasmid"}])
        overview=project.summary(db)
        lookup={candidate["label"]:candidate["id"] for candidate in overview["candidates"]}
        def component(candidate,label):
            return next(c["id"] for c in overview["components"] if c["candidate"]==lookup[candidate] and c["label"]==label)
        peptide=component("Example C","Peptide")
        coords=structures.preview(ROOT/"examples/synthetic-peptide.pdb",project.component_detail(db,peptide))
        structures.save(db,coords,"A","Reference")
        workbook=root/"Comparison.xlsx"
        def exercise(page,pid):
            def choose(candidate,label):
                key=component(candidate,label)
                page.locator(f'#tree .part[data-key="{key}"]').click()
            choose("Example A","Reporter")
            page.get_by_role("button",name="Compare regions",exact=True).click()
            page.get_by_role("button",name="Add region",exact=True).click()
            choose("Example B","Extended reporter")
            page.get_by_role("button",name="Add region",exact=True).click()
            expect(page.locator("#regionComparison tr")).to_have_count(4)
            choose("Example C","Annotated plasmid")
            page.locator("#regionSource").select_option(label="Example CDS · CDS")
            page.get_by_role("button",name="Add region",exact=True).click()
            expect(page.locator("#regionComparison tr")).to_have_count(5)
            expect(page.locator("#regionComparison th[title='Unanchored insertion']")).to_have_count(3)
            target=page.locator('[data-region-row="2"][data-source-position="8"]')
            expect(target).to_have_text("C")
            target.click()
            expect(page.locator("#pos")).to_have_value("8")
            expect(page.locator("#codonIdentity")).to_have_text("Translation 2 · A · GCT · DNA 9, 8, 4")
            panel=page.locator("#regionsPanel")
            panel.get_by_text("Identity matrix and method",exact=True).click()
            expect(page.locator("#regionIdentity")).to_contain_text("9/9 · 100.0%")
            expect(panel.get_by_text("3 · 9 nt · GC 3/9 known bases · 8–12 (−), 1–4 (−)")).to_be_visible()
            panel.get_by_text("Identity matrix and method",exact=True).click()
            page.locator("#sequences").evaluate("(el)=>el.scrollTop=0")
            page.screenshot(path=str(output.with_suffix(".png")))
            panel.get_by_role("button",name="Export comparison…",exact=True).click()
            choose_file(pid,workbook)
            expect(page.locator("#status")).to_have_text("Region comparison exported.")
            page.get_by_role("button",name="Inspect Peptide",exact=True).click()
            expect(page.locator("#coordinate")).to_contain_text("10A · sequence 2")
            page.get_by_role("button",name="Go to source codon").click()
            expect(page.locator("#pos")).to_have_value("9")
            expect(page.locator("#regionComparison tr")).to_have_count(5)
            page.locator("#note").click()
            page.locator("#saveNote").click()
            expect(page.locator("#noteDialog")).not_to_be_visible()
        report=run(db,output.parent,False,executable,exercise)
        def restored(page,_pid):
            expect(page.locator("#regionComparison tr")).to_have_count(5,timeout=20000)
            expect(page.locator("#pos")).to_have_value("9")
            expect(page.locator('[data-region-row="2"][data-source-position="9"]')).to_have_attribute("aria-pressed","true")
        report["restart"]=run(db,output.parent,True,executable,restored)
        book=load_workbook(workbook,read_only=True)
        try:
            records=list(book["Regions"].values)
            assert records[5][6]==sha256((ROOT/"examples/coordinate-example.gb").read_bytes()).hexdigest()
            cells=list(book["Source coordinates"].values)[1:]
            source=[row for row in cells if row[1]==3 and row[3] is not None]
            assert [(r[2],r[3],r[4]) for r in source]==list(zip("ATGGCTTAA",[12,11,10,9,8,4,3,2,1],[-1]*9))
            assert sum(row[5] and row[2] is not None for row in cells)==3
            assert (2,3,9,9,1) in list(book["Identity"].values)
        finally:
            book.close()
        output.with_suffix(".xlsx").write_bytes(workbook.read_bytes())
        report.update(candidates=3,insertion_columns=3,identity=[9,9],gc=[3,9],
                      clicked_genome_base=8,verified_codon=[9,8,4],structure="A 10A",xlsx_readback=True)
    output.write_text(json.dumps(report,indent=2),encoding="utf-8")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output",type=Path)
    parser.add_argument("--executable",type=Path)
    args=parser.parse_args()
    verify(args.output,args.executable)
