"""Independent F09 boundaries: P01/J01/AC-J01; no scientific golden claims."""

import copy

import pytest

from workspace_app.domain import ValidationError
from workspace_app.fixtures import example_bundle
from workspace_app.observation import observation_order
from workspace_app.storage import Store


def measurements(bundle):
    return [e for e in bundle["entities"] if e["type"] == "evidence" and e["kind"] == "measured"]


def test_original_cohort_member_survives_earlier_representative_and_reimport(tmp_path):
    bundle = example_bundle()
    original = measurements(bundle)[0]
    added = copy.deepcopy(original)
    added["id"] = "evd_00000000-0000-4000-8000-000000000001"
    added["value"] = -2.5
    bundle["entities"].append(added)
    before = copy.deepcopy(bundle)
    ambiguous = next(r for r in observation_order(bundle, original["id"])["candidates"] if r["evidence_id"] is None and len(r["options"]) == 2)
    choices = {ambiguous["molecule_id"]: original["id"]}
    baseline = observation_order(bundle, original["id"], choices)
    assert next(c for c in baseline["cohorts"] if original["id"] in c["evidence_ids"])["id"] == added["id"]
    assert next(r for r in baseline["candidates"] if r["molecule_id"] == ambiguous["molecule_id"])["value"] == 0
    bundle["entities"].reverse()
    store = Store(tmp_path / "shuffled.sqlite3")
    store.import_bundle(bundle)
    assert observation_order(Store(store.path).bundle(bundle["project"]["id"]), original["id"], choices) == baseline
    assert list(reversed(bundle["entities"])) == before["entities"]


def test_explicit_null_never_falls_back_to_equal_sequence_or_other_lot(tmp_path):
    bundle = example_bundle()
    original = measurements(bundle)[0]
    null = copy.deepcopy(original)
    null["id"] = "evd_00000000-0000-4000-8000-000000000002"
    null["subject_id"] = next(e["id"] for e in bundle["entities"] if e["type"] == "material" and e["name"] == "Fixture alternate lot")
    null["value"] = None
    negative = measurements(bundle)[3]
    negative["value"] = -3.25
    bundle["entities"].append(null)
    store = Store(tmp_path / "explicit-null.sqlite3")
    store.import_bundle(bundle)
    ambiguous = next(r for r in observation_order(bundle, original["id"])["candidates"] if len(r["options"]) == 2)
    same_sequence = [e for e in bundle["entities"] if e["type"] == "molecule"][:2]
    assert same_sequence[0]["chains"] == same_sequence[1]["chains"]
    choices = {ambiguous["molecule_id"]: null["id"]}
    for direction in ("ascending", "descending"):
        result = observation_order(Store(store.path).bundle(bundle["project"]["id"]), original["id"], choices, direction)
        rows = {r["molecule_id"]: r for r in result["candidates"]}
        assert rows[ambiguous["molecule_id"]]["evidence_id"] == null["id"]
        assert rows[ambiguous["molecule_id"]]["value"] is None
        assert rows[ambiguous["molecule_id"]]["status"] == "value missing"
        assert rows[same_sequence[1]["id"]]["value"] is None
        numeric = [r["value"] for r in result["candidates"] if r["value"] is not None]
        assert -3.25 in numeric and numeric == sorted(numeric, reverse=direction == "descending")
        assert all(r["value"] is None for r in result["candidates"][len(numeric):])
    with pytest.raises(ValidationError):
        observation_order(bundle, original["id"], {same_sequence[1]["id"]: null["id"]})


@pytest.mark.parametrize("variant", ["object_order", "array_order", "typed_nested", "unit_case"])
def test_nested_context_keeps_original_types_array_order_and_unit_case(variant):
    bundle = example_bundle()
    first, second = measurements(bundle)[:2]
    first["conditions"] = {"assay": "explicit fixture", "steps": [1, {"flag": False, "pH": 7}]}
    second["conditions"] = {"steps": [1, {"pH": 7, "flag": False}], "assay": "explicit fixture"}
    if variant == "array_order": second["conditions"]["steps"].reverse()
    elif variant == "typed_nested": second["conditions"]["steps"][1]["flag"] = 0
    elif variant == "unit_case": second["unit"] = "NM"
    original = copy.deepcopy(bundle)
    result = observation_order(bundle, first["id"])
    cohort = next(c for c in result["cohorts"] if first["id"] in c["evidence_ids"])
    assert (second["id"] in cohort["evidence_ids"]) == (variant == "object_order")
    assert bundle == original
