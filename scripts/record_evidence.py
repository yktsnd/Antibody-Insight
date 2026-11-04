"""Record source identity for local uncommitted validation; never reads research DBs."""

import hashlib
import argparse
import json
import platform
import importlib.metadata
import uuid
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser()
parser.add_argument("--stage", default="M1")
parser.add_argument("--scope", default="Initial M1 F01-F05; not final eight journeys or sixteen edge cases")
args = parser.parse_args()
if not args.stage.replace("-", "").isalnum():
    parser.error("Stage must contain only letters, numbers and hyphens")
paths = [ROOT / p for p in (".gitattributes", "AGENTS.md", "PRODUCT_GOAL.md", "DEVELOPMENT_PLAN.md", "requirements.txt", "requirements-dev.txt", "start.ps1", "THIRD_PARTY_NOTICES.md") if (ROOT / p).exists()]
for folder, pattern in (("workspace_app", "*.py"), ("web", "*"), ("web/vendor", "*"), ("tests", "*.py"), ("tests", "*.cjs"), ("scripts", "*.py"), ("fixtures/public", "*")):
    paths.extend((ROOT / folder).glob(pattern))
checksums = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(paths)) if p.is_file()}
record = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "scope": args.scope,
    "git_base": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
    "source_state": "Exact working-tree source digests; use these when tested changes are not yet committed",
    "python": platform.python_version(), "platform": platform.platform(),
    "source_sha256": hashlib.sha256(json.dumps(checksums, sort_keys=True).encode()).hexdigest(),
    "files": checksums,
    "commands": [".venv/Scripts/python.exe -m pytest -q --tb=short", "node tests/browser.cjs", "node tests/numbering-browser.cjs", "node tests/structures-browser.cjs", "node tests/j01-browser.cjs", "node tests/j02-browser.cjs", "node tests/j05-browser.cjs", "node tests/j06-browser.cjs", "node tests/j07-browser.cjs", "node tests/decisions-independent-browser.cjs", "node tests/experiments-independent-browser.cjs", "node tests/numeric-transport-browser.cjs", "node tests/numeric-transport-guards-browser.cjs", "node tests/composition-independent-browser.cjs", "node tests/observation-independent-browser.cjs", "node tests/design-hypotheses-independent-browser.cjs", "node tests/design-save-independent-browser.cjs", "node tests/observation-journeys-browser.cjs", "node tests/observation-representation-independent-browser.cjs", "python scripts/check_traceability.py"],
}
try:
    record["gemmi_version"] = importlib.metadata.version("gemmi")
except importlib.metadata.PackageNotFoundError:
    record["gemmi_version"] = None
record["commands"].extend(["node tests/j08-browser.cjs", "node tests/predictions-independent-browser.cjs", "node tests/prediction-source-details-independent.cjs", "node tests/selection-independent-browser.cjs", "node tests/performance-browser.cjs", ".venv/Scripts/python.exe -m coverage run --branch --source=workspace_app -m pytest -q --tb=short"])
target = ROOT / "TEST_EVIDENCE" / f"{args.stage}-source-manifest.json"
pending = target.with_name(target.name + ".pending-" + uuid.uuid4().hex)
pending.write_text(json.dumps(record, indent=2), encoding="utf-8")
pending.replace(target)
print("Recorded source digest", record["source_sha256"])
