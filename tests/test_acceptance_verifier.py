"""Acceptance must fail closed when a report or its tested implementation changes."""

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("traceability", Path(__file__).resolve().parents[1] / "scripts/check_traceability.py")
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


def evidence(tmp_path):
    (tmp_path / "workspace_app").mkdir()
    (tmp_path / "workspace_app/example.py").write_text("# original implementation\n", encoding="utf-8")
    report = {"status": "PASS", "results": [{"name": name, "status": "PASS"} for name in ("main", "negative1", "negative2")]}
    files = {p: verifier.digest(tmp_path / p) for p in verifier.source_files(tmp_path)}
    source = {"files": files, "source_sha256": hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()}
    (tmp_path / "review.md").write_text("Independent review: PASS\n", encoding="utf-8")
    (tmp_path / "report.json").write_text(json.dumps(report), encoding="utf-8")
    (tmp_path / "source.json").write_text(json.dumps(source), encoding="utf-8")
    row = {"review_result": "PASS", "reviewer": "independent reviewer", "commit": "a" * 40,
           "main_test": "main", "negative_test_1": "negative1", "negative_test_2": "negative2"}
    record = {"status": "PASS", "reviewer": row["reviewer"], "review_report": "review.md", "test_report": "report.json", "source_manifest": "source.json"}
    for key in ("review_report", "test_report", "source_manifest"):
        record[key + "_sha256"] = verifier.digest(tmp_path / record[key])
    return row, record


def test_complete_named_evidence_and_exact_source_pass(tmp_path):
    row, record = evidence(tmp_path)
    verifier.validate_acceptance(tmp_path, row, record)


@pytest.mark.parametrize("case", ["source_changed", "source_added", "report_changed", "review_changed", "missing_negative", "failed_negative", "duplicate_name", "wrong_reviewer", "commit_missing", "outside_repo"])
def test_unreviewed_or_changed_acceptance_rejects(tmp_path, case):
    row, record = evidence(tmp_path)
    if case == "source_changed": (tmp_path / "workspace_app/example.py").write_text("# changed", encoding="utf-8")
    elif case == "source_added": (tmp_path / "workspace_app/extra.py").write_text("# new", encoding="utf-8")
    elif case == "report_changed": (tmp_path / "report.json").write_text("{}", encoding="utf-8")
    elif case == "review_changed": (tmp_path / "review.md").write_text("FAIL", encoding="utf-8")
    elif case == "wrong_reviewer": record["reviewer"] = "implementation agent"
    elif case == "commit_missing": row["commit"] = ""
    elif case == "outside_repo": record["source_manifest"] = "../outside.json"
    else:
        report = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
        if case == "missing_negative": report["results"].pop()
        elif case == "failed_negative": report["results"][-1]["status"] = "FAIL"
        elif case == "duplicate_name": report["results"].append(report["results"][0])
        (tmp_path / "report.json").write_text(json.dumps(report), encoding="utf-8")
        record["test_report_sha256"] = verifier.digest(tmp_path / "report.json")
    with pytest.raises((AssertionError, KeyError)): verifier.validate_acceptance(tmp_path, row, record)
