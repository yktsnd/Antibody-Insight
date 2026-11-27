"""Offline verification using GenBank and deposited protein FASTA files."""
import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path

from Bio import SeqIO

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from antibody_insight import imports, project
from antibody_insight.desktop import Desktop

# The first exon contributes 43 or 49 nt: 14 or 16 codons and one more nucleotide.
EXAMPLES = [
    ("M27660.1", "AAA58746.1", 135, 15, [258, 341, 342], 702, None),
    ("M27661.1", "AAA58747.1", 127, 17, [210, 324, 325], 655, 656),
]


def validate(directory, gui_output=None, executable=None):
    report = []
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp)/"Antidigoxin.ais"
        project.create_project(db)
        desktop = Desktop(db)
        for nucleotide, protein, length, junction, positions, last_base, trailing in EXAMPLES:
            source = directory/(nucleotide+".gb")
            reference = directory/(protein+".faa")
            record = SeqIO.read(reference, "fasta")
            assert record.id == protein and len(record) == length
            packet = imports.parse_file(source)
            project.commit(db, packet)
            project.commit(db, imports.parse_file(reference), [{"candidate":nucleotide,"component":protein}])
            snapshot = desktop.current()
            parent = next(c["id"] for c in snapshot["candidates"] if c["label"]==nucleotide)
            parts = [p for p in snapshot["components"] if p["candidate"]==parent]
            dna = next(p["id"] for p in parts if p["kind"]=="DNA")
            aa = next(p["id"] for p in parts if p["kind"]=="AA")
            detail = desktop.inspect(snapshot["session"], dna)
            idx, feature = next((i,f) for i,f in enumerate(detail["features"]) if f["type"]=="CDS")
            assert str(record.seq) == feature["translation"]
            assert feature["coding"]["terminal_stop"] is False
            assert not feature["mature_regions"]
            fragments = feature["mature_fragments"]
            assert [(r["start"],r["end"]) for r in fragments] == ([(19,135)] if nucleotide=="M27660.1" else [])
            assert imports.codon_positions(feature, junction) == positions
            assert all(imports.residue_at(feature,p)==junction for p in positions)
            assert imports.residue_at(feature, positions[0]+1) is None
            assert imports.codon_positions(feature, length)[-1] == last_base
            assert imports.codon_positions(feature, length+1) == []
            if trailing:
                assert imports.residue_at(feature, trailing) is None
            assert imports.coding_context(detail, idx, positions[0])["selected"] == junction
            assert [p["id"] for p in desktop.protein_targets(snapshot["session"], dna, idx)] == [aa]
            report.append(dict(nucleotide=nucleotide, protein=protein, dna_sha256=packet["sha"],
                               fasta_sha256=hashlib.sha256(reference.read_bytes()).hexdigest(),
                               matched_residues=length, exon_junction_residue=junction,
                               junction_genomic_positions=positions, expected_amino_acid=str(record.seq[junction-1]),
                               last_translated_base=last_base, trailing_unmapped_base=trailing, terminal_stop_present=False,
                               mature_fragments=fragments, complete_mature_exports=0))
        if gui_output:
            from desktop_replay import run
            from playwright.sync_api import expect
            def exercise(page, _pid):
                for nucleotide, protein, length, junction, positions, _, trailing in EXAMPLES:
                    page.get_by_role("button",name=nucleotide,exact=False).click()
                    expect(page.locator("#translationPosition")).to_have_attribute("max",str(length))
                    page.locator("#translationPosition").fill(str(junction))
                    page.locator("#translationPosition").press("Enter")
                    expect(page.locator("#codonIdentity")).to_contain_text(", ".join(map(str,positions)))
                    expect(page.locator(".coding-track")).to_contain_text(protein)
                    if nucleotide=="M27660.1":
                        page.locator("#pos").fill(str(positions[1]))
                        page.locator("#pos").press("Enter")
                        page.locator("#wholeRecord").click()
                        expect(page.locator("#visibleRange")).to_have_text("1–702 nt")
                        expect(page.locator(".coordinate-ruler")).to_be_visible()
                        assert page.locator(".cds-bar").count()==2 and page.locator("[data-base]").count()==0
                        page.screenshot(path=str(gui_output/"whole-record.png"))
                        zoom=page.locator("#sequenceZoom")
                        zoom.focus()
                        zoom.press("PageUp")
                        expect(page.locator("#pos")).to_have_value(str(positions[1]))
                        assert page.locator("#visibleRange").inner_text()!="1–702 nt"
                        zoom.press("End")
                        expect(page.locator("#visibleRange")).to_have_text("341–341 nt")
                        expect(page.locator('[data-base="341"]')).to_be_visible()
                        expect(page.locator("#codonIdentity")).to_contain_text("258, 341, 342")
                        page.screenshot(path=str(gui_output/"zoomed-codon.png"))
                    if trailing:
                        page.screenshot(path=str(gui_output/"public-cds.png"))
                    page.get_by_role("button",name="Inspect "+protein,exact=True).click()
                    expect(page.locator("#pos")).to_have_value(str(junction))
                    page.get_by_role("button",name="Go to source codon").click()
                    expect(page.locator("#pos")).to_have_value(str(positions[0]))
                    if nucleotide=="M27660.1":
                        page.locator("#pos").fill("352")
                        page.locator("#pos").press("Enter")
                        expect(page.locator(".mature-fragment")).to_contain_text("position 1 · annotated end unresolved")
                        assert not page.get_by_role("button",name="Export mature FASTA…").count()
                    if trailing:
                        page.locator("#pos").fill(str(trailing))
                        page.locator("#pos").press("Enter")
                        expect(page.locator("#codonIdentity")).to_contain_text("outside")
                page.get_by_role("button",name="M27660.1",exact=False).click()
                page.locator("#pos").fill("341")
                page.locator("#pos").press("Enter")
                expect(page.locator("#codonIdentity")).to_contain_text("258, 341, 342")
                page.locator("#note").click()
                page.locator("#saveNote").click()
                expect(page.locator("#noteDialog")).not_to_be_visible()
            result=run(db,gui_output,False,executable,exercise)
            def restored(page,_pid):
                expect(page.locator("#visibleRange")).to_have_text("341–341 nt",timeout=20000)
                expect(page.locator("#codonIdentity")).to_contain_text("258, 341, 342")
            report[0]["zoom_restart"]=run(db,gui_output,True,executable,restored)
            for entry in report:
                entry["desktop_replay"]=result
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, help="Directory containing <accession>.gb and <protein>.faa")
    parser.add_argument("output", type=Path)
    parser.add_argument("--gui", action="store_true")
    parser.add_argument("--executable",type=Path)
    args = parser.parse_args()
    args.output.write_text(json.dumps(validate(args.directory,args.output.parent if args.gui else None,args.executable),indent=2),encoding="utf-8")
