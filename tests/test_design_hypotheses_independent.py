"""Independent M3 boundaries; P02/P03/P04, J02/J03/J04 and their ACs."""

import copy
import hashlib

import pytest

from workspace_app.composition import composition_signature
from workspace_app.design import variant_preview
from workspace_app.domain import ValidationError, new_id
from workspace_app.fixtures import composition_bundle, numbering_bundle
from workspace_app.hypotheses import hypothesis_preview
from workspace_app.storage import Store
from workspace_app.structure_fixtures import structure_bundle


def edit(mapping, number, target="A"):
    return {"parent_map_id": mapping["id"], "number": number, "ins_code": "", "to_aa": target, "reference_map_id": None}


def proposal(bundle):
    molecule = next(e for e in bundle["entities"] if e["type"] == "molecule")
    return {"text": "Independent engineering question only.", "question": "What would falsify this proposal?",
            "limitations": "No scientific validity claimed.", "molecule_ids": [molecule["id"]],
            "related_evidence_ids": [], "lineage_ids": [], "residue_refs": [], "structure_refs": []}


def mapped_composition():
    bundle = composition_bundle()
    parent = next(e for e in bundle["entities"] if e.get("component_graph"))
    chain = parent["chains"][0]
    template = next(e for e in numbering_bundle()["entities"] if e["type"] == "residue_map")
    mapping = copy.deepcopy(template)
    mapping.update(id=new_id("residue_map"), project_id=bundle["project"]["id"], molecule_id=parent["id"], chain_id=chain["id"],
                   sequence_start=1, sequence_end=len(chain["sequence"]),
                   entries=[{"sequence_index": i, "aa": aa, "number": i, "ins_code": ""} for i, aa in enumerate(chain["sequence"], 1)])
    bundle["entities"].append(mapping)
    return bundle, parent, mapping


def test_component_boundary_two_copy_effect_and_ancestry_roundtrip(tmp_path):
    bundle, parent, mapping = mapped_composition()
    before = copy.deepcopy(bundle)
    original = parent["component_graph"]["chains"][0]
    boundary = len(original["components"][0]["sequence"])
    # Cross both exact-source component boundaries, leaving the middle linker alone.
    second_start = boundary + len(original["components"][1]["sequence"]) + 1
    result = variant_preview(bundle, parent["id"], "Boundary child", "BOUNDARY", "Independent exact component edits", [edit(mapping, boundary), edit(mapping, second_start)])
    child, lineage = result["entities"]
    after = child["component_graph"]["chains"][0]
    assert [c["origin"] for c in after["components"]] == [None, None, None]
    assert original["components"][1] == after["components"][1]
    assert all(c["origin"] is not None for c in (original["components"][0], original["components"][2]))
    assert original["copies"] == after["copies"] == 2
    assert parent["component_graph"]["chains"][1:] == child["component_graph"]["chains"][1:]
    assert parent["component_graph"]["connections"] == child["component_graph"]["connections"]
    assert lineage["change_set"]["before"] == composition_signature(parent)
    assert lineage["change_set"]["after"] == composition_signature(child)
    assert bundle == before
    store = Store(tmp_path / "boundary.sqlite3"); store.import_bundle(bundle); store.import_bundle(result)
    assert Store(store.path).bundle(bundle["project"]["id"])["entities"][-2:] == result["entities"]


@pytest.mark.parametrize("tamper", ["unlisted_residue", "copy_count", "origin", "format", "role", "missing_child"])
def test_forged_child_or_partial_save_rejects_atomically(tmp_path, tamper):
    bundle, parent, mapping = mapped_composition()
    result = variant_preview(bundle, parent["id"], "Boundary child", "BOUNDARY", "Independent import reconstruction", [edit(mapping, 1)])
    child, lineage = result["entities"]
    if tamper == "unlisted_residue":
        chain = child["chains"][1]; chain["sequence"] = "A" + chain["sequence"][1:]
        child["component_graph"]["chains"][1]["components"][0].update(sequence=chain["sequence"], origin=None)
    elif tamper == "copy_count": child["component_graph"]["chains"][0]["copies"] = 3
    elif tamper == "origin": child["component_graph"]["chains"][0]["components"][0]["origin"] = parent["component_graph"]["chains"][0]["components"][0]["origin"]
    elif tamper == "format": child["format"] += " changed"
    elif tamper == "role": child["chains"][1]["role"] += " changed"
    elif tamper == "missing_child": result["entities"] = [lineage]
    if tamper != "missing_child": lineage["change_set"]["after"] = composition_signature(child)
    store = Store(tmp_path / "tamper.sqlite3"); store.import_bundle(bundle)
    with pytest.raises(ValidationError): store.import_bundle(result)
    assert store.bundle(bundle["project"]["id"]) == bundle


def test_alias_maps_reject_duplicate_raw_locus_even_different_coordinates():
    bundle = numbering_bundle()
    mapping = next(e for e in bundle["entities"] if e["type"] == "residue_map")
    other = copy.deepcopy(mapping); other["id"] = new_id("residue_map"); other["domain_id"] = "alternative supplied domain"
    other["entries"] = other["entries"][:26]; other["sequence_end"] = 26
    # A consistent alternative partial annotation gives the same physical raw 1 a different coordinate.
    for entry in other["entries"]: entry["number"] += 1
    bundle["entities"].append(other)
    with pytest.raises(ValidationError, match="Duplicate source residue"):
        variant_preview(bundle, mapping["molecule_id"], "Alias child", "ALIAS", "Do not edit one raw locus twice", [edit(mapping, 1), edit(other, 2)])


def test_hypothesis_rejects_correspondence_from_another_model_atomically(tmp_path):
    bundle = structure_bundle(); definition = proposal(bundle)
    structure = next(e for e in bundle["entities"] if e["type"] == "structure")
    map_two = next(e for e in bundle["entities"] if e["type"] == "structure_map" and e["structure_id"] == structure["id"] and e["chain_assignments"][0]["model"] == 2)
    definition["structure_refs"] = [{"structure_id": structure["id"], "model": 1, "structure_map_id": map_two["id"]}]
    store = Store(tmp_path / "wrong-model.sqlite3"); store.import_bundle(bundle)
    with pytest.raises(ValidationError): hypothesis_preview(bundle, definition)
    assert store.bundle(bundle["project"]["id"]) == bundle


def test_parent_evidence_does_not_become_child_evidence(tmp_path):
    bundle = numbering_bundle()
    mapping = next(e for e in bundle["entities"] if e["type"] == "residue_map")
    child, lineage = variant_preview(bundle, mapping["molecule_id"], "Child", "CHILD", "Independent subject isolation", [edit(mapping, 1)])["entities"]
    bundle["entities"].extend([child, lineage])
    definition = proposal(bundle); definition["molecule_ids"] = [child["id"]]
    definition["related_evidence_ids"] = [next(e["id"] for e in bundle["entities"] if e["type"] == "evidence")]
    with pytest.raises(ValidationError, match="outside its explicit scope"): hypothesis_preview(bundle, definition)
    definition["related_evidence_ids"] = []; definition["lineage_ids"] = [lineage["id"]]
    with pytest.raises(ValidationError, match="both parent and child"): hypothesis_preview(bundle, definition)


def test_sequence_reversion_does_not_invent_old_binding_unit_origin(tmp_path):
    bundle, parent, mapping = mapped_composition()
    child, lineage = variant_preview(bundle, parent["id"], "Child", "CHILD", "Independent origin loss", [edit(mapping, 1)])["entities"]
    bundle["entities"].extend([child, lineage])
    # A separate explicit synthetic map import authorizes the new child; no map was inherited.
    imported = copy.deepcopy(mapping)
    imported.update(id=new_id("residue_map"), molecule_id=child["id"], source={"name": "Separate synthetic child map input", "version": "1"})
    imported["entries"][0]["aa"] = child["chains"][0]["sequence"][0]
    bundle["entities"].append(imported)
    reverted, second_lineage = variant_preview(bundle, child["id"], "Reverted sequence", "REVERTED", "Sequence equality does not restore provenance", [edit(imported, 1, parent["chains"][0]["sequence"][0])])["entities"]
    assert reverted["chains"] == parent["chains"]
    assert reverted["component_graph"]["chains"][0]["components"][0]["origin"] is None
    assert parent["component_graph"]["chains"][0]["components"][0]["origin"] is not None
    assert second_lineage["parent_id"] == child["id"]
    store = Store(tmp_path / "reversion.sqlite3"); store.import_bundle(bundle)
    store.import_bundle({"schema_version": bundle["schema_version"], "project": bundle["project"], "entities": [reverted, second_lineage]})


def test_unknown_source_model_stays_null_and_rejects_invented_model_one(tmp_path):
    bundle = structure_bundle()
    structure = next(e for e in bundle["entities"] if e["type"] == "structure" and e["file_format"] == "mmcif")
    lines = structure["content"].splitlines()
    lines = [line for line in lines if line != "_atom_site.pdbx_PDB_model_num" and (not line.startswith("ATOM ") or line.endswith(" 1"))]
    structure["content"] = "\n".join(" ".join(line.split()[:-1]) if line.startswith("ATOM ") else line for line in lines) + "\n"
    structure["sha256"] = hashlib.sha256(structure["content"].encode()).hexdigest()
    bundle["entities"] = [e for e in bundle["entities"] if not (e["type"] == "structure_map" and e["structure_id"] == structure["id"])]
    definition = proposal(bundle)
    definition["molecule_ids"] = [structure["molecule_id"]]
    definition["structure_refs"] = [{"structure_id": structure["id"], "model": None, "structure_map_id": None}]
    result = hypothesis_preview(bundle, definition)
    assert result["entities"][0]["structure_refs"] == definition["structure_refs"]
    store = Store(tmp_path / "unknown-model.sqlite3"); store.import_bundle(bundle); store.import_bundle(result)
    definition["structure_refs"][0]["model"] = 1
    with pytest.raises(ValidationError, match="model does not exist"): hypothesis_preview(bundle, definition)
