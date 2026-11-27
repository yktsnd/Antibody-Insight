"""Selection must preserve the deposited subject and the original coordinate record."""
import json
from pathlib import Path
import pytest

from antibody_insight import imports, project, structures
from antibody_insight.desktop import Desktop


ROOT = Path(__file__).resolve().parents[1]


def test_same_sequence_other_candidate_is_not_a_translation_target(tmp_path):
    from antibody_insight.example import populate
    db = tmp_path/"case.ais"
    project.create_project(db)
    populate(db)
    app = Desktop(db)
    s = app.current()
    plasmid = next(c for c in s["components"] if c["label"]=="Example plasmid")
    peptides = [c for c in s["components"] if c["label"]=="Peptide"]
    assert len(peptides)==2
    matches = app.protein_targets(s["session"],plasmid["id"],0)
    assert [r["id"] for r in matches]==[c["id"] for c in peptides if c["candidate"]==plasmid["candidate"]]


def test_saved_annotations_recover_frame_from_retained_genbank(tmp_path):
    db = tmp_path/"case.ais"
    project.create_project(db)
    project.commit(db, imports.parse_file(ROOT/"tests/fixtures/cds_codon_start_2.gb"))
    component = project.summary(db)["components"][0]["id"]
    with project.connection(db) as cx:
        features = json.loads(cx.execute("SELECT features FROM component WHERE id=?",(component,)).fetchone()[0])
        for f in features:
            f.pop("coding",None)
        cx.execute("UPDATE component SET features=? WHERE id=?",(json.dumps(features),component))
    feat = next(f for f in project.component_detail(db,component)["features"] if f["type"]=="CDS")
    assert feat["coding"]["frame_offset"]==1


def test_mmCIF_conflicting_entity_refuses_correspondence(tmp_path):
    text = (ROOT/"tests/fixtures/partial.cif").read_text()
    assert "ALA L 1 3" in text
    file = tmp_path/"conflict.cif"
    file.write_text(text.replace("ALA L 1 3","ALA L 2 3"))
    result = structures.preview(file, {"id":"component","kind":"AA","seq":"MGA"})
    assert result["mappings"]=={} and result["display"]


def test_mmCIF_zero_occupancy_is_unobserved(tmp_path):
    text = (ROOT/"tests/fixtures/partial.cif").read_text()
    file = tmp_path/"zero.cif"
    file.write_text(text.replace("1.0 0.0 ? 10 ALA","0.0 0.0 ? 10 ALA"))
    packet = structures.preview(file, {"id":"component","kind":"AA","seq":"MGA"})
    assert packet["mappings"]["X"]==[[10,""],None,None]


def test_mature_export_contains_only_the_annotated_residues(tmp_path, monkeypatch):
    db=tmp_path/"synthetic.ais"
    project.create_project(db)
    project.commit(db, imports.parse_file(ROOT/"examples/processing-example.gb"))
    app=Desktop(db)
    overview=app.current()
    component=overview["components"][0]["id"]
    target=tmp_path/"selected.fasta"
    monkeypatch.setattr(app,"_choose",lambda *args: target)
    assert app.export_peptide(overview["session"],component,0,1)
    header,sequence=target.read_text().splitlines()
    assert sequence=="MA" and "translation_positions=3-4" in header and "source_sha256=" in header
    with pytest.raises(ValueError):
        app.export_peptide(overview["session"],component,0,0)


def test_open_end_annotation_cannot_be_exported_as_a_complete_chain(tmp_path):
    gb=(ROOT/"examples/processing-example.gb").read_text()
    assert "mat_peptide     7..12" in gb
    file=tmp_path/"open.gb"
    file.write_text(gb.replace("mat_peptide     7..12","mat_peptide     7..>12"))
    db=tmp_path/"open.ais"
    project.create_project(db)
    project.commit(db, imports.parse_file(file))
    component=project.summary(db)["components"][0]["id"]
    cds=project.component_detail(db,component)["features"][0]
    assert cds["mature_fragments"]==[dict(feature_index=1,start=3,end=4)]
    with pytest.raises(ValueError):
        project.mature_fasta(db,component,0,1)
