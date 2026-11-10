"""Independent source-order probes. Synthetic fixtures, temporary databases only.

P03/P04/P08, J03/J04/J08, AC-J03/AC-J04/AC-J08.
Run from repo root with venv Python; --output names a new evidence file.
No production data, previous evidence or implementation is modified.
"""
import argparse
import copy
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from workspace_app.domain import ValidationError, validate_graph
from workspace_app.storage import Store
from workspace_app.hypotheses import hypothesis_preview
from workspace_app.structure_fixtures import structure_bundle
from workspace_app.structures import CHAIN_FIELDS, RESIDUE_FIELDS, parse_structure, structure_observation


def pdb(rows):
    lines = []
    serial = 0
    for row in rows:
        if row == "TER":
            lines.append("TER")
            continue
        serial += 1
        number, insertion = row
        lines.append(f"ATOM  {serial:5d}  CA  ALA H{number:4d}{insertion or ' '}   {serial * 3.:8.3f}{0.:8.3f}{0.:8.3f}{1.:6.2f}{10.:6.2f}           C  ")
    return "\n".join(lines) + "\nEND\n"


def cif(rows):
    tags = "group_PDB id type_symbol label_atom_id label_alt_id label_comp_id label_asym_id label_seq_id pdbx_PDB_ins_code Cartn_x Cartn_y Cartn_z occupancy B_iso_or_equiv auth_seq_id auth_comp_id auth_asym_id pdbx_PDB_model_num".split()
    lines = ["data_independent", "loop_", *("_atom_site." + tag for tag in tags)]
    for serial, (label, author, insertion) in enumerate(rows, 1):
        lines.append(f"ATOM {serial} C CA . ALA VH {label if label is not None else '?'} {insertion or '.'} {serial * 3.} 0 0 1 10 {author} ALA H 1")
    return "\n".join(lines) + "\n"


def bundle(content, file_format="pdb", indexes=None):
    original = structure_bundle()
    molecule, structure, mapping = (copy.deepcopy(next(e for e in original["entities"] if e["type"] == kind))
                                    for kind in ("molecule", "structure", "structure_map"))
    parsed = parse_structure(content, file_format)
    molecule["chains"] = [{"id": "H", "role": "declared synthetic antibody fragment", "sequence": "A" * (max(indexes) if indexes else len(parsed["residues"]))}]
    structure.update(content=content, file_format=file_format, sha256=hashlib.sha256(content.encode()).hexdigest())
    mapping["chain_assignments"] = [{**{key: chain[key] for key in CHAIN_FIELDS}, "role": "antibody", "molecule_chain_id": "H", "target_ref": None, "label": "Independent synthetic H"} for chain in parsed["chains"]]
    mapping["residues"] = [{"chain_id": "H", "sequence_index": indexes[i] if indexes else i + 1, "status": "mapped", "structure_residue": {key: residue[key] for key in RESIDUE_FIELDS}, "altloc": "", "reason": None} for i, residue in enumerate(parsed["residues"])]
    return {"schema_version": original["schema_version"], "project": original["project"], "entities": [molecule, structure, mapping]}


def pick(b, kind):
    return next(e for e in b["entities"] if e["type"] == kind)


def reject(b):
    try:
        validate_graph(b["project"], b["entities"])
    except ValidationError:
        pass
    else:
        raise AssertionError("Graph validation accepted a contradictory map")
    with tempfile.TemporaryDirectory(prefix="antibody-independent-map-") as directory:
        store = Store(Path(directory) / "reject.sqlite3")
        try:
            store.import_bundle(b)
        except ValidationError:
            assert store.projects() == [], "Failed import wrote part of the project"
        else:
            raise AssertionError("Atomic import accepted a contradictory map")


def assert_no_mapped(view):
    assert view["map"] is None or not any(e["status"] == "mapped" for e in view["map"]["residues"]), "Unverified/contradictory map remains available for coordinate highlighting"


def safe_unknown(b):
    with tempfile.TemporaryDirectory(prefix="antibody-independent-unknown-") as directory:
        store = Store(Path(directory) / "unknown.sqlite3")
        try:
            store.import_bundle(b)
        except ValidationError:
            # A conservative rejection also prevents an unknown order from being used.
            assert store.projects() == []
        else:
            restored = store.bundle(b["project"]["id"])
            assert_no_mapped(structure_observation(restored, pick(b, "structure")["id"], pick(b, "structure_map")["id"]))


def verify_correct(b):
    validate_graph(b["project"], b["entities"])
    with tempfile.TemporaryDirectory(prefix="antibody-independent-correct-") as directory:
        store = Store(Path(directory) / "correct.sqlite3")
        store.import_bundle(b)
        restored = store.bundle(b["project"]["id"])
        assert restored == b
        view = structure_observation(restored, pick(b, "structure")["id"], pick(b, "structure_map")["id"])
        assert view["map"] is not None and all(e["status"] == "mapped" for e in view["map"]["residues"])


def legacy_view_and_continuation():
    b = bundle(pdb([(1, ""), (2, "")]), indexes=[2, 1])
    original = copy.deepcopy(b)
    assert_no_mapped(structure_observation(b, pick(b, "structure")["id"], pick(b, "structure_map")["id"]))
    assert b == original, "Read-time quarantine mutated source records"
    with tempfile.TemporaryDirectory(prefix="antibody-independent-legacy-") as directory:
        store = Store(Path(directory) / "legacy.sqlite3")
        # Recreate only the storage state produced by the old accepted implementation.
        with closing(store.connect()) as db, db:
            db.execute("INSERT INTO projects VALUES (?,?)", (b["project"]["id"], json.dumps(b["project"])))
            for entity in b["entities"]:
                store._insert(db, entity)
        decision = store.save_shortlist(b["project"]["id"], [pick(b, "molecule")["id"]], [], "Retain source-only observation; repair the unverified mapping before using residue correspondence.")
        assert decision["type"] == "decision"
        assert store.bundle(b["project"]["id"])["entities"][:3] == original["entities"]


def mapped_hypothesis_guard():
    for b in (bundle(pdb([(1, ""), (2, "")]), indexes=[2, 1]), bundle(cif([(None, 101, "")]), "mmcif")):
        definition = {"text": "Independent mapping question", "question": "Repair the correspondence before evaluating this residue.",
                      "limitations": "Synthetic engineering observation only.", "molecule_ids": [pick(b, "molecule")["id"]],
                      "related_evidence_ids": [], "lineage_ids": [], "residue_refs": [],
                      "structure_refs": [{"structure_id": pick(b, "structure")["id"], "model": 1, "structure_map_id": pick(b, "structure_map")["id"]}]}
        before = copy.deepcopy(b)
        try:
            hypothesis_preview(b, definition)
        except ValidationError:
            pass
        else:
            raise AssertionError("A new hypothesis accepted a quarantined correspondence")
        assert b == before
        definition["structure_refs"][0]["structure_map_id"] = None
        record = hypothesis_preview(b, definition)["entities"][0]
        assert record["structure_refs"][0]["structure_map_id"] is None


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    cases = [
        ("PDB repeated identical residues reverse order rejected in graph and atomic import", lambda: reject(bundle(pdb([(1, ""), (2, "")]), indexes=[2, 1]))),
        ("CIF repeated identical residues reverse label order rejected", lambda: reject(bundle(cif([(1, 101, ""), (2, 102, "")]), "mmcif", [2, 1]))),
        ("Correct PDB source order accepts missing raw index and author insertion", lambda: verify_correct(bundle(pdb([(10, ""), (10, "A"), (15, "")]), indexes=[1, 3, 4]))),
        ("Correct PDB order never sorts descending author numbers", lambda: verify_correct(bundle(pdb([(12, ""), (7, ""), (-3, "")])))),
        ("CIF shuffled atom rows and descending author numbers use polymer label order", lambda: verify_correct(bundle(cif([(3, -3, ""), (1, 101, ""), (2, 60, "A")]), "mmcif", [3, 1, 2]))),
        ("CIF missing single-residue label has no verified sequence highlight", lambda: safe_unknown(bundle(cif([(None, 101, "")]), "mmcif"))),
        ("CIF duplicated polymer label under distinct author loci remains unverified", lambda: safe_unknown(bundle(cif([(1, 101, ""), (1, 102, "")]), "mmcif"))),
        ("PDB same source chain across TER cannot establish cross-part order", lambda: safe_unknown(bundle(pdb([(1, ""), "TER", (2, "")])))),
        ("Legacy contradictory map source-only; unrelated shortlist still saves; source immutable", legacy_view_and_continuation),
        ("New hypothesis cannot assert a quarantined map; explicit source-only context allowed", mapped_hypothesis_guard),
    ]
    results = []
    for name, action in cases:
        try:
            action()
        except Exception as exc:
            results.append({"name": name, "status": "FAIL", "error": str(exc), "traceback": traceback.format_exc()})
        else:
            results.append({"name": name, "status": "PASS"})
    root = Path(__file__).resolve().parents[1]
    sources = {str(path.relative_to(root)).replace("\\", "/"): hashlib.sha256(path.read_bytes()).hexdigest() for path in [root / "workspace_app" / name for name in ("structures.py", "domain.py", "storage.py", "hypotheses.py", "server.py")]}
    result = {"reviewer": "/root/mapping_review", "scope": "P0 source-order domain and read-time quarantine; synthetic engineering evidence only", "sources_at_completion": sources, "results": results, "status": "PASS" if all(r["status"] == "PASS" for r in results) else "FAIL"}
    target = Path(args.output)
    assert not target.exists(), "Do not overwrite prior independent evidence"
    target.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"status": result["status"], "passed": sum(r["status"] == "PASS" for r in results), "total": len(results), "output": str(target)}))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(run())
