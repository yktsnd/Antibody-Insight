"""Independent F21/F22 domain/API edges; synthetic data, no model execution."""

import copy
import hashlib
import json
import threading
import urllib.error
import urllib.request
from http.cookiejar import CookieJar

import pytest

from workspace_app.domain import ValidationError, new_id, validate_graph
from workspace_app.fixtures import STAMP
from workspace_app.predictions import CANONICAL, NATIVE, prediction_preview
from workspace_app.server import make_server
from workspace_app.storage import Store
from workspace_app.structure_fixtures import structure_bundle


def row(subject, **changes):
    return {'kind': 'computed', 'subject_ref': subject, 'metric': 'independent SYNTHETIC property',
            'value': -0.0, 'unit': 'source units',
            'source': {'name': 'SYNTHETIC independent source; no model executed', 'version': None},
            'timestamp': STAMP, 'conditions': {'explicit_parameter': 25.0}, **changes}


def canonical(rows, **extra):
    return json.dumps({'schema_version': CANONICAL, 'records': rows, **extra}, ensure_ascii=False)


def options(structure):
    return {'structure_id': structure['id'], 'model': 1,
            'source': {'name': 'SYNTHETIC independent sample assertion; no model executed', 'version': None},
            'timestamp': STAMP, 'conditions': None}


def subjects_fixture():
    bundle = structure_bundle()
    molecules = [e for e in bundle['entities'] if e['type'] == 'molecule']
    structures = [e for e in bundle['entities'] if e['type'] == 'structure']
    for record in [*molecules, *structures]:
        record['name'] = 'Exactly the same visible label'
    assert molecules[0]['chains'] == molecules[1]['chains']
    roles = []
    for molecule, structure in zip(molecules, structures):
        common = {'project_id': bundle['project']['id'], 'created_at': STAMP, 'name': molecule['name']}
        construct = {**common, 'id': new_id('construct'), 'type': 'construct', 'molecule_id': molecule['id'],
                     'cds': None, 'vector': None, 'signal_peptide': None}
        material = {**common, 'id': new_id('material'), 'type': 'material', 'construct_id': construct['id'], 'lot': 'same-lot'}
        bundle['entities'].extend([construct, material])
        roles.append([molecule, construct, material, structure])
    validate_graph(bundle['project'], bundle['entities'])
    return bundle, structures, roles


def test_four_direct_subject_roles_and_explicit_aliases_never_collapse_equal_names_sequences(tmp_path):
    bundle, _, roles = subjects_fixture()
    actual = [entity for group in roles for entity in group]
    tokens = ['__proto__', 'constructor', '/', '~', '<img src=x onerror=alert(1)>', ' α ', 'same-lot', 'same-label']
    raw = '\ufeff' + canonical([row(token, value=i) for i, token in enumerate(tokens)]).replace(', ', ',\r\n ')
    bindings = dict(zip(tokens, [entity['id'] for entity in actual]))
    digest = hashlib.sha256(raw.encode('utf-8')).hexdigest()
    result = prediction_preview(bundle, raw, 'exact-source.json', CANONICAL, bindings, {}, digest)
    source, *evidence = result['bundle']['entities']
    assert [e['subject_id'] for e in evidence] == [entity['id'] for entity in actual]
    assert [e['value'] for e in evidence] == list(range(8))
    assert len(set(e['subject_id'] for e in evidence)) == 8
    assert source['content'] == raw and source['bindings'] == bindings
    direct = prediction_preview(bundle, canonical([row(entity['id'], value=i) for i, entity in enumerate(actual)]),
                                'direct-typed-subjects.json', CANONICAL, {}, {})
    assert [e['subject_id'] for e in direct['bundle']['entities'][1:]] == [entity['id'] for entity in actual]
    store = Store(tmp_path / 'source.sqlite3')
    store.import_bundle(bundle)
    store.import_bundle(result['bundle'])
    saved = store.bundle(bundle['project']['id'])
    fresh = Store(tmp_path / 'fresh.sqlite3')
    fresh.import_bundle({**saved, 'entities': list(reversed(saved['entities']))})
    assert {e['id']: json.dumps(e, sort_keys=True) for e in saved['entities']} == {
        e['id']: json.dumps(e, sort_keys=True) for e in fresh.bundle(bundle['project']['id'])['entities']}


@pytest.mark.parametrize('change', ['evidence_subject', 'source_target', 'source_model', 'source_conditions'])
def test_two_same_model1_sources_cannot_swap_one_side_without_rejection(tmp_path, change):
    bundle, structures, _ = subjects_fixture()
    raw = '{"iptm": 0.75, "has_clash": false}'
    first = prediction_preview(bundle, raw, 'identical-summary.json', NATIVE, {}, options(structures[0]))['bundle']
    second = prediction_preview(bundle, raw, 'identical-summary.json', NATIVE, {}, options(structures[1]))['bundle']
    incoming = {**first, 'entities': [*first['entities'], *second['entities']]}
    validate_graph(bundle['project'], [*bundle['entities'], *incoming['entities']])
    source, evidence = incoming['entities'][:2]
    if change == 'evidence_subject':
        evidence['subject_id'] = structures[1]['id']
    elif change == 'source_target':
        source['options']['structure_id'] = structures[1]['id']
    elif change == 'source_model':
        source['options']['model'] = 2
    else:
        source['options']['conditions'] = {'unreported': 'new value'}
    store = Store(tmp_path / 'same-model.sqlite3')
    store.import_bundle(bundle)
    with pytest.raises(ValidationError):
        store.import_bundle(incoming)
    assert store.bundle(bundle['project']['id']) == bundle


def test_unknown_fields_scan_all_source_and_residue_paths_but_keep_conditions_opaque():
    bundle, structures, _ = subjects_fixture()
    target = structures[0]['id']
    rows = [row(target), row('unmapped'), row(target)]
    rows[0]['source']['a/b~c'] = 1
    rows[1]['residue_refs'] = [{'chain_id': 'H', 'sequence_index': 1, 'x/y~z': False}]
    rows[2]['residue_refs'] = [{'chain_id': 'L', 'sequence_index': 1, 'later': None}]
    rows[2]['new/key'] = 2
    with pytest.raises(ValidationError) as exc:
        prediction_preview(bundle, canonical(rows, **{'root/~': 3}), 'unknown.json', CANONICAL, {}, {})
    assert exc.value.details == ['/records/0/source/a~1b~0c', '/records/1/residue_refs/0/x~1y~0z',
                                 '/records/2/new~1key', '/records/2/residue_refs/0/later', '/root~1~0']
    conditions = {'arbitrary/~key': {'__proto__': [True, None, 25.0, -0.0]}}
    good = prediction_preview(bundle, canonical([row(target, conditions=conditions)]), 'conditions.json', CANONICAL, {}, {})
    assert good['bundle']['entities'][1]['conditions'] == conditions


@pytest.mark.parametrize('change', ['reverse_allocation_missing', 'unallocated_origin', 'noncomputed', 'wrong_project', 'extra_import_origin'])
def test_bidirectional_allocation_and_origin_kind_reject_direct_awx(tmp_path, change):
    bundle, structures, _ = subjects_fixture()
    incoming = prediction_preview(bundle, canonical([row(structures[0]['id']), row(structures[0]['id'])]),
                                  'twins.json', CANONICAL, {}, {})['bundle']
    source, first, second = incoming['entities']
    if change == 'reverse_allocation_missing':
        source['allocations'].pop()
    elif change == 'unallocated_origin':
        clone = copy.deepcopy(second)
        clone['id'] = new_id('evidence')
        incoming['entities'].append(clone)
    elif change == 'noncomputed':
        first['kind'] = 'annotation'
    elif change == 'wrong_project':
        source['project_id'] = new_id('project')
    else:
        first['import_origin'] = {'file_name': 'unrelated.csv', 'text_utf8_sha256': 'a' * 64,
                                  'record_index': 1, 'line_number': 2, 'source_material_ref': 'token',
                                  'importer': {'name': 'declared importer', 'version': None}}
    store = Store(tmp_path / 'allocations.sqlite3')
    store.import_bundle(bundle)
    with pytest.raises(ValidationError):
        store.import_bundle(incoming)
    assert store.bundle(bundle['project']['id']) == bundle


@pytest.mark.parametrize('value', ['mol_\u0000', 'mol_NOT-A-UUID', 'con_not-a-uuid', 'prf_not-a-uuid', 'evd_not-a-uuid'])
def test_reserved_malformed_non_subject_prefixes_are_never_explicit_aliases(value):
    bundle, structures, _ = subjects_fixture()
    raw = canonical([row(value)])
    with pytest.raises(ValidationError):
        prediction_preview(bundle, raw, 'reserved.json', CANONICAL, {value: structures[0]['id']}, {}, hashlib.sha256(raw.encode()).hexdigest())


def test_api_rejects_invalid_utf8_and_each_authentication_boundary_without_writes(tmp_path):
    server = make_server(tmp_path / 'api.sqlite3', 0)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        browser = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))
        browser.open(server.origin + '/').close()
        with browser.open(server.origin + '/api/bootstrap') as response:
            boot = json.load(response)
        bundle, structures, _ = subjects_fixture()
        server.store.import_bundle(bundle)
        headers = {'Content-Type': 'application/json', 'Origin': server.origin, 'X-CSRF-Token': boot['csrf']}
        data = {'project_id': bundle['project']['id'], 'text': '{"iptm":0.8}', 'filename': 'source.json',
                'file_format': NATIVE, 'bindings': {}, 'options': options(structures[0]), 'bindings_text_sha256': None}

        def reject(payload, request_headers, status, client=browser):
            request = urllib.request.Request(server.origin + '/api/prediction-preview', data=payload, headers=request_headers)
            with pytest.raises(urllib.error.HTTPError) as exc:
                client.open(request)
            assert exc.value.code == status
            assert server.store.bundle(bundle['project']['id']) == bundle

        valid = json.dumps(data).encode('utf-8')
        reject(b'\xff\xfe{"invalid":"UTF8"}', headers, 422)
        reject(valid, {**headers, 'Origin': 'https://unrelated.invalid'}, 403)
        reject(valid, {**headers, 'X-CSRF-Token': 'wrong'}, 403)
        reject(valid, headers, 403, urllib.request.build_opener())
        reject(valid, {**headers, 'Content-Type': 'text/plain'}, 415)
        reject(b'', {**headers, 'Content-Length': str(32 * 1024 * 1024 + 1)}, 422)
        with browser.open(urllib.request.Request(server.origin + '/api/prediction-preview', data=valid, headers=headers)) as response:
            reviewed = json.load(response)
        assert reviewed['report']['source_files_added'] == 1 and reviewed['report']['valid_rows'] == 1
        assert server.store.bundle(bundle['project']['id']) == bundle
    finally:
        server.shutdown()
        worker.join(timeout=5)
        server.server_close()
