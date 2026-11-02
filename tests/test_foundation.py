"""Initial M1 invariant tests, not the final eight journey acceptance suite."""

import copy
import json
import sqlite3
import threading
import urllib.error
import urllib.request
from http.cookiejar import CookieJar

import pytest

from workspace_app.adapters import new_project, parse_json, preview
from workspace_app.domain import ValidationError, new_id, validate_graph
from workspace_app.fixtures import example_bundle
from workspace_app.server import make_server
from workspace_app.storage import Store


@pytest.fixture
def store(tmp_path):
    return Store(tmp_path / "workspace.sqlite3")


def test_roundtrip_and_restart_retains_identity_and_provenance(store, tmp_path):
    original = example_bundle(8)
    store.import_bundle(original)
    restored = Store(store.path).bundle(original["project"]["id"])
    assert restored == original
    fresh = Store(tmp_path / "fresh.sqlite3")
    fresh.import_bundle(json.loads(json.dumps(restored)))
    assert fresh.bundle(original["project"]["id"]) == original
    entities = restored["entities"]
    molecules = [e for e in entities if e["type"] == "molecule"]
    assert molecules[0]["chains"] == molecules[1]["chains"]
    assert molecules[0]["id"] != molecules[1]["id"]
    constructs = [e for e in entities if e["type"] == "construct" and e["molecule_id"] == molecules[0]["id"]]
    assert len(constructs) == 2 and constructs[0]["cds"] != constructs[1]["cds"]
    measured = [e for e in entities if e["type"] == "evidence" and e["kind"] == "measured"]
    assert measured[0]["value"] == 0 and measured[1]["value"] is None
    assert measured[2]["conditions"] is None


def test_800_fasta_records_are_counted_without_identity_collapse(store):
    raw = "\n".join(f">C{i}\nEVQLVESGGGACD" for i in range(800))
    result = preview(raw, "fasta", "synthetic-800.fasta", new_project("Synthetic 800", "Engineering fixture"))
    assert result["report"]["total_rows"] == result["report"]["valid_rows"] == 800
    assert len(result["report"]["duplicates"]) == 799
    assert store.projects() == []  # preview does not save
    store.import_bundle(result["bundle"])
    assert len(store.bundle(result["bundle"]["project"]["id"])["entities"]) == 800


def test_invalid_sequence_rows_are_explicitly_excluded_before_commit(store):
    raw = ">ok\nEVQL\n>missing\n>invalid\nABC*\n>ok\nEVQL\n>ambiguous\nEVQX"
    result = preview(raw, "fasta", "fixture.fa", new_project("Fixture", "QC"))
    report = result["report"]
    assert report["total_rows"] == 5 and report["valid_rows"] == 2
    assert [r["reason"] for r in report["excluded"]] == ["Missing sequence", "Invalid amino-acid symbols", "Duplicate external ID in input"]
    assert len(report["warnings"]) == 1
    assert store.projects() == []
    store.import_bundle(result["bundle"])
    assert len(store.bundle(result["bundle"]["project"]["id"])["entities"]) == 2


@pytest.mark.parametrize("raw", ["EVQL", "", ">\nEVQL"])
def test_fasta_missing_header_or_records(raw):
    if raw.startswith(">"):
        assert preview(raw, "fasta", "test.fa", new_project("Test", "Test"))["report"]["valid_rows"] == 0
    else:
        with pytest.raises(ValidationError):
            preview(raw, "fasta", "test.fa", new_project("Test", "Test"))


def test_sequence_csv_contract_does_not_infer_pairing():
    raw = "external_id,name,sequence,chain_role,format\nA,Alpha,EVQL,VH,Fab\nB,Beta,DIQM,VL,Fab\n"
    result = preview(raw, "csv", "test.csv", new_project("Test", "Test"))
    assert len(result["bundle"]["entities"]) == 2
    assert result["bundle"]["entities"][0]["chains"][0]["role"] == "VH"
    assert result["bundle"]["entities"][1]["chains"][0]["role"] == "VL"


@pytest.mark.parametrize("raw", ["external_id,name,sequence,mystery\nA,A,EVQL,1", "external_id,name,name\nA,A,B", "external_id,name,sequence\nA,A,EVQL,extra", "name,sequence\nA,EVQL"])
def test_csv_unsupported_or_malformed_fields_reject(raw):
    with pytest.raises(ValidationError):
        preview(raw, "csv", "test.csv", new_project("Test", "Test"))


def test_late_collision_rolls_back_new_entities_and_project(store):
    original = example_bundle()
    store.import_bundle(original)
    candidate = example_bundle(9)
    candidate["entities"][-1]["id"] = next(e["id"] for e in original["entities"] if e["type"] == candidate["entities"][-1]["type"])
    with pytest.raises(ValidationError, match="collision"):
        store.import_bundle(candidate)
    assert store.projects() == [original["project"]]
    assert store.bundle(original["project"]["id"]) == original


def test_stale_preview_and_external_id_collision_are_atomic(store):
    original = example_bundle()
    store.import_bundle(original)
    project = original["project"]
    pending = preview(">NEW\nEVQL", "fasta", "new.fa", project)["bundle"]
    store.import_bundle(pending)
    before = store.bundle(project["id"])
    with pytest.raises(ValidationError):
        store.import_bundle(pending)
    assert store.bundle(project["id"]) == before
    another = preview(">FIX-001\nACDE", "fasta", "collision.fa", project)["bundle"]
    with pytest.raises(ValidationError, match="External ID collision"):
        store.import_bundle(another)
    assert store.bundle(project["id"]) == before


def test_same_project_append_rejects_project_metadata_change(store):
    original = example_bundle()
    store.import_bundle(original)
    modified = {"schema_version": original["schema_version"], "project": dict(original["project"], title="changed"), "entities": []}
    with pytest.raises(ValidationError, match="Project ID collision"):
        store.import_bundle(modified)


@pytest.mark.parametrize("target_kind", ["construct", "molecule", "unknown", "other_project"])
def test_measured_requires_correct_project_material(store, target_kind):
    original = example_bundle()
    store.import_bundle(original)
    second = example_bundle(9)
    if target_kind == "other_project":
        store.import_bundle(second)
    e = copy.deepcopy(next(x for x in original["entities"] if x["type"] == "evidence" and x["kind"] == "measured"))
    e["id"] = new_id("evidence")
    e["subject_id"] = (new_id("material") if target_kind == "unknown" else
                        next(x["id"] for x in (second if target_kind == "other_project" else original)["entities"]
                             if x["type"] == ("material" if target_kind == "other_project" else target_kind)))
    with pytest.raises(ValidationError):
        store.import_bundle({**original, "entities": [e]})
    assert store.bundle(original["project"]["id"]) == original


@pytest.mark.parametrize("key,value", [("value", True), ("value", "0"), ("value", float("nan")), ("value", float("inf")),
                                        ("conditions", "unknown"), ("unit", None), ("timestamp", "2026-11-02"),
                                        ("source", {"name": "", "version": None}), ("kind", "prediction")])
def test_invalid_evidence_never_saves(store, key, value):
    b = example_bundle()
    e = next(x for x in b["entities"] if x["type"] == "evidence" and x["value"] is not None)
    e[key] = value
    with pytest.raises(ValidationError):
        store.import_bundle(b)
    assert store.projects() == []


def test_unknown_fields_and_bad_entity_shapes_report_errors(store):
    b = example_bundle()
    b["entities"][0]["chains"][0]["imaginary_numbering"] = 1
    with pytest.raises(ValidationError) as error:
        store.import_bundle(b)
    assert "chain.imaginary_numbering" in error.value.details
    b = example_bundle()
    b["entities"][0]["chains"] = []
    with pytest.raises(ValidationError):
        store.import_bundle(b)


def test_five_candidate_draft_snapshot_is_persistent_and_immutable(store):
    b = example_bundle()
    store.import_bundle(b)
    candidates = [e["id"] for e in b["entities"] if e["type"] == "molecule"][:5]
    evidence = [e["id"] for e in b["entities"] if e["type"] == "evidence"][:2]
    d = store.save_shortlist(b["project"]["id"], candidates, evidence, "Compare specificity before selecting the next experiment.")
    assert d["status"] == "draft" and d["candidate_ids"] == candidates
    saved = Store(store.path).bundle(b["project"]["id"])
    assert saved["entities"][-1] == d
    with sqlite3.connect(store.path) as db:
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            db.execute("UPDATE entities SET payload='{}' WHERE id=?", (d["id"],))
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            db.execute("DELETE FROM entities WHERE id=?", (d["id"],))
    late = copy.deepcopy(next(e for e in b["entities"] if e["type"] == "evidence"))
    late["id"] = new_id("evidence"); late["value"] = 99
    store.import_bundle({**b, "entities": [late]})
    assert store.bundle(b["project"]["id"])["entities"][-2] == d


@pytest.mark.parametrize("case", ["empty_reason", "missing_candidate", "wrong_evidence", "duplicate_candidate", "duplicate_evidence"])
def test_invalid_shortlist_is_rejected_without_side_effects(store, case):
    b = example_bundle(); store.import_bundle(b)
    candidates = [e["id"] for e in b["entities"] if e["type"] == "molecule"][:1]
    evidence = [e["id"] for e in b["entities"] if e["type"] == "evidence"][:1]
    reason = "Next question"
    if case == "empty_reason": reason = " "
    elif case == "missing_candidate": candidates = [new_id("molecule")]
    elif case == "wrong_evidence": evidence = [e["id"] for e in b["entities"] if e["type"] == "evidence"][-1:]
    elif case == "duplicate_candidate": candidates *= 2
    elif case == "duplicate_evidence": evidence *= 2
    with pytest.raises(ValidationError):
        store.save_shortlist(b["project"]["id"], candidates, evidence, reason)
    assert store.bundle(b["project"]["id"]) == b


def test_tampered_snapshot_rejected(store):
    b = example_bundle(); store.import_bundle(b)
    candidate = next(e["id"] for e in b["entities"] if e["type"] == "molecule")
    ev = next(e["id"] for e in b["entities"] if e["type"] == "evidence")
    draft = store.save_shortlist(b["project"]["id"], [candidate], [ev], "Test")
    draft["id"] = new_id("decision"); draft["evidence_snapshot"][0]["value"] = 100
    with pytest.raises(ValidationError, match="snapshot differs"):
        store.import_bundle({**b, "entities": [draft]})


@pytest.mark.parametrize("raw", ['{"a":NaN}', '{"a":Infinity}', '{"a":1e999}', '{"a":1e-999}', '{"a":1,"a":2}', '{broken'])
def test_invalid_json_rejected(raw):
    with pytest.raises(ValidationError): parse_json(raw)


def test_corrupt_structure_rejected_without_changing_database(store):
    b = example_bundle(); store.import_bundle(b)
    with pytest.raises(ValidationError, match="Unsupported file format"):
        preview("ATOM broken", "pdb", "corrupt.pdb", b["project"])
    assert store.bundle(b["project"]["id"]) == b


@pytest.fixture
def http_server(tmp_path):
    server = make_server(tmp_path / "http.sqlite3", 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    yield server
    server.shutdown(); thread.join(timeout=5); server.server_close()


def test_api_security_and_roundtrip(http_server):
    origin = http_server.origin
    jar = CookieJar(); browser = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    def request(path, data=None, headers=None, client=browser):
        return client.open(urllib.request.Request(origin + path, data=data, headers=headers or {}), timeout=5)
    with pytest.raises(urllib.error.HTTPError) as error: request("/api/bootstrap")
    assert error.value.code == 401
    response = request("/")
    assert "script-src 'self'" in response.headers["Content-Security-Policy"]
    assert "HttpOnly" in response.headers["Set-Cookie"]
    boot = json.load(request("/api/bootstrap"))
    headers = {"Content-Type": "application/json", "Origin": origin, "X-CSRF-Token": boot["csrf"]}
    for bad_headers in [{**headers, "Host": "attacker.example"}, {**headers, "Origin": "https://attacker.example"},
                        {**headers, "X-CSRF-Token": "bad"}, {"Content-Type": "application/json"}]:
        with pytest.raises(urllib.error.HTTPError) as error: request("/api/import", b"{}", bad_headers)
        assert error.value.code == 403
    assert json.load(request("/api/bootstrap"))["projects"] == []
    b = example_bundle(); request("/api/import", json.dumps(b).encode(), headers)
    restored = json.load(request("/api/bundle?project_id=" + b["project"]["id"]))
    assert restored == b
    with pytest.raises(urllib.error.HTTPError) as error:
        request("/api/import", b"{}", {**headers, "Content-Type": "text/plain"})
    assert error.value.code == 415
    with pytest.raises(urllib.error.HTTPError) as error:
        request("/api/import", b"{}", {**headers, "Content-Length": "33554433"})
    assert error.value.code == 422
    assert json.load(request("/api/bundle?project_id=" + b["project"]["id"])) == b
