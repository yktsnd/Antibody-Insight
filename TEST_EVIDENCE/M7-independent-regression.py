"""Replay the accepted regression suites in an exact temporary source snapshot."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
TE = ROOT / 'TEST_EVIDENCE'
sys.path.insert(0, str(ROOT))
from scripts.check_traceability import source_files

def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def new_json(path, content):
    with path.open('x', encoding='utf-8') as out:
        json.dump(content, out, indent=2)


def freeze():
    assert not (TE / NAME).exists()
    snapshot = Path(tempfile.mkdtemp(prefix='antibody-M7-regression-'))
    files = {path: sha((ROOT / path).read_bytes()) for path in sorted(source_files(ROOT))}
    git_paths = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode('utf-8').split('\0')
    paths = set(files) | {p for p in git_paths if p and not p.startswith('TEST_EVIDENCE/')}
    paths.update('TEST_EVIDENCE/' + name for name in ('M6-mapping-independent-browser.cjs', 'M6-mapping-independent-probe.py',
                  'M5-integration-independent-reviewed-pre-lazy-metadata.js'))
    for path in sorted(paths):
        target = snapshot / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / path, target)
    legacy = (TE / 'M6-independent-regression-runner.py').read_text(encoding='utf-8')
    legacy = legacy.replace("r'M6-[A-Za-z0-9-]+-'", "r'M7-[A-Za-z0-9-]+-'")
    legacy = legacy.replace("str(ROOT / '.venv/Scripts/python.exe')", "os.environ['PYTHON']")
    (snapshot / 'TEST_EVIDENCE/regression-runner.py').write_text(legacy, encoding='utf-8')
    scoped = (TE / 'M6-independent-new-suites.py').read_text(encoding='utf-8')
    scoped = scoped.replace('M6-integration-independent-v2-source-manifest.json', NAME)
    scoped = scoped.replace('M6-final-', f'M7-scoped-v{REVISION}-')
    scoped = scoped.replace("str(ROOT / '.venv/Scripts/python.exe')", "os.environ['PYTHON']")
    (snapshot / 'TEST_EVIDENCE/scoped-runner.py').write_text(scoped, encoding='utf-8')
    manifest = {'timestamp': now(), 'reviewer': '/root/mapping_review', 'snapshot': str(snapshot),
                'git_base': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                'scope': 'Exact working-tree source for bounded F27/F28 integration and retained engineering regression',
                'source_sha256': sha(json.dumps(files, sort_keys=True).encode()), 'files': files}
    check(manifest)
    new_json(snapshot / 'TEST_EVIDENCE' / NAME, manifest)
    new_json(TE / NAME, manifest)
    print(f"Frozen {len(files)} files {manifest['source_sha256']} in {snapshot}", flush=True)


def check(manifest):
    for path in (ROOT, Path(manifest['snapshot'])):
        assert source_files(path) == set(manifest['files']), f'Source inventory changed in {path}'
        changed = [p for p, expected in manifest['files'].items() if sha((path / p).read_bytes()) != expected]
        assert not changed, (str(path), changed)


def replay(phase):
    manifest = json.loads((TE / NAME).read_text(encoding='utf-8'))
    snapshot = Path(manifest['snapshot'])
    env = {**os.environ, 'PYTHON': sys.executable, 'PYTHONUTF8': '1'}
    check(manifest)
    if phase == 'python':
        jobs = [('python', [sys.executable, '-m', 'pytest', '-q'], None)]
    elif phase == 'deposited':
        script = 'TEST_EVIDENCE/M7-deposited-independent-browser.cjs'
        shutil.copyfile(ROOT / script, snapshot / script)
        env['NODE_PATH'] = r'C:\Users\yukis\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules'
        prefix = f'M7-deposited-v{REVISION}-'
        jobs = [('deposited', ['node', script, f'TEST_EVIDENCE/{prefix}browser.json'], prefix)]
    else:
        groups = ('journeys', 'retained', 'edges')
        if phase == 'resume-browser':
            fixture = 'TEST_EVIDENCE/M5-integration-independent-reviewed-pre-lazy-metadata.js'
            shutil.copyfile(ROOT / fixture, snapshot / fixture)
            runner = snapshot / 'TEST_EVIDENCE/regression-runner.py'
            code = runner.read_text(encoding='utf-8')
            needle = 'parser = argparse.ArgumentParser()'
            if "GROUPS['edges-tail']" not in code:
                code = code.replace(needle, "GROUPS['edges-tail'] = GROUPS['edges'][-2:]\n" + needle)
                runner.write_text(code, encoding='utf-8')
            groups = ('edges-tail',)
        jobs = [(group, [sys.executable, 'TEST_EVIDENCE/regression-runner.py', 'TEST_EVIDENCE/' + NAME, group,
                         '--prefix', f'M7-{group}-v{REVISION}-'], f'M7-{group}-v{REVISION}-') for group in groups]
        jobs.append(('scoped', [sys.executable, 'TEST_EVIDENCE/scoped-runner.py'], f'M7-scoped-v{REVISION}-'))
    runs = []
    summary = TE / f'M7-{phase}-independent-v{REVISION}-summary.json'
    assert not summary.exists()
    try:
        for name, command, prefix in jobs:
            check(manifest)
            print('START', name, flush=True)
            start = time.monotonic()
            log = TE / f'M7-{name}-independent-v{REVISION}.log'
            with log.open('xb') as out:
                result = subprocess.run(command, cwd=snapshot, env=env, stdout=out, stderr=subprocess.STDOUT, timeout=3600)
            copied = []
            if prefix:
                for path in sorted((snapshot / 'TEST_EVIDENCE').glob(prefix + '*')):
                    with (TE / path.name).open('xb') as dest:
                        dest.write(path.read_bytes())
                    copied.append(path.name)
            check(manifest)
            runs.append({'name': name, 'exit_code': result.returncode, 'duration_s': round(time.monotonic() - start, 2),
                         'log': log.name, 'copied_artifacts': copied,
                         'tail': log.read_text(encoding='utf-8', errors='replace').splitlines()[-5:]})
            print(json.dumps(runs[-1]), flush=True)
            assert result.returncode == 0, runs[-1]
        status = 'PASS'
    except BaseException:
        status = 'FAIL'
        raise
    finally:
        new_json(summary, {'status': status, 'reviewer': '/root/mapping_review', 'timestamp': now(),
                           'source_sha256': manifest['source_sha256'], 'runs': runs})


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('freeze', 'python', 'browser', 'resume-browser', 'deposited'))
    parser.add_argument('--revision', type=int, default=2)
    args = parser.parse_args()
    REVISION = args.revision
    NAME = f'M7-integration-independent-v{REVISION}-source-manifest.json'
    freeze() if args.phase == 'freeze' else replay(args.phase)
