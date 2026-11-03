"""F10 source-numbered designs: P02/P04, J02/J04, corresponding ACs."""

import copy

import pytest

from workspace_app.design import design_context, variant_preview
from workspace_app.domain import ValidationError, new_id
from workspace_app.fixtures import composition_bundle, numbering_bundle
from workspace_app.storage import Store


def parent_and_maps(bundle):
    parent = next(e for e in bundle["entities"] if e["type"] == "molecule")
    maps = [e for e in bundle["entities"] if e["type"] == "residue_map" and e["molecule_id"] == parent["id"]]
    return parent, maps


def request(record, number=111, ins_code=".1", to_aa="A"):
    return {"parent_map_id": record["id"], "number": number, "ins_code": ins_code, "to_aa": to_aa, "reference_map_id": None}


def preview(bundle, mutations):
    parent, _ = parent_and_maps(bundle)
    return variant_preview(bundle, parent["id"], "Explicit child", "CHILD-001", "Test a defined substitution; function remains unverified.", mutations)


def test_exact_insertion_child_lineage_parent_unchanged_no_measurement_copy_and_roundtrip(tmp_path):
    b = numbering_bundle(); original = copy.deepcopy(b); parent, maps = parent_and_maps(b)
    changes = [request(maps[0]), request(maps[1], 27, "", "W")]
    result = preview(b, changes); child, lineage = result["entities"]
    assert b == original and len(result["entities"]) == 2
    assert child["id"] != parent["id"] and child["chains"][0]["sequence"][111] == "A"
    assert child["chains"][0]["sequence"][110] == parent["chains"][0]["sequence"][110]
    assert child["chains"][1]["sequence"][26] == "W"
    assert lineage["change_set"]["mutations"][0] == {**changes[0], "chain_id": "H", "domain_id": "fixture-V", "scheme": "IMGT",
                                                    "sequence_index": 112, "from_aa": parent["chains"][0]["sequence"][111], "region": "CDR3"}
    store = Store(tmp_path / "design.sqlite3"); store.import_bundle(b); store.import_bundle(result)
    restored = Store(store.path).bundle(b["project"]["id"])
    assert restored["entities"][:len(b["entities"])] == original["entities"]
    assert not [e for e in restored["entities"] if e["type"] in ("material", "construct", "evidence", "residue_map", "structure") and
                (e.get("molecule_id") == child["id"] or e.get("subject_id") == child["id"])]
    fresh = Store(tmp_path / "fresh.sqlite3"); fresh.import_bundle(restored); assert fresh.bundle(b["project"]["id"]) == restored


@pytest.mark.parametrize("case", ["missing_insertion", "float_number", "bool_number", "wrong_molecule", "noop", "duplicate", "unknown_target", "blank_reference", "unavailable", "failed", "unverified"])
def test_bad_numbered_design_never_changes_existing_data(tmp_path, case):
    b = numbering_bundle(); parent, maps = parent_and_maps(b); r = request(maps[0])
    if case == "missing_insertion": r["ins_code"] = ".3"
    elif case == "float_number": r["number"] = 111.1
    elif case == "bool_number": r["number"] = True
    elif case == "wrong_molecule": r["parent_map_id"] = next(e["id"] for e in b["entities"] if e["type"] == "residue_map" and e["molecule_id"] != parent["id"])
    elif case == "noop": r["to_aa"] = parent["chains"][0]["sequence"][111]
    elif case == "unknown_target": r["to_aa"] = "X"
    elif case == "blank_reference": r["reference_map_id"] = ""
    elif case in ("unavailable", "failed"):
        maps[0].update(status=case, entries=[], reason="Numbering source did not map", sequence_start=None, sequence_end=None)
    elif case == "unverified": maps[0]["verification"]["status"] = "unverified"
    store = Store(tmp_path / "reject.sqlite3"); store.import_bundle(b); before = store.bundle(b["project"]["id"])
    with pytest.raises(ValidationError): preview(b, [r, copy.deepcopy(r)] if case == "duplicate" else [r])
    assert store.bundle(b["project"]["id"]) == before


def test_overlapping_maps_deduplicate_actual_raw_position_not_coordinate_name():
    b = numbering_bundle(); _, maps = parent_and_maps(b); alternate = copy.deepcopy(maps[0]); alternate["id"] = new_id("residue_map")
    b["entities"].append(alternate)
    with pytest.raises(ValidationError, match="Duplicate source residue"):
        preview(b, [request(maps[0]), request(alternate)])
    # The same integer position on another chain is a separate residue.
    assert len(preview(b, [request(maps[0], 27, ""), request(maps[1], 27, "")])["entities"]) == 2


def test_reference_gaps_and_partial_domains_never_invent_positions(tmp_path):
    b = numbering_bundle(); parent, maps = parent_and_maps(b)
    reference = next(e for e in b["entities"] if e["type"] == "residue_map" and e["molecule_id"] != parent["id"] and e["chain_type"] == "heavy")
    reference["entries"] = reference["entries"][:110]; reference["sequence_end"] = 110
    store = Store(tmp_path / "partial.sqlite3"); store.import_bundle(b)
    context = design_context(b, parent["id"], maps[0]["id"], reference["id"])
    assert context["different_observed_cdr_counts"]
    assert context["parent_observed_cdr_counts"] == {"CDR1": 12, "CDR2": 10, "CDR3": 15}
    assert context["reference_observed_cdr_counts"] == {"CDR1": 12, "CDR2": 10, "CDR3": 6}
    assert context["parent_map"]["cdr3_complete"] and not context["reference_map"]["cdr3_complete"]
    assert next(row for row in context["rows"] if row["coordinate"] == "111.1")["reference"] is None
    r = request(maps[0]); r["reference_map_id"] = reference["id"]
    assert preview(b, [r])["entities"][1]["change_set"]["mutations"][0]["reference_map_id"] == reference["id"]
    maps[0]["entries"] = maps[0]["entries"][:110]; maps[0]["sequence_end"] = 110
    assert preview(b, [request(maps[0], 27, "")])
    with pytest.raises(ValidationError, match="mapping unavailable"): preview(b, [request(maps[0])])


@pytest.mark.parametrize("field", ["from_aa", "sequence_index", "chain_id", "domain_id", "region", "scheme"])
def test_fabricated_imported_change_identity_rejects_atomically(tmp_path, field):
    b = numbering_bundle(); _, maps = parent_and_maps(b); result = preview(b, [request(maps[0])])
    mutation = result["entities"][1]["change_set"]["mutations"][0]
    mutation[field] = mutation[field] + 1 if field == "sequence_index" else "wrong"
    store = Store(tmp_path / "tamper.sqlite3"); store.import_bundle(b)
    with pytest.raises(ValidationError): store.import_bundle(result)
    assert store.bundle(b["project"]["id"]) == b


def test_component_edit_explicitly_drops_only_changed_exact_origin_and_keeps_copies(tmp_path):
    b = composition_bundle()
    parent = next(e for e in b["entities"] if e.get("component_graph"))
    chain = parent["chains"][0]
    mapping = {"id": new_id("residue_map"), "type": "residue_map", "project_id": b["project"]["id"], "created_at": parent["created_at"],
               "molecule_id": parent["id"], "chain_id": chain["id"], "domain_id": "synthetic interval", "chain_type": "heavy",
               "scheme": "IMGT", "definition": "rearranged_v_domain", "status": "mapped", "reason": None,
               "sequence_start": 1, "sequence_end": len(chain["sequence"]),
               "source": {"name": "SYNTHETIC component interval engineering test", "version": "1"},
               "verification": {"status": "engineering_fixture", "reference": "No biological numbering validity claimed", "reviewer": None, "reviewed_at": None},
               "entries": [{"sequence_index": i, "aa": aa, "number": i, "ins_code": ""} for i, aa in enumerate(chain["sequence"], 1)]}
    b["entities"].append(mapping)
    result = variant_preview(b, parent["id"], "Component child", "COMP-CHILD", "Test a declared segment; assess assembly separately.", [request(mapping, 1, "")])
    child = result["entities"][0]; before = parent["component_graph"]["chains"][0]; after = child["component_graph"]["chains"][0]
    assert before["components"][0]["origin"] is not None and after["components"][0]["origin"] is None
    assert before["components"][1:] == after["components"][1:]
    assert before["copies"] == after["copies"] == 2
    assert child["component_graph"]["connections"] == parent["component_graph"]["connections"]
    store = Store(tmp_path / "components.sqlite3"); store.import_bundle(b); store.import_bundle(result)
    tampered = copy.deepcopy(result); tampered["entities"][0]["component_graph"]["chains"][0]["components"][0]["origin"] = before["components"][0]["origin"]
    fresh = Store(tmp_path / "tamper-component.sqlite3"); fresh.import_bundle(b)
    with pytest.raises(ValidationError): fresh.import_bundle(tampered)
    assert fresh.bundle(b["project"]["id"]) == b
