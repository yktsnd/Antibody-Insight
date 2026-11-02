"""Check declared coverage without equating a partial slice with full acceptance."""

import ast
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    with (ROOT / "TRACEABILITY.csv").open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 8 and {r["scenario_id"] for r in rows} == {f"J{i:02}" for i in range(1, 9)}
    for r in rows:
        j = r["scenario_id"]
        assert r["persona_id"] == "P" + j[1:] and r["acceptance_id"] == "AC-" + j
        assert all(r[key] for key in ("main_test", "negative_test_1", "negative_test_2"))
        assert r["release_status"] in {"PLANNED", "PARTIAL", "PASS"}
        if r["release_status"] == "PASS":
            assert r["review_result"] == "PASS" and r["commit"]
            raise AssertionError("Full acceptance gate requires a release verifier; not implemented in this initial checker")
    with (ROOT / "IMPLEMENTATION_TRACEABILITY.csv").open(encoding="utf-8-sig", newline="") as f:
        slices = list(csv.DictReader(f))
    assert {s["ticket"] for s in slices} == {f"F{i:02}" for i in range(1, 7)}
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
    print("Full journey acceptance: 0/8. Prescribed final browser edge cases: 0/16. Initial checks are not counted as full acceptance.")


if __name__ == "__main__":
    main()
