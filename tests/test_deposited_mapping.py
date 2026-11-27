"""Check deposited-sequence mapping independently from observed atom rows."""

from pathlib import Path

from antibody_insight import structures


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "partial.cif"


def test_mmcif_maps_declared_sequence_and_preserves_unobserved_residue():
    packet = structures.preview(FIXTURE, {"id": "dummy", "kind": "AA", "seq": "MGA"})

    # label_asym_id L is the deposited polymer instance; auth_asym_id X is
    # the author chain used by the coordinate parser and returned mapping.
    assert packet["chains"] == ["X"]
    assert packet["mappings"]["X"] == [[10, ""], None, [10, "A"]]


def test_observed_atom_subset_does_not_override_declared_polymer_sequence():
    packet = structures.preview(FIXTURE, {"id": "dummy", "kind": "AA", "seq": "MA"})

    # The atom rows contain Met and Ala, but entity_poly_seq declares MGA.
    assert packet["mappings"] == {}


def test_dna_component_is_not_mapped_to_protein_coordinates():
    packet = structures.preview(FIXTURE, {"id": "dummy", "kind": "DNA", "seq": "ATG"})

    assert packet["mappings"] == {}
