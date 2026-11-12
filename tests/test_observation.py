"""F09: P01/P04/P06/P07, J01/J04/J06/J07, corresponding ACs."""

import copy

import pytest

from workspace_app.adapters import new_project
from workspace_app.domain import ValidationError, new_id
from workspace_app.fixtures import example_bundle
from workspace_app.observation import observation_order
from workspace_app.storage import Store
from workspace_app.discovery_fixtures import sequence_input, support_bundle
from workspace_app.adapters import preview


def measured(bundle):
    return [e for e in bundle["entities"] if e["type"] == "evidence" and e["kind"] == "measured"]


def test_exact_context_zero_missing_and_both_directions_survive_roundtrip(tmp_path):
    b = example_bundle(); original = copy.deepcopy(b)
    store = Store(tmp_path / "observations.sqlite3"); store.import_bundle(b)
    cohort = measured(b)[0]["id"]
    for direction, expected in [("ascending", [0, 3, 4, 5, 6, 7]), ("descending", [7, 6, 5, 4, 3, 0])]:
        result = observation_order(Store(store.path).bundle(b["project"]["id"]), cohort, {}, direction)
        assert [r["value"] for r in result["candidates"] if r["value"] is not None] == expected
        assert all(r["value"] is None for r in result["candidates"][6:])
        assert {r["status"] for r in result["candidates"][6:]} == {"value missing", "context incomplete"}
    assert b == original


@pytest.mark.parametrize("change", ["unit", "assay", "condition", "bool", "float", "source_name", "source_version", "kind"])
def test_no_pooling_different_recorded_context(change):
    b = example_bundle(); record = measured(b)[3]
    if change == "unit": record["unit"] = "uM"
    elif change == "assay": record["conditions"]["assay"] = "another assay"
    elif change == "condition": record["conditions"]["temperature_C"] = 26
    elif change == "bool": record["conditions"]["temperature_C"] = True
    elif change == "float": record["conditions"]["temperature_C"] = 25.0
    elif change == "source_name": record["source"]["name"] += " another file"
    elif change == "source_version": record["source"]["version"] = "2"
    elif change == "kind": record["kind"] = "computed"
    result = observation_order(b, measured(b)[0]["id"])
    assert record["id"] not in [r["evidence_id"] for r in result["candidates"]]
    assert len(result["cohorts"]) == 2
    if change == "float":
        labels = [cohort["conditions_text"] for cohort in result["cohorts"]]
        assert any('"temperature_C":25}' in label for label in labels)
        assert any('"temperature_C":25.0}' in label for label in labels)


def test_multiple_materials_require_explicit_choice_even_equal_values(tmp_path):
    b = example_bundle(); first = measured(b)[0]; second = copy.deepcopy(first)
    second["id"] = new_id("evidence")
    second["subject_id"] = next(e["id"] for e in b["entities"] if e["type"] == "material" and e["name"] == "Fixture alternate lot")
    b["entities"].append(second)
    store = Store(tmp_path / "multiple.sqlite3"); store.import_bundle(b)
    result = observation_order(b, first["id"])
    row = next(r for r in result["candidates"] if len(r["options"]) == 2)
    assert row["status"] == "choose observation" and row["value"] is None and row["evidence_id"] is None
    selected = observation_order(b, first["id"], {row["molecule_id"]: second["id"]})
    assert selected["candidates"][0]["evidence_id"] == second["id"] and selected["candidates"][0]["value"] == 0
    assert store.bundle(b["project"]["id"])["entities"] == Store(store.path).bundle(b["project"]["id"])["entities"]


@pytest.mark.parametrize("bad", [None, False, 0, "", [], {"not-a-molecule": "bad"}])
def test_malformed_choices_reject_without_falsy_fallback(bad):
    with pytest.raises(ValidationError): observation_order(example_bundle(), choices=bad)


@pytest.mark.parametrize("case", ["blank", "stale", "other_subject", "other_context", "no_context"])
def test_choice_cannot_cross_candidate_or_context(case):
    b = example_bundle(); records = measured(b)
    result = observation_order(b, records[0]["id"])
    first = next(r for r in result["candidates"] if r["evidence_id"] == records[0]["id"])
    value = {"blank": " ", "stale": new_id("evidence"), "other_subject": records[3]["id"],
             "other_context": records[2]["id"], "no_context": records[0]["id"]}[case]
    with pytest.raises(ValidationError):
        observation_order(b, None if case == "no_context" else records[0]["id"], {first["molecule_id"]: value})


@pytest.mark.parametrize("case", ["null_conditions", "empty_conditions", "blank_assay", "missing_version", "missing_unit"])
def test_incomplete_context_stays_viewable_but_cannot_rank(case):
    b = example_bundle(); record = measured(b)[0]
    if case == "null_conditions": record["conditions"] = None
    elif case == "empty_conditions": record["conditions"] = {}
    elif case == "blank_assay": record["conditions"]["assay"] = " "
    elif case == "missing_version": record["source"]["version"] = None
    elif case == "missing_unit": record["unit"] = None
    assert any(r["evidence_id"] == record["id"] for r in observation_order(b)["ineligible"])
    with pytest.raises(ValidationError): observation_order(b, record["id"])


def test_new_project_data_class_is_explicit_and_never_title_inferred():
    assert new_project("[SYNTHETIC FIXTURE] misleading title", "Test")["data_class"] == "research"
    assert new_project("Explicit fixture", "Test", "synthetic_fixture")["data_class"] == "synthetic_fixture"
    with pytest.raises(ValidationError): new_project("Bad", "Test", None)


def test_discovery_fixture_input_qc_and_explicit_support_file(tmp_path):
    project = new_project("Synthetic discovery", "Engineering only", "synthetic_fixture")
    result = preview(sequence_input(), "csv", "synthetic-discovery.csv", project)
    assert result["report"]["valid_rows"] == 800 and len(result["report"]["excluded"]) == 2
    store = Store(tmp_path / "discovery.sqlite3"); store.import_bundle(result["bundle"])
    imported = store.bundle(project["id"]); support = support_bundle(imported)
    store.import_bundle(support)
    restored = store.bundle(project["id"])
    assert len([e for e in restored["entities"] if e["type"] == "molecule"]) == 800
    viewed = observation_order(restored)
    assert len(viewed["cohorts"]) == 2
    cohort = next(c for c in viewed["cohorts"] if c["unit"] == "nM")
    ranked = observation_order(restored, cohort["id"])
    assert ranked["candidates"][0]["value"] == 0
    assert {r["status"] for r in ranked["candidates"]} >= {"value missing", "context incomplete", "different context", "choose observation", "not measured / not predicted"}
    imported["project"]["data_class"] = "research"
    with pytest.raises(ValidationError): support_bundle(imported)
