"""Native ANARCI output, explicit provenance and compatibility with existing map gates."""

import copy
from pathlib import Path

import pytest

from public_structure_fixture import public_structure_bundle
from workspace_app.design import design_context
from workspace_app.domain import ValidationError, new_id
from workspace_app.numbering_import import anarci_preview, source_digest
from workspace_app.storage import Store

NATIVE = Path(__file__).resolve().parents[1] / "fixtures/public/1MLC-AB.anarci.txt"
SHA256 = "26c2c44b388d7f62dd9efdf992a1c69f366f07cc0db1b43001e32c175c3e0747"
UNVERIFIED = {"status": "unverified", "reference": None, "reviewer": None, "reviewed_at": None}


def input_case():
    project = public_structure_bundle()
    molecule = project["entities"][0]
    project["entities"] = [molecule]
    content = NATIVE.read_bytes().decode("utf-8")
    bindings = [{"record_index": i, "domain_index": 1, "molecule_id": molecule["id"],
                 "chain_id": chain["id"], "verification": copy.deepcopy(UNVERIFIED)}
                for i, chain in enumerate(molecule["chains"])]
    return project, content, bindings


def test_native_public_output_retains_original_file_and_eligibility(tmp_path):
    project, content, bindings = input_case()
    assert source_digest(content) == SHA256
    store = Store(tmp_path / "original.sqlite3")
    store.import_bundle(project)
    before = store.bundle(project["project"]["id"])
    read = anarci_preview(before, content, NATIVE.name, "2026.2.13.2", [], None)
    assert read["bundle"]["entities"] == []
    assert [(r["source_chain_type"], r["sequence_end"]) for r in read["report"]["numbering_domains"]] == [("K", 107), ("H", 116)]
    preview = anarci_preview(before, content, NATIVE.name, "2026.2.13.2", bindings, SHA256)
    assert store.bundle(project["project"]["id"]) == before
    file, light, heavy = preview["bundle"]["entities"]
    assert file["content"] == content and file["sha256"] == SHA256
    assert (light["chain_id"], light["chain_type"], light["sequence_start"], light["sequence_end"]) == ("A", "light", 1, 107)
    assert (heavy["chain_id"], heavy["chain_type"], heavy["sequence_start"], heavy["sequence_end"]) == ("B", "heavy", 1, 116)
    store.import_bundle(preview["bundle"])
    saved = Store(store.path).bundle(project["project"]["id"])
    with pytest.raises(ValidationError, match="unverified"):
        design_context(saved, heavy["molecule_id"], heavy["id"])
    fresh = Store(tmp_path / "fresh.sqlite3")
    fresh.import_bundle(saved)
    assert fresh.bundle(project["project"]["id"]) == saved


@pytest.mark.parametrize("case", ["wrong_scheme", "wrong_chain", "bad_interval", "stale", "failed_domain",
                                  "duplicate_domain", "boolean_index", "fixture_attestation"])
def test_native_binding_rejects_inconsistent_or_unavailable_sources(case):
    project, content, bindings = input_case()
    digest = SHA256
    if case == "wrong_scheme":
        content = content.replace("# Scheme = imgt", "# Scheme = kabat", 1)
    elif case == "wrong_chain":
        bindings[0]["chain_id"] = "B"
    elif case == "bad_interval":
        content = content.replace("|0|106|", "|1|106|", 1)
    elif case == "stale":
        content += "\n"
    elif case == "failed_domain":
        content = "# no significant hit\n//\n" + content
    elif case == "duplicate_domain":
        bindings.append(copy.deepcopy(bindings[0]))
    elif case == "boolean_index":
        bindings[0]["record_index"] = False
    else:
        bindings[0]["verification"]["status"] = "engineering_fixture"
    if case != "stale":
        digest = source_digest(content)
    with pytest.raises(ValidationError):
        anarci_preview(project, content, NATIVE.name, "2026.2.13.2", bindings, digest)


@pytest.mark.parametrize("case", ["digest", "origin", "coordinate", "rebind_equal_sequence", "verification"])
def test_reimport_checks_source_binding_and_attestation(tmp_path, case):
    project, content, bindings = input_case()
    preview = anarci_preview(project, content, NATIVE.name, "2026.2.13.2", bindings, SHA256)
    file, light, _ = preview["bundle"]["entities"]
    if case == "digest":
        file["content"] += "\n"
    elif case == "origin":
        del light["numbering_origin"]
    elif case == "coordinate":
        light["entries"].pop()
        light["sequence_end"] -= 1
    elif case == "rebind_equal_sequence":
        duplicate = copy.deepcopy(project["entities"][0])
        duplicate.update(id=new_id("molecule"), external_id="another Fab")
        project["entities"].append(duplicate)
        light["molecule_id"] = duplicate["id"]
    else:
        light["verification"] = {"status": "source_verified", "reference": "Synthetic tampering test",
                                 "reviewer": "Fixture", "reviewed_at": light["created_at"]}
    store = Store(tmp_path / "reject.sqlite3")
    store.import_bundle(project)
    with pytest.raises(ValidationError):
        store.import_bundle(preview["bundle"])
    assert store.bundle(project["project"]["id"]) == project


def test_native_imgt_extensions_keep_both_sides_and_nonzero_raw_start():
    project, _, bindings = input_case()
    molecule = project["entities"][0]
    molecule["chains"][1]["sequence"] = "MMACDEFGQ"
    content = ("# synthetic extension\n# ANARCI numbered\n# Domain 1 of 1\n# Most significant HMM hit\n"
               "#|species|chain_type|e-value|score|seqstart_index|seqend_index|\n#|test|H|1|1|2|7|\n"
               "# Scheme = imgt\nH 110 -\nH 111 A\nH 111 A C\nH 111 B D\n"
               "H 112 B E\nH 112 A F\nH 112 G\n//\n")
    bindings[1]["record_index"] = 0
    result = anarci_preview(project, content, "synthetic.txt", None, [bindings[1]], source_digest(content))
    record = result["bundle"]["entities"][1]
    assert [(e["sequence_index"], e["number"], e["ins_code"], e["aa"]) for e in record["entries"]] == [
        (3, 111, "", "A"), (4, 111, ".1", "C"), (5, 111, ".2", "D"),
        (6, 112, ".2", "E"), (7, 112, ".1", "F"), (8, 112, "", "G")]
    wrong_order = content.replace("H 112 B E\nH 112 A F", "H 112 A E\nH 112 B F")
    with pytest.raises(ValidationError, match="coordinate order"):
        anarci_preview(project, wrong_order, "synthetic.txt", None, [bindings[1]], source_digest(wrong_order))
