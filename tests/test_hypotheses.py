"""F11: explicit research claims, immutable original source paths and contexts."""

import copy

import pytest

from workspace_app.domain import ValidationError, new_id
from workspace_app.fixtures import example_bundle
from workspace_app.hypotheses import hypothesis_preview
from workspace_app.storage import Store
from workspace_app.structure_fixtures import structure_bundle


def definition(bundle):
    molecule = next(e for e in bundle["entities"] if e["type"] == "molecule")
    return {"text": "Synthetic proposed explanation, not an observed fact.", "question": "Which controlled experiment would distinguish the alternatives?",
            "limitations": None, "molecule_ids": [molecule["id"]], "related_evidence_ids": [], "lineage_ids": [],
            "residue_refs": [{"molecule_id": molecule["id"], "chain_id": molecule["chains"][0]["id"], "sequence_index": 1}], "structure_refs": []}


def test_saved_claim_is_distinct_proposed_and_exact_after_restart_roundtrip(tmp_path):
    b = example_bundle(); original = copy.deepcopy(b); d = definition(b)
    measurement = next(e for e in b["entities"] if e["type"] == "evidence" and e["kind"] == "measured")
    d["related_evidence_ids"] = [measurement["id"]]
    result = hypothesis_preview(b, d); record = result["entities"][0]
    assert record["type"] == "hypothesis" and record["status"] == "proposed"
    assert record["limitations"] is None and record["source"]["name"] == "Antibody Insight local researcher entry"
    assert b == original
    store = Store(tmp_path / "hypothesis.sqlite3"); store.import_bundle(b); store.import_bundle(result)
    restored = Store(store.path).bundle(b["project"]["id"])
    assert restored["entities"][:len(b["entities"])] == original["entities"]
    assert restored["entities"][-1] == record
    fresh = Store(tmp_path / "fresh.sqlite3"); fresh.import_bundle(restored); assert fresh.bundle(b["project"]["id"]) == restored


@pytest.mark.parametrize("case", ["unrelated_evidence", "unknown_evidence", "unknown_molecule", "missing_molecules", "duplicate_molecules", "wrong_chain", "bool_index", "missing_residue", "empty_question"])
def test_invalid_claim_context_cannot_save_or_change_originals(tmp_path, case):
    b = example_bundle(); d = definition(b)
    if case == "unrelated_evidence": d["related_evidence_ids"] = [next(e["id"] for e in reversed(b["entities"]) if e["type"] == "evidence")]
    elif case == "unknown_evidence": d["related_evidence_ids"] = [new_id("evidence")]
    elif case == "unknown_molecule": d["molecule_ids"] = [new_id("molecule")]
    elif case == "missing_molecules": d["molecule_ids"] = []
    elif case == "duplicate_molecules": d["molecule_ids"] *= 2
    elif case == "wrong_chain": d["residue_refs"][0]["chain_id"] = "not-a-chain"
    elif case == "bool_index": d["residue_refs"][0]["sequence_index"] = True
    elif case == "missing_residue": d["residue_refs"][0]["sequence_index"] = 99999
    elif case == "empty_question": d["question"] = " "
    store = Store(tmp_path / "reject.sqlite3"); store.import_bundle(b)
    with pytest.raises(ValidationError): hypothesis_preview(b, d)
    assert store.bundle(b["project"]["id"]) == b


def test_structural_claim_keeps_actual_model_and_refuses_another_source(tmp_path):
    b = structure_bundle(); d = definition(b)
    structure = next(e for e in b["entities"] if e["type"] == "structure")
    mapping = next(e for e in b["entities"] if e["type"] == "structure_map" and e["structure_id"] == structure["id"])
    d["structure_refs"] = [{"structure_id": structure["id"], "model": 1, "structure_map_id": mapping["id"]}]
    assert hypothesis_preview(b, d)["entities"][0]["structure_refs"] == d["structure_refs"]
    d["structure_refs"][0]["model"] = 999
    with pytest.raises(ValidationError, match="model"): hypothesis_preview(b, d)
    d["structure_refs"][0]["model"] = True
    with pytest.raises(ValidationError): hypothesis_preview(b, d)
    d["structure_refs"][0]["model"] = 1
    d["structure_refs"][0]["structure_map_id"] = next(e["id"] for e in b["entities"] if e["type"] == "structure_map" and e["structure_id"] != structure["id"])
    with pytest.raises(ValidationError, match="another coordinate source"): hypothesis_preview(b, d)


def test_import_cannot_promote_research_statement_to_validated_fact(tmp_path):
    b = example_bundle(); result = hypothesis_preview(b, definition(b)); result["entities"][0]["status"] = "validated"
    store = Store(tmp_path / "status.sqlite3"); store.import_bundle(b)
    with pytest.raises(ValidationError, match="proposed"): store.import_bundle(result)
    assert store.bundle(b["project"]["id"]) == b
