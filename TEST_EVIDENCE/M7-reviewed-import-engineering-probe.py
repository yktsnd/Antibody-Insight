"""Exercise attestation transport and design in an explicitly synthetic test project."""

import hashlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]

from public_structure_fixture import public_structure_bundle
from workspace_app.design import variant_preview
from workspace_app.numbering_import import anarci_preview
from workspace_app.storage import Store

bundle = public_structure_bundle()
parent = bundle["entities"][0]
bundle["entities"] = [parent]
bundle["project"].update(title="Synthetic review record plumbing test", data_class="synthetic_fixture")
native = ROOT / "fixtures/public/1MLC-AB.anarci.txt"
raw = native.read_bytes()
digest = hashlib.sha256(raw).hexdigest()
review = {"status": "source_verified", "reviewer": "Synthetic engineering test record",
          "reference": "Test-only attestation used to exercise the existing design gate",
          "reviewed_at": "2026-11-11T00:00:00+00:00"}
bindings = [{"record_index": 0, "domain_index": 1, "molecule_id": parent["id"], "chain_id": "A",
             "verification": review}]
with tempfile.TemporaryDirectory(prefix="awx-m7-attestation-test-") as temp:
    store = Store(Path(temp) / "test.sqlite3")
    store.import_bundle(bundle)
    preview = anarci_preview(bundle, raw.decode("utf-8"), native.name, "2026.2.13.2", bindings, digest)
    store.import_bundle(preview["bundle"])
    numbering = preview["bundle"]["entities"][1]
    assert numbering["verification"] == review
    before = store.bundle(bundle["project"]["id"])
    variant = variant_preview(before, parent["id"], "Engineering test substitution", "TEST-D44-A-S30A",
                              "Exercise an eligible reviewed map through existing design",
                              [{"parent_map_id": numbering["id"], "number": 36, "ins_code": "",
                                "to_aa": "A", "reference_map_id": None}])
    store.import_bundle(variant)
    after = Store(store.path).bundle(bundle["project"]["id"])
    child = next(e for e in after["entities"] if e.get("external_id") == "TEST-D44-A-S30A")
    assert parent["chains"][0]["sequence"][29] == "S"
    assert child["chains"][0]["sequence"][29] == "A"
    assert parent in after["entities"] and child["chains"][1] == parent["chains"][1]
    assert all(e["type"] != "evidence" for e in after["entities"])
    mutation = next(e for e in after["entities"] if e["type"] == "lineage")["change_set"]["mutations"][0]
    assert mutation["sequence_index"] == 30 and mutation["number"] == 36
    print(json.dumps({"status": "PASS", "scope": "Synthetic attestation plumbing only",
                      "native_file_sha256": digest, "raw_index": 30, "IMGT_position": 36,
                      "parent_preserved": True, "child_and_lineage_persisted": True}))
