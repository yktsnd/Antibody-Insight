"""Verify mature-peptide annotations against explicit synthetic CDS coordinates."""

from pathlib import Path

from antibody_insight import imports


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "mature.gb"


def synthetic_records():
    return {
        record["candidate"]: record
        for record in imports.annotated(FIXTURE.read_bytes(), ".gb", "mature")
    }


def cds_features(record):
    return [feature for feature in record["features"] if feature["type"] == "CDS"]


def test_explicit_mat_peptide_maps_to_mature_residue_interval():
    record = synthetic_records()["mature_positive"]
    mature_index = next(
        index for index, feature in enumerate(record["features"])
        if feature["type"] == "mat_peptide"
    )
    cds = cds_features(record)[0]
    mature_feature = record["features"][mature_index]

    assert mature_index == 2
    assert cds["translation"] == "MAKG"
    assert mature_feature["parts"] == [[7, 12, 1]]
    assert mature_feature["qualifiers"]["translation"] == ["KG"]
    assert cds["mature_regions"] == [
        {"feature_index": 2, "start": 3, "end": 4}
    ]


def test_partial_codon_boundary_is_not_associated():
    record = synthetic_records()["mature_middle_boundary"]

    assert cds_features(record)[0]["mature_regions"] == []


def test_reverse_strand_features_map_in_translation_order():
    record = synthetic_records()["mature_reverse"]
    mature_index = next(
        index for index, feature in enumerate(record["features"])
        if feature["type"] == "mat_peptide"
    )

    assert cds_features(record)[0]["translation"] == "MAKG"
    assert cds_features(record)[0]["mature_regions"] == [
        {"feature_index": mature_index, "start": 3, "end": 4}
    ]


def test_opposite_strand_mature_feature_is_not_associated():
    record = synthetic_records()["mature_opposite_strand"]

    assert cds_features(record)[0]["translation"] == "MAKG"
    assert cds_features(record)[0]["mature_regions"] == []


def test_mat_peptide_overlapping_multiple_cdss_has_no_inferred_owner():
    record = synthetic_records()["mature_ambiguous"]

    assert len(cds_features(record)) == 2
    assert [cds["mature_regions"] for cds in cds_features(record)] == [[], []]


def test_signal_peptide_alone_does_not_define_a_mature_region():
    record = synthetic_records()["mature_signal_only"]

    assert any(feature["type"] == "sig_peptide" for feature in record["features"])
    assert not any(feature["type"] == "mat_peptide" for feature in record["features"])
    assert cds_features(record)[0]["mature_regions"] == []
