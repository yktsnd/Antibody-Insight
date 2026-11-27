"""Q1, R-08/R-21, AC-01/AC-03, V-09: synthetic CDS coordinate checks.

All expected coordinates below are hand-derived, 1-based positions in the
original DNA record and ordered in translation direction. The fixtures use
short, nonfunctional synthetic strings; the tests do not infer any biological
identity or mature-chain correspondence.
"""

from pathlib import Path

import pytest

from antibody_insight import imports


FIXTURES = Path(__file__).resolve().parent / "fixtures"


def cds_feature(filename):
    path = FIXTURES / filename
    record = imports.annotated(path.read_bytes(), ".gb", path.stem)[0]
    feature = next(feature for feature in record["features"] if feature["type"] == "CDS")
    return record, feature


@pytest.mark.parametrize(
    ("filename", "frame_offset", "protein", "codons", "stop", "flanks"),
    [
        # Forward 3..11: ATG(3,4,5) GCT(6,7,8) TAA(9,10,11).
        (
            "cds_plus.gb",
            0,
            "MA",
            [[3, 4, 5], [6, 7, 8]],
            [9, 10, 11],
            [1, 2],
        ),
        # complement(3..11): ATG(11,10,9) GCT(8,7,6) TAA(5,4,3).
        (
            "cds_reverse.gb",
            0,
            "MA",
            [[11, 10, 9], [8, 7, 6]],
            [5, 4, 3],
            [1, 2, 12, 13],
        ),
        # join(1..4,10..14): the GCT codon crosses the join after base 4.
        (
            "cds_join_boundary.gb",
            0,
            "MA",
            [[1, 2, 3], [4, 10, 11]],
            [12, 13, 14],
            [5, 6, 7, 8, 9],
        ),
        # codon_start=2: skip base 1; complete translated region is 2..10.
        (
            "cds_codon_start_2.gb",
            1,
            "MA",
            [[2, 3, 4], [5, 6, 7]],
            [8, 9, 10],
            [1],
        ),
    ],
)
def test_complete_cds_maps_codons_to_original_dna(
    filename, frame_offset, protein, codons, stop, flanks
):
    record, feature = cds_feature(filename)

    assert feature["coding"] == {"frame_offset": frame_offset, "table": 1}
    assert feature["translation"] == protein
    assert record["sequence"]

    for residue_number, expected in enumerate(codons, 1):
        assert imports.codon_positions(feature, residue_number) == expected
        assert [imports.residue_at(feature, position) for position in expected] == [
            residue_number
        ] * 3

    stop_number = len(protein) + 1
    assert imports.codon_positions(feature, stop_number) == stop
    assert [imports.residue_at(feature, position) for position in stop] == [stop_number] * 3
    assert imports.codon_positions(feature, 0) == []
    assert imports.codon_positions(feature, stop_number + 1) == []
    assert all(imports.residue_at(feature, position) is None for position in flanks)


@pytest.mark.parametrize(
    "filename",
    [
        "cds_unknown_coordinates.gb",
        "cds_incomplete.gb",
        "cds_missing_start.gb",
        "cds_translation_mismatch.gb",
        "cds_translation_exception.gb",
    ],
)
def test_non_exact_or_invalid_cds_has_no_codon_mapping(filename):
    _, feature = cds_feature(filename)

    assert feature["coding"] is None
    assert imports.codon_positions(feature, 1) == []
    assert imports.residue_at(feature, 1) is None
