"""Hand-checked global pairwise alignment contract for short synthetic strings."""

import pytest

from antibody_insight.alignment import align_pair


def test_internal_single_residue_deletion_keeps_later_positions_offset():
    # Query MGTK lacks reference residue A at position 2 in MAGTK.
    result = align_pair("MGTK", "MAGTK", "AA")

    assert result["columns"] == [[1, 1], [None, 2], [2, 3], [3, 4], [4, 5]]
    assert result["unique"] is True
    assert result["matches"] == 4
    assert result["paired"] == 4
    assert result["score"] == 3  # 4 matches (+8) and one gap opening (-5).


def test_mismatch_is_a_paired_nonmatch():
    result = align_pair("MARG", "MAKG", "AA")

    assert result["columns"] == [[1, 1], [2, 2], [3, 3], [4, 4]]
    assert result["unique"] is True
    assert result["matches"] == 3
    assert result["paired"] == 4
    assert result["score"] == 5  # 3 matches (+6) and one mismatch (-1).


def test_repeated_residue_has_two_equally_optimal_global_paths():
    # AA vs A scores -3 whether the reference A pairs with query position 1 or 2:
    # one match (+2) and one length-one terminal gap (-5) in either case.
    result = align_pair("AA", "A", "AA")

    assert result["unique"] is False
    assert len(result["columns"]) == 2
    assert result["matches"] == 1
    assert result["paired"] == 1
    assert result["score"] == -3  # One match (+2) and one terminal gap (-5).


def test_two_residue_gap_uses_one_opening_and_one_extension_penalty():
    # MGTK aligns to MAAGTK with a two-residue reference-only gap after M.
    result = align_pair("MGTK", "MAAGTK", "AA")

    assert result["columns"] == [
        [1, 1], [None, 2], [None, 3], [2, 4], [3, 5], [4, 6]
    ]
    assert result["unique"] is True
    assert result["matches"] == 4
    assert result["paired"] == 4
    assert result["score"] == 2  # 4 matches (+8), gap open (-5), extension (-1).


@pytest.mark.parametrize(
    ("sequence", "kind"),
    [("MGA", "AA"), ("ATGN", "DNA")],
)
def test_valid_protein_and_ambiguous_dna_alphabets_are_accepted(sequence, kind):
    # Even identical letters only establish positional alignment, not molecule identity.
    result = align_pair(sequence, sequence, kind)

    assert result["columns"] == [[i, i] for i in range(1, len(sequence) + 1)]
    assert result["unique"] is True
    assert result["matches"] == len(sequence)
    assert result["paired"] == len(sequence)


@pytest.mark.parametrize(
    ("query", "reference", "kind"),
    [
        ("M?A", "MGA", "AA"),
        ("ATX", "ATG", "DNA"),
        ("MGA", "MGA", "RNA"),
        ("", "A", "AA"),
    ],
)
def test_invalid_sequence_or_kind_is_rejected(query, reference, kind):
    with pytest.raises(ValueError):
        align_pair(query, reference, kind)
