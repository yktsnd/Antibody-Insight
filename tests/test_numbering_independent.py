"""Independent F07 scientific-definition and identity boundary replays.

All sequences/attestations are synthetic engineering fixtures, not golden data.
"""

import copy

import pytest

from workspace_app.domain import ValidationError, new_id
from workspace_app.fixtures import numbering_bundle
from workspace_app.numbering import cdr3_groups, observations, region_for
from workspace_app.storage import Store


def heavy_map(bundle):
    return next(e for e in bundle["entities"] if e["type"] == "residue_map" and e["chain_type"] == "heavy")


def molecule_for(bundle, record):
    return next(e for e in bundle["entities"] if e["id"] == record["molecule_id"])


def coordinate_fixture(coordinates):
    bundle = numbering_bundle(1)
    record = heavy_map(bundle)
    alphabet = "ACDEFGHIKLMNPQRSTVWY"
    record["entries"] = [{"sequence_index": i, "aa": alphabet[(i - 1) % len(alphabet)], "number": number, "ins_code": code}
                         for i, (number, code) in enumerate(coordinates, 1)]
    record["sequence_end"] = len(coordinates)
    molecule_for(bundle, record)["chains"][0]["sequence"] = "".join(e["aa"] for e in record["entries"])
    bundle["entities"] = [e for e in bundle["entities"] if e["type"] != "residue_map" or e is record]
    return bundle


def test_long_insertion_suffixes_preserve_identity_and_sequence_order_on_restart(tmp_path):
    coordinates = ([(n, "") for n in range(1, 112)] + [(111, f".{n}") for n in range(1, 11)] +
                   [(112, f".{n}") for n in range(10, 0, -1)] + [(n, "") for n in range(112, 130)])
    bundle = coordinate_fixture(coordinates)
    store = Store(tmp_path / "long-insertions.sqlite3")
    store.import_bundle(bundle)
    restored = Store(store.path).bundle(bundle["project"]["id"])
    viewed = observations(restored)["maps"][0]
    assert [e["coordinate"] for e in viewed["entries"] if e["ins_code"]] == [
        *[f"111.{n}" for n in range(1, 11)], *[f"112.{n}" for n in range(10, 0, -1)]]
    assert viewed["cdr3_complete"]
    expected = "".join(e["aa"] for e in heavy_map(bundle)["entries"] if 105 <= e["number"] <= 117)
    assert cdr3_groups(restored)["groups"][0]["cdr3_sequence"] == expected
    assert restored == bundle


@pytest.mark.parametrize("number,expected", [(26,"FR1"),(27,"CDR1"),(38,"CDR1"),(39,"FR2"),(55,"FR2"),(56,"CDR2"),
                                           (65,"CDR2"),(66,"FR3"),(104,"FR3"),(105,"CDR3"),(117,"CDR3"),(118,"FR4"),(129,"FR4")])
def test_declared_imgt_nomenclature_region_boundaries(number, expected):
    assert region_for(number) == expected


@pytest.mark.parametrize("number,code", [(60,".1"),(84,"A"),(111,".01"),(112,".0"),(111,".1e1")])
def test_supported_subset_never_reinterprets_other_imgt_or_noncanonical_coordinates(tmp_path, number, code):
    bundle = coordinate_fixture([(number, code)])
    store = Store(tmp_path / "unsupported.sqlite3")
    with pytest.raises(ValidationError, match="Unsupported IMGT insertion"):
        store.import_bundle(bundle)
    assert store.projects() == []


@pytest.mark.parametrize("coordinates", [[(n, "") for n in range(105, 111)], [(104,""),(118,"")]])
def test_partial_or_unobserved_cdr3_is_not_an_empty_or_complete_group(tmp_path, coordinates):
    bundle = coordinate_fixture(coordinates)
    store = Store(tmp_path / "partial.sqlite3")
    store.import_bundle(bundle)
    viewed = observations(bundle)["maps"][0]
    assert viewed["cdr3_sequence"] is None and not viewed["cdr3_complete"]
    assert cdr3_groups(bundle)["groups"] == []


def test_short_observed_cdr3_keeps_gaps_without_padding_residues(tmp_path):
    bundle = coordinate_fixture([(n, "") for n in (104,105,106,107,115,116,117,118)])
    store = Store(tmp_path / "short.sqlite3")
    store.import_bundle(bundle)
    viewed = observations(bundle)["maps"][0]
    assert viewed["cdr3_complete"] and viewed["cdr3_sequence"] == "CDEFGH"
    assert len(viewed["cdr3_sequence"]) == 6


def test_two_heavy_domains_in_one_chain_require_exact_map_choice_after_restart(tmp_path):
    bundle = numbering_bundle(1)
    first = heavy_map(bundle)
    molecule = molecule_for(bundle, first)
    chain = molecule["chains"][0]
    length = len(chain["sequence"])
    chain["sequence"] *= 2
    second = copy.deepcopy(first)
    second["id"] = new_id("residue_map")
    second["domain_id"] = "second explicit heavy domain"
    second["sequence_start"] += length
    second["sequence_end"] += length
    for entry in second["entries"]:
        entry["sequence_index"] += length
    bundle["entities"].append(second)
    store = Store(tmp_path / "domains.sqlite3")
    store.import_bundle(bundle)
    restored = Store(store.path).bundle(bundle["project"]["id"])
    unselected = cdr3_groups(restored)
    assert unselected["groups"] == [] and unselected["candidates"][0]["status"] == "choose map/domain"
    selected = cdr3_groups(restored, {molecule["id"]: second["id"]})
    assert selected["candidates"][0]["map_id"] == second["id"]


@pytest.mark.parametrize("choices", [[], False, 0, ""])
def test_falsy_nonobject_map_choices_are_rejected_instead_of_silent_fallback(choices):
    with pytest.raises(ValidationError):
        cdr3_groups(numbering_bundle(1), choices)


def test_unknown_molecule_choice_is_not_silently_ignored():
    bundle = numbering_bundle(1)
    with pytest.raises(ValidationError):
        cdr3_groups(bundle, {new_id("molecule"): heavy_map(bundle)["id"]})


def test_same_sequence_other_molecule_gets_no_implicit_map_and_wrong_choice_rejects(tmp_path):
    bundle = numbering_bundle(1)
    first = heavy_map(bundle)
    clone = copy.deepcopy(molecule_for(bundle, first))
    clone["id"] = new_id("molecule")
    clone["external_id"] = "SAME-SEQUENCE-DISTINCT-IDENTITY"
    bundle["entities"].append(clone)
    store = Store(tmp_path / "identity.sqlite3")
    store.import_bundle(bundle)
    grouped = cdr3_groups(bundle)
    other = next(c for c in grouped["candidates"] if c["molecule_id"] == clone["id"])
    assert other["status"] == "mapping unavailable" and other["map_id"] is None
    with pytest.raises(ValidationError):
        cdr3_groups(bundle, {clone["id"]: first["id"]})


def test_actual_cross_project_same_sequence_cannot_satisfy_a_map_reference(tmp_path):
    foreign, incoming = numbering_bundle(2), numbering_bundle(1)
    foreign_molecule = molecule_for(foreign, heavy_map(foreign))
    incoming_molecule = molecule_for(incoming, heavy_map(incoming))
    assert foreign_molecule["chains"][0]["sequence"] == incoming_molecule["chains"][0]["sequence"]
    store = Store(tmp_path / "cross-project.sqlite3")
    store.import_bundle(foreign)
    heavy_map(incoming)["molecule_id"] = foreign_molecule["id"]
    with pytest.raises(ValidationError, match="numbered molecule"):
        store.import_bundle(incoming)
    assert store.projects() == [foreign["project"]]
    assert store.bundle(foreign["project"]["id"]) == foreign


def test_old_project_class_absence_stays_absent_and_title_never_enables_unverified_group(tmp_path):
    bundle = numbering_bundle(1)
    del bundle["project"]["data_class"]
    for record in (e for e in bundle["entities"] if e["type"] == "residue_map"):
        record["verification"]["status"] = "unverified"
    store = Store(tmp_path / "old-project.sqlite3")
    store.import_bundle(bundle)
    restored = Store(store.path).bundle(bundle["project"]["id"])
    assert "data_class" not in restored["project"]
    assert "[SYNTHETIC FIXTURE]" in restored["project"]["title"]
    assert cdr3_groups(restored)["groups"] == []


@pytest.mark.parametrize("target", ["verification", "entry"])
def test_unknown_nested_map_fields_reject_without_project_insertion(tmp_path, target):
    bundle = numbering_bundle(1)
    record = heavy_map(bundle)
    (record["verification"] if target == "verification" else record["entries"][0])["imaginary_confidence"] = 0.99
    store = Store(tmp_path / "unknown.sqlite3")
    with pytest.raises(ValidationError) as error:
        store.import_bundle(bundle)
    assert "imaginary_confidence" in error.value.details[0]
    assert store.projects() == []
