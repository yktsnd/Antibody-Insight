"""Independent ADR9 domain/API edges, P06/P08 J06/J08 AC-J06/AC-J08.

Synthetic observations only; no claim of biological assay validation.
"""

import copy
import hashlib
import json
import threading
import urllib.error
import urllib.request
from http.cookiejar import CookieJar

import pytest

from workspace_app.domain import ValidationError, new_id
from workspace_app.experiments import construct_context
from workspace_app.measurements import measurement_preview
from workspace_app.server import make_server
from workspace_app.storage import Store
from test_experiments import experiment_bundle
from test_measurements import csv_text, row
from workspace_app.fixtures import STAMP


def test_opaque_tokens_require_individual_mapping_without_normalization():
    b, _, _, materials = experiment_bundle()
    # Equal-looking external labels and a noncanonical UUID spelling do not
    # authorize binding. Each explicit choice is recorded verbatim.
    refs = ['sample', 'Sample', ' sample ', materials[0]['id'].upper(), '__proto__']
    raw = csv_text([row(ref) for ref in refs])
    sha = hashlib.sha256(raw.encode('utf-8')).hexdigest()
    first = measurement_preview(b, raw, 'exact.csv', {'sample': materials[0]['id']}, mapping_text_sha256=sha)
    assert first['report']['valid_rows'] == 1
    assert set(first['report']['unresolved_refs']) == set(refs[1:])
    mapping = {ref: materials[i % len(materials)]['id'] for i, ref in enumerate(refs)}
    result = measurement_preview(b, raw, 'exact.csv', mapping, mapping_text_sha256=sha)
    assert result['report']['valid_rows'] == len(refs)
    assert [(e['import_origin']['source_material_ref'], e['subject_id']) for e in result['bundle']['entities']] == list(mapping.items())
    # Same references and filename do not make a revised file the approved file.
    with pytest.raises(ValidationError, match='Stale file mapping'):
        measurement_preview(b, raw.replace('1.0', '2.0'), 'exact.csv', mapping, mapping_text_sha256=sha)


def test_import_row_origin_does_not_split_assay_but_source_version_and_kind_do(tmp_path):
    b, m, constructs, materials = experiment_bundle()
    conditions = '{"assay":"SYNTHETIC protocol","dose":1.0}'
    raw = csv_text([row(materials[0]['id'], '2', 'mg/L', STAMP, conditions, 'SYNTHETIC tool', 'v1'),
                    row(materials[1]['id'], '3', 'mg/L', STAMP, conditions, 'SYNTHETIC tool', 'v1'),
                    row(materials[1]['id'], '4', 'mg/L', STAMP, conditions, 'SYNTHETIC tool', 'v2'),
                    row(materials[1]['id'], '5', 'mg/L', STAMP, conditions, 'SYNTHETIC tool', '')],
                   ('conditions_json', 'source_name', 'source_version'))
    preview = measurement_preview(b, raw, 'source.csv', file_source={'name': 'unrelated', 'version': 'never borrow'})
    a, same, changed, unknown = preview['bundle']['entities']
    assert a['import_origin']['record_index'] != same['import_origin']['record_index']
    assert unknown['source'] == {'name': 'SYNTHETIC tool', 'version': None}
    extras = [{**copy.deepcopy(a), 'id': new_id('evidence'), 'kind': kind} for kind in ('computed', 'literature', 'annotation')]
    joined = {**b, 'entities': b['entities'] + preview['bundle']['entities'] + extras}
    store = Store(tmp_path / 'source.sqlite3'); store.import_bundle(joined)
    frozen = Store(store.path).bundle(b['project']['id'])
    result = construct_context(frozen, m['id'], constructs[0]['id'], constructs[1]['id'], a['id'])
    assert set(result['context_evidence_ids']) == {a['id'], same['id']}
    assert changed['id'] not in result['context_evidence_ids']
    assert any(x['evidence_id'] == unknown['id'] for x in result['ineligible'])
    original_kinds = {e['id']: e['kind'] for e in extras}
    assert {e['id']: e['kind'] for e in result['observations'] if e['id'] in original_kinds} == original_kinds
    assert all(any(x['evidence_id'] == e['id'] for x in result['ineligible']) for e in extras if e['kind'] != 'computed')
    computed = next(e for e in extras if e['kind'] == 'computed')
    assert next(c for c in result['cohorts'] if computed['id'] in c['evidence_ids'])['kind'] == 'computed'
    fresh = Store(tmp_path / 'fresh.sqlite3'); fresh.import_bundle(frozen)
    assert json.dumps(fresh.bundle(b['project']['id']), sort_keys=True) == json.dumps(frozen, sort_keys=True)


@pytest.mark.parametrize('mutation', ['origin_float_row', 'unknown_origin_field', 'foreign_subject', 'duplicate_id'])
def test_reviewed_subset_revalidation_is_atomic_even_after_valid_first_row(tmp_path, mutation):
    b, _, _, materials = experiment_bundle()
    raw = csv_text([row(materials[0]['id']), row('unrecognized'), row(materials[1]['id'], '2')])
    reviewed = measurement_preview(b, raw, 'reviewed.csv')
    assert reviewed['report']['valid_rows'] == 2 and len(reviewed['report']['excluded']) == 1
    assert [e['import_origin']['record_index'] for e in reviewed['bundle']['entities']] == [1, 3]
    store = Store(tmp_path / 'atomic.sqlite3'); store.import_bundle(b)
    before = store.bundle(b['project']['id'])
    tampered = copy.deepcopy(reviewed['bundle']); bad = tampered['entities'][1]
    if mutation == 'origin_float_row': bad['import_origin']['record_index'] = 3.0
    elif mutation == 'unknown_origin_field': bad['import_origin']['authenticated_original'] = True
    elif mutation == 'foreign_subject': bad['subject_id'] = new_id('material')
    else: bad['id'] = tampered['entities'][0]['id']
    with pytest.raises(ValidationError): store.import_bundle(tampered)
    assert Store(store.path).bundle(b['project']['id']) == before
    store.import_bundle(reviewed['bundle'])
    assert Store(store.path).bundle(b['project']['id'])['entities'][-2:] == reviewed['bundle']['entities']


def test_live_route_rejects_invalid_encoding_and_foreign_mapping_without_writes(tmp_path):
    server = make_server(tmp_path / 'http.sqlite3', 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    browser = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))
    try:
        browser.open(server.origin + '/').close()
        boot = json.load(browser.open(server.origin + '/api/bootstrap'))
        headers = {'Content-Type': 'application/json', 'Origin': server.origin, 'X-CSRF-Token': boot['csrf']}
        def post(path, payload):
            body = payload if isinstance(payload, bytes) else json.dumps(payload).encode('utf-8')
            return json.load(browser.open(urllib.request.Request(server.origin + path, data=body, headers=headers)))
        b, _, _, materials = experiment_bundle(); post('/api/import', b)
        foreign, _, _, foreign_materials = experiment_bundle()
        # Base fixtures deliberately reuse stable IDs; make the second project
        # genuinely independent before exercising cross-project rejection.
        replacements = {foreign['project']['id']: new_id('project'),
                        **{e['id']: new_id(e['type']) for e in foreign['entities']}}
        def rekey(value):
            if isinstance(value, dict): return {k: rekey(v) for k, v in value.items()}
            if isinstance(value, list): return [rekey(v) for v in value]
            return replacements.get(value, value) if isinstance(value, str) else value
        foreign_target = replacements[foreign_materials[0]['id']]
        foreign = rekey(foreign); post('/api/import', foreign)
        frozen = server.store.bundle(b['project']['id'])
        raw = csv_text([row('external')]); sha = hashlib.sha256(raw.encode()).hexdigest()
        data = {'project_id': b['project']['id'], 'text': raw, 'filename': 'source.csv',
                'mappings': {'external': foreign_target}, 'file_source': None, 'mapping_text_sha256': sha}
        cases = [b'{"project_id":"\xff"}', data, {**data, 'mappings': {'external': materials[0]['id']}, 'mapping_text_sha256': '0' * 64},
                 {**data, 'text': '\ud800', 'mappings': {}}]
        for payload in cases:
            with pytest.raises(urllib.error.HTTPError) as exc: post('/api/measurement-preview', payload)
            assert exc.value.code == 422
            assert server.store.bundle(b['project']['id']) == frozen
        data['mappings'] = {'external': materials[0]['id']}
        approved = post('/api/measurement-preview', data)
        assert approved['report']['valid_rows'] == 1
        assert server.store.bundle(b['project']['id']) == frozen
        post('/api/import', json.loads(approved['serialized_bundle']))
        assert server.store.bundle(b['project']['id'])['entities'][-1]['subject_id'] == materials[0]['id']
    finally:
        server.shutdown(); thread.join(timeout=5); server.server_close()
