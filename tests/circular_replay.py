"""Inspect a synthetic origin-spanning CDS on a circular 3,000 nt record."""
import argparse
import json
import tempfile
from pathlib import Path

from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqFeature import CompoundLocation, SeqFeature, SimpleLocation
from Bio.SeqRecord import SeqRecord
from playwright.sync_api import expect

from desktop_replay import run
from antibody_insight import imports, project


def verify(output,executable=None):
    with tempfile.TemporaryDirectory() as tmp:
        folder=Path(tmp)
        # The synthetic CDS reads ATGG at the end and CTTAA at the beginning.
        record=SeqRecord(Seq("CTTAA"+"C"*2991+"ATGG"),id="CircularDemo",name="CircularDemo",
                         description="Synthetic origin-spanning software fixture",
                         annotations={"molecule_type":"DNA","topology":"circular"})
        record.features=[SeqFeature(CompoundLocation([SimpleLocation(2996,3000,1),SimpleLocation(0,5,1)]),
                                    type="CDS",qualifiers={"label":["Example CDS"],"translation":["MA"]})]
        source=folder/"Circular record.gb"
        SeqIO.write(record,source,"genbank")
        db=folder/"Origin-spanning coordinates.ais"
        project.create_project(db)
        project.commit(db,imports.parse_file(source))
        def exercise(page,_pid):
            page.locator("#tree .part").click()
            page.locator("#wholeRecord").click()
            expect(page.locator("#visibleRange")).to_have_text("1–3000 nt")
            expect(page.locator(".cds-bar")).to_have_count(2)
            expect(page.locator(".sequence-meta")).to_contain_text("circular")
            # Choose the second segment, then zoom to its first base.
            page.locator('.cds-bar[data-low="1"]').click()
            zoom=page.locator("#sequenceZoom")
            zoom.focus()
            zoom.press("End")
            expect(page.locator("#visibleRange")).to_have_text("1–1 nt")
            expect(page.locator("#codonIdentity")).to_have_text("Translation 2 · A · GCT · DNA 3000, 1, 2")
            page.locator("#codonIdentity").get_by_role("button",name="3000",exact=True).click()
            expect(page.locator("#visibleRange")).to_have_text("3000–3000 nt")
            expect(page.locator('[data-base="3000"]')).to_have_text("G")
            expect(page.locator("#codonIdentity")).to_contain_text("DNA 3000, 1, 2")
            page.screenshot(path=str(output.with_suffix(".png")))
        result=run(db,output.parent,False,executable,exercise)
        result.update(topology="circular",length=3000,visible_segments=2,codon="GCT",source_positions=[3000,1,2])
        output.write_text(json.dumps(result,indent=2),encoding="utf-8")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output",type=Path)
    parser.add_argument("--executable",type=Path)
    args=parser.parse_args()
    verify(args.output,args.executable)
