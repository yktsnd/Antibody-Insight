"""Independent F08 source-identity boundaries. All coordinates are synthetic."""

import copy
import hashlib

import pytest

from workspace_app.domain import ValidationError, new_id
from workspace_app.structure_fixtures import structure_bundle
from workspace_app.storage import Store
from workspace_app.structures import parse_structure, structure_observation


TAGS = "group_PDB id type_symbol label_atom_id label_alt_id label_comp_id label_asym_id label_seq_id pdbx_PDB_ins_code Cartn_x Cartn_y Cartn_z occupancy B_iso_or_equiv auth_seq_id auth_comp_id auth_asym_id pdbx_PDB_model_num pdbx_PDB_segment_id".split()


def cif_text(changes=None, omitted=(), count=1):
    tags = [tag for tag in TAGS if tag not in omitted]
    lines = ["data_independent_synthetic", "loop_", *["_atom_site." + tag for tag in tags]]
    for i in range(1, count + 1):
        values = dict(zip(TAGS, ["ATOM", str(i), "C", "CA", ".", "ALA", "L", str(i), ".", "0", "1", "2", "?", ".", str(i), "ALA", "A", "1", "."]))
        values.update(changes or {})
        lines.append(" ".join(values[tag] for tag in tags))
    return "\n".join(lines) + "\n"


def first(bundle, kind):
    return next(e for e in bundle["entities"] if e["type"] == kind)


def one_structure_bundle():
    bundle = structure_bundle()
    molecule = first(bundle, "molecule")
    structure = first(bundle, "structure")
    mapping = first(bundle, "structure_map")
    evidence = [e for e in bundle["entities"] if e["type"] == "evidence" and e["subject_id"] == structure["id"]]
    bundle["entities"] = [molecule, structure, mapping, *evidence]
    return bundle


@pytest.mark.parametrize("field", ["occupancy", "B_iso_or_equiv", "auth_seq_id", "label_seq_id"])
@pytest.mark.parametrize("literal", ["'.'", "'?' "])
def test_quoted_cif_missing_marker_is_literal_and_invalid_in_numeric_field(field, literal):
    with pytest.raises(ValidationError):
        parse_structure(cif_text({field: literal}), "mmcif")


def test_quoted_cif_identifier_codes_and_unknown_codes_remain_distinct():
    unknown = parse_structure(cif_text({"auth_asym_id": "?", "pdbx_PDB_ins_code": "?", "label_alt_id": "?"}), "mmcif")["atoms"][0]
    quoted = parse_structure(cif_text({"auth_asym_id": "'?'", "pdbx_PDB_ins_code": "'?'", "label_alt_id": "'?'"}), "mmcif")["atoms"][0]
    blank = parse_structure(cif_text(), "mmcif")["atoms"][0]
    assert (unknown["auth_chain"], unknown["insertion_code"], unknown["altloc"]) == (None, None, None)
    assert (quoted["auth_chain"], quoted["insertion_code"], quoted["altloc"]) == ("?", "?", "?")
    assert blank["insertion_code"] == blank["altloc"] == ""


def test_missing_cif_model_column_never_fabricates_source_model_one():
    parsed = parse_structure(cif_text(omitted={"pdbx_PDB_model_num"}), "mmcif")
    assert parsed["models"] == [None]
    assert parsed["atoms"][0]["model"] is None


def test_mixed_unknown_and_known_model_identity_stays_deterministic_without_relabeling():
    lines = cif_text(count=2).splitlines()
    first_row = lines[-2].split()
    first_row[-2] = "?"
    lines[-2] = " ".join(first_row)
    parsed = parse_structure("\n".join(lines) + "\n", "mmcif")
    assert parsed["models"] == [1, None]
    assert [a["model"] for a in parsed["atoms"]] == [None, 1]


def test_unknown_cif_segment_is_not_known_blank_segment():
    unknown = parse_structure(cif_text({"pdbx_PDB_segment_id": "?"}), "mmcif")["atoms"][0]
    blank = parse_structure(cif_text({"pdbx_PDB_segment_id": "."}), "mmcif")["atoms"][0]
    assert unknown["segment"] is None and blank["segment"] == ""


@pytest.mark.parametrize("number", ["0", "-3"])
def test_author_numbers_zero_or_negative_are_source_numbers_not_missing(number):
    parsed = parse_structure(cif_text({"auth_seq_id": number, "label_seq_id": "?", "occupancy": "0", "B_iso_or_equiv": "0"}), "mmcif")
    atom = parsed["atoms"][0]
    assert atom["auth_number"] == int(number) and atom["label_number"] is None
    assert atom["occupancy"] == atom["b_value"] == 0


@pytest.mark.parametrize("microheterogeneity", [False, True])
def test_alternates_and_residue_name_variants_at_one_locus_cannot_map_to_two_sequence_positions(tmp_path, microheterogeneity):
    bundle = one_structure_bundle()
    molecule, structure, mapping = [first(bundle, kind) for kind in ("molecule", "structure", "structure_map")]
    selected = next(e for e in mapping["residues"] if e["chain_id"] == "H" and e["altloc"] == "A")
    extra = copy.deepcopy(selected)
    extra["sequence_index"] = 6
    extra["altloc"] = "B"
    molecule["chains"][0]["sequence"] = "ACDEFY" if microheterogeneity else "ACDEFF"
    mapping["residues"] = [e for e in mapping["residues"] if (e["chain_id"], e["sequence_index"]) != ("H", 6)] + [extra]
    if microheterogeneity:
        lines = []
        for line in structure["content"].splitlines():
            if line.startswith("ATOM") and line[16] == "B" and line[17:20] == "PHE":
                line = line[:17] + "TYR" + line[20:]
            lines.append(line)
        structure["content"] = "\n".join(lines) + "\n"
        structure["sha256"] = hashlib.sha256(structure["content"].encode()).hexdigest()
        extra["structure_residue"]["residue_name"] = "TYR"
    store = Store(tmp_path / "locus.sqlite3")
    with pytest.raises(ValidationError, match="locus"):
        store.import_bundle(bundle)
    assert store.projects() == []


@pytest.mark.parametrize("scope", [None, {"structure_model": 1}])
def test_model_score_scope_is_preserved_and_missing_confidence_stays_missing(tmp_path, scope):
    bundle = one_structure_bundle()
    structure = first(bundle, "structure")
    evidence = first(bundle, "evidence")
    evidence["conditions"] = scope
    evidence["value"] = None
    bundle["entities"] = [e for e in bundle["entities"] if e["type"] != "evidence" or e is evidence]
    store = Store(tmp_path / "scope.sqlite3")
    store.import_bundle(bundle)
    observed = structure_observation(store.bundle(bundle["project"]["id"]), structure["id"])
    assert len(observed["confidence"]) == 1
    assert observed["confidence"][0]["conditions"] == scope and observed["confidence"][0]["value"] is None


def test_measured_structure_subject_is_rejected_independently_of_metric_name(tmp_path):
    bundle = one_structure_bundle()
    evidence = first(bundle, "evidence")
    evidence.update(kind="measured", metric="Binding measurement fixture", unit="nM")
    store = Store(tmp_path / "measured.sqlite3")
    with pytest.raises(ValidationError, match="Material"):
        store.import_bundle(bundle)
    assert store.projects() == []


def test_exact_same_sequence_cross_project_primary_structure_reference_is_rejected(tmp_path):
    original, incoming = one_structure_bundle(), one_structure_bundle()
    ids = {e["id"]: new_id(e["type"]) for e in incoming["entities"]}
    ids[incoming["project"]["id"]] = new_id("project")
    def rewrite(value):
        if isinstance(value, str): return ids.get(value, value)
        if isinstance(value, list): return [rewrite(v) for v in value]
        if isinstance(value, dict): return {k: rewrite(v) for k, v in value.items()}
        return value
    incoming = rewrite(incoming)
    first(incoming, "structure")["molecule_id"] = first(original, "molecule")["id"]
    store = Store(tmp_path / "cross-project.sqlite3")
    store.import_bundle(original)
    with pytest.raises(ValidationError):
        store.import_bundle(incoming)
    assert store.projects() == [original["project"]]
    assert store.bundle(original["project"]["id"]) == original


def test_exact_atom_count_boundary_and_one_extra_are_not_silently_truncated():
    accepted = parse_structure(cif_text(count=100000), "mmcif")
    assert len(accepted["atoms"]) == len(accepted["residues"]) == 100000
    with pytest.raises(ValidationError, match="100,000"):
        parse_structure(cif_text(count=100001), "mmcif")


def test_reused_pdb_chain_residue_after_ter_cannot_merge_distinct_chain_parts():
    template = next(line for line in first(structure_bundle(), "structure")["content"].splitlines() if line.startswith("ATOM"))
    first_atom = template[:6] + f"{1:5d}" + template[11:12] + " N  " + template[16:]
    second_atom = template[:6] + f"{2:5d}" + template[11:]
    content = first_atom + "\nTER\n" + second_atom + "\nEND\n"
    with pytest.raises(ValidationError):
        parse_structure(content, "pdb")


def test_nonpolymer_after_ter_with_distinct_source_residue_is_still_viewable():
    template = next(line for line in first(structure_bundle(), "structure")["content"].splitlines() if line.startswith("ATOM"))
    water = "HETATM" + f"{2:5d}" + template[11:12] + " O  " + template[16:17] + "HOH" + template[20:22] + f"{2000:4d}" + template[26:]
    parsed = parse_structure(template + "\nTER\n" + water + "\nEND\n", "pdb")
    assert len(parsed["atoms"]) == len(parsed["residues"]) == 2
    assert parsed["residues"][1]["auth_number"] == 2000
    assert parsed["residues"][1]["aa"] is None
