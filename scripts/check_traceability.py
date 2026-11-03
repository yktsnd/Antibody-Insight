"""Check declared coverage without equating a partial slice with full acceptance."""

import ast
import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def artifact(root, relative):
    assert isinstance(relative, str), "Evidence path must be text"
    path = (root / relative).resolve()
    assert path.is_relative_to(root.resolve()) and path.is_file(), relative
    return path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_files(root):
    paths = {root / p for p in (".gitattributes", "AGENTS.md", "PRODUCT_GOAL.md", "DEVELOPMENT_PLAN.md", "requirements.txt", "requirements-dev.txt", "start.ps1", "THIRD_PARTY_NOTICES.md") if (root / p).is_file()}
    for folder, pattern in (("workspace_app", "*.py"), ("web", "*"), ("web/vendor", "*"), ("tests", "*.py"), ("tests", "*.cjs"), ("scripts", "*.py"), ("fixtures/public", "*")):
        paths.update(p for p in (root / folder).glob(pattern) if p.is_file())
    return {p.relative_to(root).as_posix() for p in paths}


def validate_acceptance(root, row, record):
    """Require independently signed-off named browser results and exact tested source."""
    assert record["status"] == row["review_result"] == "PASS"
    assert record["reviewer"] == row["reviewer"] and record["reviewer"]
    assert re.fullmatch(r"[0-9a-f]{40}", row["commit"]), "Accepted journey needs its local implementation commit"
    for key in ("review_report", "test_report", "source_manifest"):
        assert digest(artifact(root, record[key])) == record[key + "_sha256"], f"Changed acceptance artifact: {key}"
    report = json.loads(artifact(root, record["test_report"]).read_text(encoding="utf-8"))
    assert report["status"] == "PASS"
    results = report["results"]
    assert len({r["name"] for r in results}) == len(results), "Duplicate test names"
    assert all(r["status"] == "PASS" for r in results)
    assert {row["main_test"], row["negative_test_1"], row["negative_test_2"]} <= {r["name"] for r in results}
    source = json.loads(artifact(root, record["source_manifest"]).read_text(encoding="utf-8"))
    assert source["source_sha256"] == hashlib.sha256(json.dumps(source["files"], sort_keys=True).encode()).hexdigest()
    assert set(source["files"]) == source_files(root), "Source inventory changed; independent replay required"
    for relative, expected in source["files"].items():
        assert digest(artifact(root, relative)) == expected, f"Source changed since acceptance: {relative}"


def main():
    with (ROOT / "TRACEABILITY.csv").open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 8 and {r["scenario_id"] for r in rows} == {f"J{i:02}" for i in range(1, 9)}
    acceptance_path = ROOT / "TEST_EVIDENCE" / "JOURNEY_ACCEPTANCE.json"
    acceptance = json.loads(acceptance_path.read_text(encoding="utf-8")) if acceptance_path.exists() else {"schema_version": "journey-acceptance/1", "journeys": {}}
    assert acceptance["schema_version"] == "journey-acceptance/1"
    assert set(acceptance["journeys"]) <= {r["scenario_id"] for r in rows}
    passed = 0
    for r in rows:
        j = r["scenario_id"]
        assert r["persona_id"] == "P" + j[1:] and r["acceptance_id"] == "AC-" + j
        assert all(r[key] for key in ("main_test", "negative_test_1", "negative_test_2"))
        assert r["release_status"] in {"PLANNED", "PARTIAL", "PASS"}
        if r["release_status"] == "PASS":
            validate_acceptance(ROOT, r, acceptance["journeys"][j])
            subprocess.run(["git", "cat-file", "-e", r["commit"] + "^{commit}"], cwd=ROOT, check=True, capture_output=True)
            passed += 1
        else:
            assert j not in acceptance["journeys"], "Acceptance and traceability disagree"
    with (ROOT / "IMPLEMENTATION_TRACEABILITY.csv").open(encoding="utf-8-sig", newline="") as f:
        slices = list(csv.DictReader(f))
    assert {s["ticket"] for s in slices} == {f"F{i:02}" for i in range(1, len(slices) + 1)}
    for s in slices:
        assert s["persona_ids"] and s["scenario_ids"] and s["acceptance_ids"]
        assert set(s["acceptance_ids"].split(";")) == {"AC-" + j for j in s["scenario_ids"].split(";")}
        assert set(s["persona_ids"].split(";")) == {"P" + j[1:] for j in s["scenario_ids"].split(";")}
        for source in s["implementation"].split(";"):
            assert (ROOT / source).is_file(), source
        for check in s["checks"].split(";"):
            filename, _, name = check.partition("::")
            p = ROOT / filename
            assert p.is_file(), filename
            if name:
                functions = {n.name for n in ast.walk(ast.parse(p.read_text(encoding="utf-8"))) if isinstance(n, ast.FunctionDef)}
                assert name in functions, check
        if s["status"] == "IMPLEMENTED_REVIEWED":
            assert (ROOT / s["review"]).is_file()
    print(f"PASS: {len(rows)} complete journey definitions and {len(slices)} traced implementation slices")
    print(f"Full journey engineering acceptance: {passed}/8. Prescribed final browser edge cases: {2 * passed}/16. Release 1.0 scientific, user and integration gates remain separate.")


if __name__ == "__main__":
    main()
