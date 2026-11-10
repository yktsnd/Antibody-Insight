"""Replay the four post-review browser suites against the final frozen source."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
TE = ROOT / 'TEST_EVIDENCE'
sys.path.insert(0, str(ROOT))
from scripts.check_traceability import source_files

manifest = json.loads((TE / 'M6-integration-independent-v2-source-manifest.json').read_text(encoding='utf-8'))
env = {**os.environ, 'PYTHONUTF8': '1', 'PYTHON': str(ROOT / '.venv/Scripts/python.exe'),
       'NODE_PATH': r'C:\Users\yukis\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules'}


def frozen():
    assert source_files(ROOT) == set(manifest['files'])
    assert all(hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest for path, digest in manifest['files'].items())


suites = [
    ('mapping-browser', ['node', 'TEST_EVIDENCE/M6-mapping-independent-browser.cjs', 'TEST_EVIDENCE/M6-final-mapping-browser.json'], {}),
    ('shortlist-browser', ['node', 'tests/shortlist-independent-browser.cjs'], {'SHORTLIST_REVIEW_OUTPUT': 'M6-final-shortlist-browser.json'}),
    ('research-entry-browser', ['node', 'tests/research-entry-independent-browser.cjs'], {'ENTRY_REVIEW_OUTPUT': 'M6-final-research-entry-browser.json'}),
    ('grouped-fasta-browser', ['node', 'tests/grouped-fasta-independent-browser.cjs'], {'GROUPED_REVIEW_OUTPUT': 'M6-final-grouped-fasta-browser.json'}),
    ('mapping-domain', [str(ROOT / '.venv/Scripts/python.exe'), 'TEST_EVIDENCE/M6-mapping-independent-probe.py', '--output', 'TEST_EVIDENCE/M6-final-mapping-domain.json'], {}),
]
assert not list(TE.glob('M6-final-*')), 'Use new evidence names; do not overwrite prior final replay'
runs = []
try:
    for name, command, extra_env in suites:
        frozen()
        print('START', name, flush=True)
        log_path = TE / ('M6-final-' + name + '-run.log')
        start = time.monotonic()
        with log_path.open('wb') as log:
            process = subprocess.run(command, cwd=ROOT, env={**env, **extra_env}, stdout=log, stderr=subprocess.STDOUT, timeout=600)
        frozen()
        output = TE / ('M6-final-' + name + '.json')
        report = json.loads(output.read_text(encoding='utf-8')) if output.exists() else None
        runs.append({'name': name, 'exit_code': process.returncode, 'duration_s': round(time.monotonic() - start, 2),
                     'log': log_path.name, 'report': output.name, 'status': report.get('status') if report else 'NO-REPORT',
                     'result_groups': len(report.get('results', [])) if report else 0})
        assert process.returncode == 0 and report['status'] == 'PASS', runs[-1]
        assert all(result['status'] == 'PASS' for result in report['results'])
        print('PASS', name, runs[-1], flush=True)
    status = 'PASS'
except BaseException:
    status = 'FAIL'
    raise
finally:
    (TE / 'M6-final-new-suites-summary.json').write_text(json.dumps({'status': status, 'reviewer': '/root/mapping_review',
        'source_sha256': manifest['source_sha256'], 'timestamp': datetime.now(timezone.utc).isoformat(), 'runs': runs,
        'scope': 'Four actual browser suites plus independent mapping domain probes; engineering evidence only. Real core/scientific/researcher validation remain separate.'}, indent=2), encoding='utf-8')
