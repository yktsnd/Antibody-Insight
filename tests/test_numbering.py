"""F07: source-bearing imported coordinates; synthetic, not human golden data."""

import copy

import pytest

from workspace_app.domain import ValidationError, new_id
from workspace_app.fixtures import numbering_bundle
from workspace_app.numbering import cdr3_groups, observations
from workspace_app.storage import Store


def first_map(bundle):
    return next(e for e in bundle["entities"] if e["type"] == "residue_map")


def test_coordinate_chain_domain_regions_and_roundtrip(tmp_path):
    b = numbering_bundle(); store = Store(tmp_path / "test.sqlite3"); store.import_bundle(b)
    restored = Store(store.path).bundle(b["project"]["id"])
    assert restored == b
    target = Store(tmp_path / "target.sqlite3"); target.import_bundle(restored)
    assert target.bundle(b["project"]["id"]) == b
    maps = observations(restored)["maps"]
    heavy, light = maps[:2]
    assert heavy["chain_id"] == "H" and light["chain_id"] == "L"
    assert heavy["entries"][26]["coordinate"] == light["entries"][26]["coordinate"] == "27"
    assert heavy["entries"][26]["region"] == "CDR1"
    inserted = [e for e in heavy["entries"] if e["ins_code"]]
    assert [e["coordinate"] for e in inserted] == ["111.1", "112.1"]
    assert all(e["region"] == "CDR3" for e in inserted)
    assert heavy["entries"][-1]["coordinate"] == "129" and heavy["entries"][-1]["region"] == "FR4"
    assert heavy["cdr3_complete"] and len(heavy["cdr3_sequence"]) == 15
    groups = cdr3_groups(b)
    assert len(groups["groups"]) == 3
    assert sum(len(g["candidate_ids"]) for g in groups["groups"]) == 8


@pytest.mark.parametrize("case", ["wrong_aa", "unknown_molecule", "unknown_chain", "duplicate_coordinate", "bool_index", "float_number",
                                  "unsupported_insertion", "bad_code", "wrong_order", "missing_index", "domain_range", "bad_scheme",
                                  "bad_definition", "fixture_title_only", "missing_reviewer", "naive_review_time"])
def test_bad_maps_reject_atomically(tmp_path, case):
    b = numbering_bundle(); record = first_map(b); entry = record["entries"][0]
    if case == "wrong_aa": entry["aa"] = "X"
    elif case == "unknown_molecule": record["molecule_id"] = new_id("molecule")
    elif case == "unknown_chain": record["chain_id"] = "not-H"
    elif case == "duplicate_coordinate": record["entries"][1]["number"] = entry["number"]
    elif case == "bool_index": entry["sequence_index"] = True
    elif case == "float_number": entry["number"] = 1.0
    elif case == "unsupported_insertion": record["entries"][59]["ins_code"] = ".1"
    elif case == "bad_code": record["entries"][111]["ins_code"] = ".0"
    elif case == "wrong_order": record["entries"][111]["number"] = 112; record["entries"][112]["number"] = 111
    elif case == "missing_index": record["entries"].pop()
    elif case == "domain_range": record["sequence_end"] += 1
    elif case == "bad_scheme": record["scheme"] = "Kabat"
    elif case == "bad_definition": record["definition"] = "germline_v_region"
    elif case == "fixture_title_only": del b["project"]["data_class"]
    elif case == "missing_reviewer": record["verification"]["status"] = "source_verified"
    elif case == "naive_review_time": record["verification"].update(status="source_verified", reviewer="Declared fixture attestation", reviewed_at="2026-11-03")
    store = Store(tmp_path / "reject.sqlite3")
    with pytest.raises(ValidationError): store.import_bundle(b)
    assert store.projects() == []


@pytest.mark.parametrize("status", ["unavailable", "failed"])
def test_numbering_failure_is_preserved_not_success(tmp_path, status):
    b = numbering_bundle(1); record = first_map(b)
    record.update(status=status, reason="Source could not assign numbering", entries=[], sequence_start=None, sequence_end=None)
    store = Store(tmp_path / "test.sqlite3"); store.import_bundle(b)
    viewed = observations(store.bundle(b["project"]["id"]))["maps"][0]
    assert viewed["status"] == status and not viewed["eligible"] and viewed["cdr3_sequence"] is None
    assert cdr3_groups(b)["groups"] == []


def test_partial_and_empty_cdr3_do_not_become_complete_groups(tmp_path):
    b = numbering_bundle(1)
    for record in (e for e in b["entities"] if e["type"] == "residue_map"):
        record["entries"] = record["entries"][:110]; record["sequence_end"] = 110
    store = Store(tmp_path / "partial.sqlite3"); store.import_bundle(b)
    assert not observations(b)["maps"][0]["cdr3_complete"]
    assert cdr3_groups(b)["groups"] == []
    # Both anchors with no observed CDR3 cannot establish an empty CDR3 group.
    b = numbering_bundle(1); record = first_map(b)
    record["entries"] = [dict(record["entries"][0], number=104), dict(record["entries"][1], number=118)]
    record["sequence_end"] = 2
    store = Store(tmp_path / "empty.sqlite3"); store.import_bundle(b)
    assert cdr3_groups(b)["groups"] == []


def test_multiple_heavy_maps_require_explicit_choice(tmp_path):
    b = numbering_bundle(1); record = first_map(b); other = copy.deepcopy(record)
    other["id"] = new_id("residue_map"); other["source"]["version"] = "alternate fixture annotation"
    b["entities"].append(other)
    store = Store(tmp_path / "ambiguous.sqlite3"); store.import_bundle(b)
    grouped = cdr3_groups(b)
    assert grouped["groups"] == [] and grouped["candidates"][0]["status"] == "choose map/domain"
    chosen = cdr3_groups(b, {record["molecule_id"]: other["id"]})
    assert len(chosen["groups"]) == 1 and chosen["candidates"][0]["map_id"] == other["id"]
    with pytest.raises(ValidationError): cdr3_groups(b, {record["molecule_id"]: new_id("residue_map")})


def test_unverified_maps_inspectable_but_not_eligible_and_declared_attestation_is_recorded(tmp_path):
    b = numbering_bundle(1); record = first_map(b)
    record["verification"]["status"] = "unverified"
    store = Store(tmp_path / "unverified.sqlite3"); store.import_bundle(b)
    assert observations(b)["maps"][0]["status"] == "mapped" and not observations(b)["maps"][0]["eligible"]
    assert cdr3_groups(b)["groups"] == []
    record["verification"].update(status="source_verified", reviewer="DECLARED FIXTURE ATTESTATION; NOT HUMAN VALIDATION",
                                  reviewed_at="2026-11-03T00:00:00+09:00")
    b["entities"] = [e for e in b["entities"] if e["type"] != "residue_map" or e is record]
    second = Store(tmp_path / "attested.sqlite3"); second.import_bundle(b)
    viewed = observations(b)["maps"][0]
    assert viewed["eligible"] and viewed["verification"]["reviewer"].startswith("DECLARED FIXTURE")
