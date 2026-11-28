"""Compare three public antibody chains and verify against independent IMGT/PDB coordinates."""
import argparse
import json
import tempfile
from pathlib import Path

from Bio import SeqIO
from playwright.sync_api import expect

from desktop_replay import run
from antibody_insight import imports, project, structures
from antibody_insight.numbering import domains


def verify(public,output,executable=None):
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp)
        db=root/"Public variable domain comparison.ais"
        project.create_project(db)
        sequences={}
        for candidate,name,length in [("1IGT","1IGT.faa",444),("1MCP","1MCP.faa",222),("Anti-digoxin","AAA58746.1.faa",135)]:
            fasta=next(r for r in SeqIO.parse(public/name,"fasta") if len(r.seq)==length)
            source=root/(candidate+".faa")
            source.write_text(">"+candidate+"\n"+str(fasta.seq)+"\n")
            project.commit(db,imports.parse_file(source),[dict(candidate=candidate,component="Heavy chain")])
            sequences[candidate]=str(fasta.seq)
        kol=next(r for r in SeqIO.parse(public/"2FB4.faa","fasta") if len(r.seq)==229)
        long_path=root/"Kol.faa"
        long_path.write_text(">Kol\n"+str(kol.seq)+"\n")
        project.commit(db,imports.parse_file(long_path),[dict(candidate="Kol",component="Heavy chain")])
        short=root/"Control.faa"
        short.write_text(">Control\nMA\n")
        project.commit(db,imports.parse_file(short),[dict(candidate="Control",component="Dipeptide")])
        summary=project.summary(db)
        keys={c["label"]:next(row["id"] for row in summary["components"] if row["candidate"]==c["id"])
              for c in summary["candidates"]}
        coordinate=project.component_detail(db,keys["1IGT"])
        packet=structures.preview(public/"1IGT.cif",coordinate)
        structures.save(db,packet,"D","Experimental")
        # Independent oracle: published IMGT Collier de Perles for 1igt_D [8.8.11].
        chain=domains(sequences["1IGT"])["domains"][0]
        residues={r["label"]:r for r in chain["residues"]}
        points={"23":"C","26":"S","39":"M","41":"W","55":"Y","66":"Y","89":"L","104":"C","118":"W","128":"S"}
        assert {k:residues[k]["aa"] for k in points}==points
        assert [sum(r["region"]==f"CDR{i}" for r in residues.values()) for i in (1,2,3)]==[8,8,11]
        mcp=domains(sequences["1MCP"],"kabat")["domains"][0]
        expected_kabat=["52A","52B","52C"]
        assert [r["label"] for r in mcp["residues"] if r["label"] in expected_kabat]==expected_kabat
        long_domain=domains(str(kol.seq))["domains"][0]
        cdr3=[r for r in long_domain["residues"] if r["region"]=="CDR3"]
        expected_insertions=["111.1","111.2","111.3","112.3","112.2","112.1"]
        assert len(cdr3)==19 and [r["label"] for r in cdr3 if "." in r["label"]]==expected_insertions
        light_controls=[]
        for archive,length,chain_type in [("1IGT.faa",214,"K"),("2FB4.faa",216,"L")]:
            aa=next(str(r.seq) for r in SeqIO.parse(public/archive,"fasta") if len(r.seq)==length)
            light=domains(aa)["domains"][0]
            assert light["complete"] and light["chain"]==chain_type and light["residues"][-1]["label"]=="127"
            light_controls.append(chain_type)

        def compare(page,_pid):
            for index,candidate in enumerate(("1IGT","1MCP","Anti-digoxin")):
                selected=page.locator(f'#tree .part[data-key="{keys[candidate]}"]')
                selected.click()
                if index==0:page.locator("#numberingToggle").click()
                add=page.get_by_role("button",name="Add to comparison")
                expect(add).to_be_enabled(timeout=20000)
                add.click()
            expect(page.locator("#numberedComparison tr")).to_have_count(5)
            page.get_by_role("combobox",name="Numbered region").select_option("CDR2")
            expect(page.locator("#numberedComparison th").first).to_have_text("CDR2 · IMGT")
            expect(page.locator("#numberedComparison tr").nth(1)).to_contain_text("—")
            target=page.locator(f'button[data-imgt="58"][data-component="{keys["1IGT"]}"]')
            expect(target).to_have_text("N")
            target.click()
            expect(page.locator("#numberedPosition")).to_have_text("IMGT 58 · CDR2 · sequence 53")
            expect(page.locator("#coordinate")).to_have_text("Chain D · 52A · sequence 53")
            expect(target).to_have_attribute("aria-pressed","true")
            page.locator("#style").select_option("Cartoon")
            page.locator("#focusResidue").click()
            page.screenshot(path=str(output.with_suffix(".png")))
            page.get_by_role("combobox",name="Numbering scheme").select_option("kabat")
            expect(page.locator("#numberedPosition")).to_have_text("Kabat 52A · CDR2 · sequence 53")
            expect(page.locator("#coordinate")).to_have_text("Chain D · 52A · sequence 53")
            page.get_by_role("button",name="Add to comparison").click()
            page.locator(f'#tree .part[data-key="{keys["1MCP"]}"]').click()
            page.get_by_role("button",name="Add to comparison").click()
            expect(page.locator("#numberedComparison th").first).to_have_text("CDR2 · Kabat")
            page.get_by_role("combobox",name="Numbering scheme").select_option("imgt")
            expect(page.locator("#numberedComparison tr")).to_have_count(5)
            page.locator(f'#tree .part[data-key="{keys["Kol"]}"]').click()
            page.get_by_role("button",name="Add to comparison").click()
            page.get_by_role("combobox",name="Numbered region").select_option("CDR3")
            expect(page.locator("#numberedComparison th").first).to_have_text("CDR3 · IMGT")
            headings=page.locator("#numberedComparison tr").first.locator("th").all_text_contents()
            assert [label for label in headings if "." in label]==expected_insertions
            page.screenshot(path=str(output.with_name("numbering-long-cdr3.png")))
            page.get_by_role("combobox",name="Numbered region").select_option("CDR2")
            page.locator(f'#tree .part[data-key="{keys["Control"]}"]').click()
            expect(page.locator("#numberingPanel")).to_contain_text("No antibody variable domain assigned.")
            target.click()
            expect(page.locator("#coordinate")).to_have_text("Chain D · 52A · sequence 53")
            page.locator("#note").click()
            page.locator("#saveNote").click()
            expect(page.locator("#noteDialog")).not_to_be_visible()
        report=run(db,output.parent,False,executable,compare)
        def restored(page,_pid):
            expect(page.locator("#numberedComparison tr")).to_have_count(6,timeout=20000)
            expect(page.locator("#numberedPosition")).to_contain_text("IMGT 58 · CDR2")
            expect(page.locator("#coordinate")).to_have_text("Chain D · 52A · sequence 53")
        report["restart"]=run(db,output.parent,True,executable,restored)
        report.update(sources=[*sequences,"Kol"],imgt_1igt_d=dict(cdr_lengths=[8,8,11],checked_labels=points),
                      kol_cdr3=dict(length=19,insertions=expected_insertions),light_terminal_127=light_controls,
                      mcpc603_kabat_insertions=expected_kabat,
                      selected=dict(imgt="58",kabat="52A",input_position=53,author="D 52A"),short_control="Unassigned")
    output.write_text(json.dumps(report,indent=2),encoding="utf-8")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("public",type=Path)
    parser.add_argument("output",type=Path)
    parser.add_argument("--executable",type=Path)
    p=parser.parse_args()
    verify(p.public,p.output,p.executable)
