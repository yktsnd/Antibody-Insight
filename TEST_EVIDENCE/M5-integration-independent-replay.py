"""Independent review orchestration; never modifies application/source files.

Run only after the implementation agent supplies the final frozen manifest and
exclusive Chrome slot. All browser interactions remain the real test scripts.
Copy their current evidence under independent names, then restore exact previous
bytes for overwritten historical outputs. No acceptance registration is edited.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TE = ROOT / 'TEST_EVIDENCE'
sys.path.insert(0, str(ROOT))
from scripts.check_traceability import source_files

GROUPS = {
    'journeys': [
        ('j01-browser.cjs', {'J01-browser-results.json': 'J01-results.json'}),
        ('j02-browser.cjs', {'J02-browser-results.json': 'J02-results.json'}),
        ('observation-journeys-browser.cjs', {'J03-browser-results.json': 'J03-results.json',
            'J04-browser-results.json': 'J04-results.json', 'public-structure-browser-results.json': 'public-results.json'}),
        ('j05-browser.cjs', {'J05-browser-results.json': 'J05-results.json'}),
        ('j06-browser.cjs', {'M4-J06-browser-results.json': 'J06-results.json'}),
        ('j07-browser.cjs', {'M4-J07-browser-results.json': 'J07-results.json'}),
        ('j08-browser.cjs', {'M5-J08-browser-results.json': 'J08-results.json'}),
    ],
    'retained': [
        ('browser.cjs', {'M1-browser-results.json': 'foundation-results.json'}),
        ('numbering-browser.cjs', {'M2-numbering-browser-results.json': 'numbering-results.json'}),
        ('structures-browser.cjs', {'M2-structure-browser-results.json': 'structures-results.json'}),
        ('observation-independent-browser.cjs', {'M2-observation-independent-browser-results.json': 'observation-results.json'}),
        ('design-hypotheses-independent-browser.cjs', {'M3-numbered-design-independent-browser-results.json': 'design-results.json'}),
        ('design-save-independent-browser.cjs', {'M3-numbered-design-independent-save-results.json': 'design-save-results.json'}),
    ],
    'edges': [
        ('composition-independent-browser.cjs', {'M3-composition-independent-browser-results.json': 'composition-edges-results.json'}),
        ('observation-representation-independent-browser.cjs', {'M3-observation-representation-independent-results.json': 'representation-results.json'}),
        ('experiments-independent-browser.cjs', {'M4-experiments-independent-browser-results.json': 'experiments-edges-results.json'}),
        ('decisions-independent-browser.cjs', {'M4-decisions-independent-browser-results.json': 'decisions-edges-results.json'}),
        ('numeric-transport-browser.cjs', {'M4-numeric-transport-browser-results.json': 'numeric-results.json'}),
        ('numeric-transport-guards-browser.cjs', {'M4-numeric-transport-guards-results.json': 'numeric-guards-results.json'}),
        ('predictions-independent-browser.cjs', {'M5-predictions-independent-browser-results.json': 'predictions-edges-results.json'}),
        ('prediction-source-details-independent.cjs', {'M5-source-details-independent-results.json': 'source-details-results.json'}),
        ('selection-independent-browser.cjs', {'M5-selection-independent-browser-results.json': 'selection-results.json'}),
    ],
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write(name, value):
    (TE / name).write_text(json.dumps(value, indent=2), encoding='utf-8')


parser = argparse.ArgumentParser()
parser.add_argument('manifest', type=Path)
parser.add_argument('group', choices=GROUPS)
args = parser.parse_args()
manifest = json.loads(args.manifest.read_text(encoding='utf-8'))
assert sha(json.dumps(manifest['files'], sort_keys=True).encode()) == manifest['source_sha256']
env = {**os.environ, 'PYTHONUTF8': '1', 'PYTHON': str(ROOT / '.venv/Scripts/python.exe'),
       'NODE_PATH': r'C:\Users\yukis\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules'}
runs, preservation = [], []
prefix = 'M5-integration-independent-'


def frozen():
    assert source_files(ROOT) == set(manifest['files']), 'Frozen source inventory changed'
    changed = [p for p, expected in manifest['files'].items() if sha((ROOT / p).read_bytes()) != expected]
    assert not changed, 'Frozen source changed: '+repr(changed)


try:
    frozen()
    for suite, reports in GROUPS[args.group]:
        frozen()
        slug = suite.removesuffix('.cjs').removesuffix('-browser')
        candidates = set(re.findall(r'\b[A-Za-z0-9][A-Za-z0-9_.-]*\.(?:json|png)\b',
                                    (ROOT / 'tests' / suite).read_text(encoding='utf-8'))) | set(reports)
        before = {name: (TE / name).read_bytes() for name in candidates if (TE / name).is_file()}
        log_name = prefix+slug+'-run.log'
        start = time.monotonic()
        print('START', suite, flush=True)
        with (TE / log_name).open('wb') as log:
            process = subprocess.run(['node', str(ROOT / 'tests' / suite)], cwd=ROOT, env=env,
                                     stdout=log, stderr=subprocess.STDOUT)
        copied = []
        for name in sorted(candidates):
            path = TE / name
            if path.is_file() and (name in reports or path.read_bytes() != before.get(name)):
                target = prefix+reports.get(name, slug+'-'+name)
                data = path.read_bytes()
                (TE / target).write_bytes(data)
                copied.append({'original': name, 'copy': target, 'sha256': sha(data)})
        # Restore actual pre-run bytes. Runtime outputs were independently
        # checked against literal Git blobs; unrelated CRLF-only old texts are
        # not normalized or overwritten by this runner.
        for name, previous in before.items():
            path = TE / name
            if path.read_bytes() != previous:
                current = path.read_bytes()
                path.write_bytes(previous)
                assert path.read_bytes() == previous
                preservation.append({'path': name, 'before_after_sha256': sha(previous),
                                     'copied_current_sha256': sha(current), 'suite': suite})
        frozen()
        checked = []
        for name, target in reports.items():
            report = json.loads((TE / (prefix+target)).read_text(encoding='utf-8'))
            assert report['status'] == 'PASS', (suite, target, report)
            if 'results' in report:
                assert all(r['status'] == 'PASS' for r in report['results'])
            checked.append({'report': prefix+target, 'status': report['status'],
                            'result_groups': len(report.get('results', [])) if 'results' in report else None})
        runs.append({'suite': suite, 'exit_code': process.returncode,
                     'duration_s': round(time.monotonic()-start, 2), 'log': log_name,
                     'results': checked, 'copied_artifacts': copied})
        write(prefix+args.group+'-replay.json', {'status': 'RUNNING', 'source_sha256': manifest['source_sha256'],
              'runs': runs, 'preservation': preservation})
        assert process.returncode == 0, (suite, process.returncode)
        print('PASS', suite, checked, flush=True)
    frozen()
    write(prefix+args.group+'-replay.json', {'status': 'PASS', 'source_sha256': manifest['source_sha256'],
          'runs': runs, 'preservation': preservation, 'timestamp': datetime.now(timezone.utc).isoformat()})
except BaseException as exc:
    write(prefix+args.group+'-replay.json', {'status': 'FAIL', 'source_sha256': manifest['source_sha256'],
          'runs': runs, 'preservation': preservation, 'error': repr(exc),
          'timestamp': datetime.now(timezone.utc).isoformat()})
    raise
