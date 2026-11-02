"""F08 source identifiers, atomic import and explicit structural correspondence."""

import copy
import hashlib

import pytest

from workspace_app.domain import ValidationError, new_id
from workspace_app.structure_fixtures import structure_bundle
from workspace_app.structures import parse_structure, structure_observation
from workspace_app.storage import Store


def pick(bundle, kind): return next(e for e in bundle["entities"] if e["type"] == kind)


def test_source_models_author_label_insertion_altloc_and_exact_roundtrip(tmp_path):
    b = structure_bundle(); store = Store(tmp_path / "one.sqlite3"); store.import_bundle(b)
    restored = Store(store.path).bundle(b["project"]["id"]); assert restored == b
    second = Store(tmp_path / "two.sqlite3"); second.import_bundle(restored); assert second.bundle(b["project"]["id"]) == b
    structures = [e for e in b["entities"] if e["type"] == "structure"]
    pdb, cif = [parse_structure(e["content"], e["file_format"]) for e in structures]
    assert pdb["models"] == cif["models"] == [1,2]
    assert len(pdb["atoms"]) == len(cif["atoms"]) == 22
    assert pdb["residues"][2]["insertion_code"] == "A"
    assert cif["residues"][0]["auth_number"] == 101 and cif["residues"][0]["label_number"] == 1
    assert cif["residues"][0]["auth_chain"] == "H-author" and cif["residues"][0]["label_asym"] == "VH"
    assert all(a["occupancy"] is None and a["b_value"] is None for a in cif["atoms"])
    assert pdb["residues"][3]["altlocs"] == ["A", "B"]
    view = structure_observation(b, structures[0]["id"])
    assert view["map"] is None and len(view["map_options"]) == 2
    assert len(view["confidence"]) == 2 and {e["conditions"]["structure_model"] for e in view["confidence"]} == {1,2}
    assert structure_observation(b, structures[1]["id"])["confidence"] == []


@pytest.mark.parametrize("case", ["digest", "corrupt", "nan", "unknown_molecule", "wrong_structure", "wrong_chain", "wrong_model", "wrong_insertion", "wrong_label",
                                  "wrong_aa", "no_conformer", "wrong_conformer", "duplicate_position", "duplicate_residue", "bad_role", "missing_target", "unknown_chain_assignment",
                                  "bool_index", "bool_model", "unknown_model_score", "wrong_metric_kind", "wrong_metric_unit", "metric_range"])
def test_invalid_structure_or_mapping_rejects_everything(tmp_path, case):
    b = structure_bundle(); structure = pick(b,"structure"); mapping = pick(b,"structure_map"); entry = mapping["residues"][0]
    if case == "digest": structure["sha256"] = "0" * 64
    elif case in ("corrupt", "nan"):
        structure["content"] = "ATOM broken" if case == "corrupt" else structure["content"].replace("   0.000", "     nan", 1)
        structure["sha256"] = hashlib.sha256(structure["content"].encode()).hexdigest()
    elif case == "unknown_molecule": structure["molecule_id"] = new_id("molecule")
    elif case == "wrong_structure": mapping["structure_id"] = new_id("structure")
    elif case == "wrong_chain": entry["structure_residue"]["auth_chain"] = "L"
    elif case == "wrong_model": entry["structure_residue"]["model"] = 3
    elif case == "wrong_insertion": entry["structure_residue"]["insertion_code"] = "A"
    elif case == "wrong_label": entry["structure_residue"]["label_number"] = 1
    elif case == "wrong_aa": pick(b,"molecule")["chains"][0]["sequence"] = "CCDEFG"
    elif case in ("no_conformer", "wrong_conformer"):
        alternate = next(e for e in mapping["residues"] if e["altloc"] == "A"); alternate["altloc"] = "" if case == "no_conformer" else "C"
    elif case == "duplicate_position": mapping["residues"].append(copy.deepcopy(entry))
    elif case == "duplicate_residue":
        extra = copy.deepcopy(entry); extra["sequence_index"] = 3; pick(b,"molecule")["chains"][0]["sequence"] = "ACAEFG"
        mapping["residues"] = [e for e in mapping["residues"] if e["sequence_index"] != 3 or e["chain_id"] != "H"] + [extra]
    elif case == "bad_role": mapping["chain_assignments"][0]["role"] = "inferred"
    elif case == "missing_target": next(a for a in mapping["chain_assignments"] if a["role"] == "antigen")["target_ref"] = None
    elif case == "unknown_chain_assignment": mapping["chain_assignments"][0]["segment"] = "absent"
    elif case == "bool_index": entry["sequence_index"] = True
    elif case == "bool_model": entry["structure_residue"]["model"] = True
    else:
        evidence = pick(b,"evidence")
        if case == "unknown_model_score": evidence["conditions"]["structure_model"] = 99
        elif case == "wrong_metric_kind": evidence["kind"] = "measured"
        elif case == "wrong_metric_unit": evidence["unit"] = "nM"
        elif case == "metric_range": evidence["value"] = 1.1
    store = Store(tmp_path / "reject.sqlite3")
    with pytest.raises(ValidationError): store.import_bundle(b)
    assert store.projects() == []


def test_missing_pdb_occupancy_b_are_unknown_and_unavailable_mapping_never_falls_back(tmp_path):
    b=structure_bundle(); structure=pick(b,"structure")
    content="\n".join(line[:54] if line.startswith("ATOM") else line for line in structure["content"].splitlines())+"\n"
    parsed=parse_structure(content,"pdb")
    assert all(a["occupancy"] is None and a["b_value"] is None for a in parsed["atoms"])
    store=Store(tmp_path/"test.sqlite3");store.import_bundle(b)
    mapping=pick(b,"structure_map"); unavailable=next(e for e in mapping["residues"] if e["chain_id"]=="H" and e["sequence_index"]==3)
    assert unavailable["status"]=="unavailable" and unavailable["structure_residue"] is None
    assert any(e["status"]=="mapped" and e["structure_residue"]["auth_number"]==3 and e["sequence_index"]==4 for e in mapping["residues"])
