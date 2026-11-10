"""Read-only audit of final engineering acceptance registration."""
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
TE = ROOT / 'TEST_EVIDENCE'
sys.path.insert(0, str(ROOT))
from scripts.check_traceability import source_files


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


manifest = read('TEST_EVIDENCE/M6-integration-independent-v2-source-manifest.json')
registration = read('TEST_EVIDENCE/M6-acceptance-registration.json')
commit = registration['implementation_commit']
assert commit == '057b3e97866a7c82cdf04f3e0d24db3ecdb251f8'
assert registration['source_sha256'] == manifest['source_sha256']
assert set(manifest['files']) == source_files(ROOT)
assert all(sha(path) == digest for path, digest in manifest['files'].items())
subprocess.run(['git', 'merge-base', '--is-ancestor', '7d691b2f8d47169c98d247a2d1e4562b872f6c23', commit], cwd=ROOT, check=True)

# Compare actual implementation content with the commit, recording the known
# canonical Git/worktree EOL distinction rather than claiming byte portability.
batch = subprocess.Popen(['git', 'cat-file', '--batch'], cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
eol_only = []
try:
    for path in sorted(manifest['files']):
        batch.stdin.write((commit + ':' + path + '\n').encode('utf-8'))
        batch.stdin.flush()
        header = batch.stdout.readline().decode('ascii').strip().split()
        assert len(header) == 3 and header[1] == 'blob', (path, header)
        blob = batch.stdout.read(int(header[2])); assert batch.stdout.read(1) == b'\n'
        actual = (ROOT / path).read_bytes()
        if blob != actual:
            assert actual.replace(b'\r\n', b'\n') == blob.replace(b'\r\n', b'\n'), 'Commit content mismatch: ' + path
            eol_only.append(path)
finally:
    batch.stdin.close(); batch.stdout.close(); batch.wait()
assert batch.returncode == 0

with (ROOT / 'TRACEABILITY.csv').open(encoding='utf-8-sig', newline='') as stream:
    journeys = list(csv.DictReader(stream))
acceptance = read('TEST_EVIDENCE/JOURNEY_ACCEPTANCE.json')['journeys']
assert len(journeys) == len(acceptance) == 8
expected_review = 'TEST_EVIDENCE/M6-final-independent-review.md'
expected_manifest = 'TEST_EVIDENCE/M6-integration-independent-v2-source-manifest.json'
for row in journeys:
    scenario = row['scenario_id']; item = acceptance[scenario]
    assert row['release_status'] == row['review_result'] == item['status'] == 'PASS'
    assert row['reviewer'] == item['reviewer'] == '/root/mapping_review'
    assert row['commit'] == commit
    assert item['review_report'] == expected_review and item['source_manifest'] == expected_manifest
    assert item['test_report'] == 'TEST_EVIDENCE/M6-integration-independent-v2-' + scenario + '-results.json'
    for field in ('review_report', 'source_manifest', 'test_report'):
        assert sha(item[field]) == item[field + '_sha256']
    report = read(item['test_report'])
    statuses = {case['name']: case['status'] for case in report['results']}
    assert len(statuses) == len(report['results'])
    assert report['status'] == 'PASS' and all(status == 'PASS' for status in statuses.values())
    for field in ('main_test', 'negative_test_1', 'negative_test_2'):
        assert statuses[row[field]] == 'PASS'

with (ROOT / 'IMPLEMENTATION_TRACEABILITY.csv').open(encoding='utf-8-sig', newline='') as stream:
    tickets = list(csv.DictReader(stream))
assert {item['ticket'] for item in tickets} == {f'F{i:02}' for i in range(1, 27)}
assert all(item['status'] == 'IMPLEMENTED_REVIEWED' for item in tickets)
assert all(item['review'] == expected_review for item in tickets if int(item['ticket'][1:]) >= 23)
for path, digest in registration['sha256'].items():
    assert sha(path) == digest, path
evidence = read('TEST_EVIDENCE/M6-final-independent-evidence-sha256.json')
assert evidence['count'] == len(evidence['files']) == 97
assert all(sha(path) == digest for path, digest in evidence['files'].items())

gates = read('TEST_EVIDENCE/M6-release-gates.json')
assert gates['implementation_commit'] == commit and gates['source_sha256'] == manifest['source_sha256']
assert gates['current_engineering_review'] == 'PASS' and gates['engineering_workflows']['main_flows'] == 8
assert gates['engineering_workflows']['prescribed_negative_flows'] == 16
assert gates['regression']['python_tests'] == 549 and gates['regression']['node_commands'] == 26
assert gates['overall_release_status'] == 'INCOMPLETE' and gates['current_product_acceptance'] == 'NOT_REEVALUATED'
assert gates['real_data_core']['status'] == 'PARTIAL' and len(gates['real_data_core']['remaining']) >= 4
assert gates['fixes']['F25'] == 'ENGINEERING_PASS_HUMAN_FIRST_USE_PENDING'
assert gates['scientific_validation']['status'] == gates['researcher_evaluation']['status'] == gates['standard_host_performance']['status'] == 'PENDING'

old = read('TEST_EVIDENCE/M6-integration-independent-historical-before.json')
raw = {path: digest for path, digest in old['files'].items() if path != 'TEST_EVIDENCE/JOURNEY_ACCEPTANCE.json'}
assert len(raw) == 641 and all(sha(path) == digest for path, digest in raw.items())
archive = read('TEST_EVIDENCE/M6-previous-JOURNEY_ACCEPTANCE.json')
old_registry = json.loads(subprocess.check_output(['git', 'show', '7d691b2:TEST_EVIDENCE/JOURNEY_ACCEPTANCE.json'], cwd=ROOT))
assert archive == old_registry, 'The previous active acceptance registry was not preserved'
checker = subprocess.run([sys.executable, 'scripts/check_traceability.py'], cwd=ROOT, check=True, capture_output=True, text=True, encoding='utf-8')
result = {'status': 'PASS', 'reviewer': '/root/mapping_review', 'timestamp': datetime.now(timezone.utc).isoformat(),
          'scope': 'Registration consistency only; bounded engineering acceptance, not whole-product completion',
          'implementation_commit': commit, 'source_sha256': manifest['source_sha256'], 'source_files': 107,
          'git_source_content_matches': True, 'git_worktree_eol_only_differences': eol_only,
          'fresh_checkout_byte_attestation': 'PENDING', 'journeys': 8, 'named_negative_paths': 16,
          'traced_reviewed_tickets': 26, 'finished_acceptance_artifact_hashes_verified': 97,
          'historical_raw_files_unchanged': 641, 'historical_registry_preserved': True,
          'registered_hashes': registration['sha256'], 'traceability_checker': checker.stdout.strip()}
output = TE / 'M6-registration-independent-audit.json'
assert not output.exists(), 'Do not overwrite an earlier audit'
output.write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
