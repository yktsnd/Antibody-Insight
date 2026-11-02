"""Record source identity for local uncommitted validation; never reads research DBs."""

import hashlib
import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
paths = [ROOT / p for p in ("AGENTS.md", "PRODUCT_GOAL.md", "DEVELOPMENT_PLAN.md")]
for folder, pattern in (("workspace_app", "*.py"), ("web", "*"), ("tests", "*.py"), ("tests", "*.cjs"), ("scripts", "*.py")):
    paths.extend((ROOT / folder).glob(pattern))
checksums = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(paths)) if p.is_file()}
record = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "scope": "Initial M1 F01-F05; not final eight journeys or sixteen edge cases",
    "git_base": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
    "source_state": "Exact working-tree source digests; use these when tested changes are not yet committed",
    "python": platform.python_version(), "platform": platform.platform(),
    "source_sha256": hashlib.sha256(json.dumps(checksums, sort_keys=True).encode()).hexdigest(),
    "files": checksums,
    "commands": ["python -m pytest -q --tb=short", "node tests/browser.cjs", "python scripts/check_traceability.py"],
}
(ROOT / "TEST_EVIDENCE" / "M1-source-manifest.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
print("Recorded initial-source digest", record["source_sha256"])
