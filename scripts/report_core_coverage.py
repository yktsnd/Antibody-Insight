"""Release1.0: report actual branch coverage of the complete domain/storage core.

P01–P08 / J01–J08 / AC-J01–AC-J08. Read-only evidence processing;
does not infer scientific validity or waive independent/human acceptance.
"""
import argparse
import json
from pathlib import Path

CORE = {'adapters', 'assembly', 'composition', 'decisions', 'design', 'domain',
        'experiments', 'hypotheses', 'measurements', 'numbering', 'numbering_import', 'observation',
        'predictions', 'residue_evidence', 'storage', 'structures'}
parser = argparse.ArgumentParser()
parser.add_argument('coverage_json', type=Path)
parser.add_argument('output', type=Path)
args = parser.parse_args()
raw = json.loads(args.coverage_json.read_text(encoding='utf-8'))
assert raw['meta']['branch_coverage'], 'A statement-only run cannot establish the branch gate'
core, excluded = {}, {}
for path, record in raw['files'].items():
    name = path.replace('\\', '/').rsplit('/', 1)[-1].removesuffix('.py')
    if name in CORE:
        core[name] = record['summary']
    else:
        assert name in {'__init__', 'server', 'fixtures'} or name.endswith('_fixtures'), 'Unclassified production module: '+name
        excluded[name] = record['summary']
assert set(core) == CORE, 'Every core module must appear in measurement'
total = sum(s['num_branches'] for s in core.values())
covered = sum(s['covered_branches'] for s in core.values())
percent = 100*covered/total
result = {'status': 'PASS' if percent >= 85 else 'FAIL', 'core_branch_percent': percent,
          'covered_branches': covered, 'num_branches': total, 'threshold_percent': 85,
          'modules': core, 'other_measured_modules': excluded, 'all_workspace_app_totals': raw['totals'],
          'method': 'Coverage.py branch opportunities, no source exclusions/pragmas. Core includes all validation, adapters, identity/provenance, scientific correspondence, design, observations, decisions and persistence modules. HTTP/static routing and synthetic fixture generators are separately reported, never hidden. This is engineering coverage, not scientific/user validation.'}
args.output.write_text(json.dumps(result, indent=2), encoding='utf-8')
print(f"{result['status']}: core branches {covered}/{total} ({percent:.2f}%)")
raise SystemExit(0 if result['status'] == 'PASS' else 1)
