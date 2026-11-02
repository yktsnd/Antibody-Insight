"""Independent review cases for the initial F01-F05 slice, not full journeys."""

import copy
import json
import threading
import urllib.error
import urllib.request
from http.cookiejar import CookieJar

import pytest

from workspace_app.adapters import new_project, parse_json, preview
from workspace_app.domain import ValidationError, new_id, shortlist
from workspace_app.fixtures import example_bundle
from workspace_app.server import make_server
from workspace_app.storage import Store


@pytest.mark.parametrize("change", ["value_boolean", "condition_boolean"])
def test_snapshot_requires_exact_json_types_not_python_numeric_equality(tmp_path, change):
    bundle = example_bundle()
    original = next(e for e in bundle["entities"] if e["type"] == "evidence" and e["kind"] == "measured")
    original["conditions"] = {"replicate": 0}
    store = Store(tmp_path / "exact-snapshot.sqlite3")
    store.import_bundle(bundle)
    candidate = next(e["id"] for e in bundle["entities"] if e["type"] == "molecule")
    draft = store.save_shortlist(bundle["project"]["id"], [candidate], [original["id"]], "Independent exact snapshot check")
    draft["id"] = new_id("decision")
    if change == "value_boolean":
        draft["evidence_snapshot"][0]["value"] = False
    else:
        draft["evidence_snapshot"][0]["conditions"]["replicate"] = False
    before = store.bundle(bundle["project"]["id"])
    with pytest.raises(ValidationError):
        store.import_bundle({**bundle, "entities": [draft]})
    assert store.bundle(bundle["project"]["id"]) == before


def test_graph_forward_references_and_shuffled_roundtrip(tmp_path):
    original = example_bundle()
    original["entities"] = list(reversed(original["entities"]))
    first = Store(tmp_path / "first.sqlite3")
    first.import_bundle(original)
    exported = first.bundle(original["project"]["id"])
    second = Store(tmp_path / "second.sqlite3")
    second.import_bundle(json.loads(json.dumps(exported)))
    assert second.bundle(original["project"]["id"]) == original


def test_decision_before_invalid_material_uses_validation_error_and_preserves_db(tmp_path):
    bundle = example_bundle()
    store = Store(tmp_path / "reference-order.sqlite3")
    candidate = next(e["id"] for e in bundle["entities"] if e["type"] == "molecule")
    evidence = next(e for e in bundle["entities"] if e["type"] == "evidence")
    draft = shortlist(bundle["project"], bundle["entities"], [candidate], [evidence["id"]], "Independent reference order check")
    material = next(e for e in bundle["entities"] if e["id"] == evidence["subject_id"])
    material["construct_id"] = new_id("construct")
    bundle["entities"] = [draft, *bundle["entities"]]
    with pytest.raises(ValidationError):
        store.import_bundle(bundle)
    assert store.projects() == []


def test_unknown_source_version_and_hostile_text_roundtrip(tmp_path):
    text = '<img src="https://example.invalid/leak" onerror="alert(1)">'
    result = preview(f">{text}\nEVQL\n", "fasta", "hostile-fixture.fa", new_project("Hostile text fixture", "Escaping check"))
    result["bundle"]["entities"][0]["source"]["version"] = None
    store = Store(tmp_path / "hostile.sqlite3")
    store.import_bundle(result["bundle"])
    exported = store.bundle(result["bundle"]["project"]["id"])
    assert exported == result["bundle"]
    assert exported["entities"][0]["external_id"] == text
    assert exported["entities"][0]["source"]["version"] is None


def test_missing_nested_version_and_multiple_unknown_keys_reject_atomically(tmp_path):
    bundle = example_bundle()
    store = Store(tmp_path / "nested.sqlite3")
    missing = copy.deepcopy(bundle)
    del missing["entities"][0]["source"]["version"]
    with pytest.raises(ValidationError, match="missing fields"):
        store.import_bundle(missing)
    unknown = copy.deepcopy(bundle)
    unknown["entities"][0]["source"]["score"] = 0.5
    unknown["entities"][0]["source"]["confidence"] = 1
    with pytest.raises(ValidationError) as error:
        store.import_bundle(unknown)
    assert error.value.details == ["source.confidence", "source.score"]
    assert store.projects() == []


def test_nonzero_json_float_underflow_is_not_silently_zero():
    with pytest.raises(ValidationError):
        parse_json('{"value":1e-999}')
    assert parse_json('{"value":0e-999}')["value"] == 0


@pytest.fixture
def review_http(tmp_path):
    server = make_server(tmp_path / "independent-http.sqlite3", 0)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    yield server
    server.shutdown()
    worker.join(timeout=5)
    server.server_close()


def authenticated_client(server):
    jar = CookieJar()
    client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    client.open(server.origin + "/", timeout=5).close()
    with client.open(server.origin + "/api/bootstrap", timeout=5) as response:
        csrf = json.load(response)["csrf"]
    return client, {"Content-Type": "application/json", "Origin": server.origin, "X-CSRF-Token": csrf}


def test_cross_site_get_duplicate_json_and_invalid_utf8_are_rejected(review_http):
    client, headers = authenticated_client(review_http)
    with pytest.raises(urllib.error.HTTPError) as error:
        client.open(urllib.request.Request(review_http.origin + "/api/bootstrap", headers={"Sec-Fetch-Site": "cross-site"}), timeout=5)
    assert error.value.code == 401
    for body in (b'{"schema_version":"awx/1","schema_version":"awx/2"}', b'\xff\xfe'):
        with pytest.raises(urllib.error.HTTPError) as error:
            client.open(urllib.request.Request(review_http.origin + "/api/import", data=body, headers=headers), timeout=5)
        assert error.value.code == 422
    assert review_http.store.projects() == []


@pytest.mark.parametrize("field", ["value", "conditions"])
@pytest.mark.parametrize("number", [10 ** 400, 2 ** 53 + 1])
def test_large_finite_json_integer_rejects_without_disconnect_or_database_write(review_http, field, number):
    bundle = example_bundle()
    evidence = next(e for e in bundle["entities"] if e["type"] == "evidence")
    evidence[field] = number if field == "value" else {"large_integer": number}
    client, headers = authenticated_client(review_http)
    with pytest.raises(urllib.error.HTTPError) as error:
        client.open(urllib.request.Request(review_http.origin + "/api/import", data=json.dumps(bundle).encode(), headers=headers), timeout=5)
    assert error.value.code == 422
    assert review_http.store.projects() == []
