"""Record source identity for local uncommitted validation; never reads research DBs."""

import hashlib
import argparse
import json
import platform
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
paths = [ROOT / p for p in ("AGENTS.md", "PRODUCT_GOAL.md", "DEVELOPMENT_PLAN.md")]
for folder, pattern in (("workspace_app", "*.py"), ("web", "*"), ("tests", "*.py"), ("tests", "*.cjs"), ("scripts", "*.py")):
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
    "commands": ["python -m pytest -q --tb=short", "node tests/browser.cjs", "python scripts/check_traceability.py"],
}
(ROOT / "TEST_EVIDENCE" / f"{args.stage}-source-manifest.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
print("Recorded source digest", record["source_sha256"])
