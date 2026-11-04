"""Independent bounded native-parameter transport checks, synthetic only."""

import copy
import json
import math
import threading
import urllib.request
from http.cookiejar import CookieJar

import pytest

from workspace_app.domain import ValidationError
from workspace_app.fixtures import STAMP
from workspace_app.predictions import CANONICAL, NATIVE, prediction_preview
from workspace_app.server import make_server
from workspace_app.storage import Store
from workspace_app.structure_fixtures import structure_bundle


@pytest.fixture
def native_input():
    bundle = structure_bundle()
    structure = next(e for e in bundle['entities'] if e['type'] == 'structure')
    options = {'structure_id': structure['id'], 'model': 1,
               'source': {'name': 'SYNTHETIC DTO check; no model executed', 'version': None},
               'timestamp': STAMP, 'conditions': None}
    return bundle, options


def test_literal_parameter_json_preserves_types_sign_and_caller_input(native_input, tmp_path):
    bundle, options = native_input
    literal = '{"integer":25,"floating":25.0,"negative_zero":-0.0,"nested":[1,1.0,-0.0,true,null]}'
    options['conditions'] = literal
    before = copy.deepcopy(options)
    result = prediction_preview(bundle, '{"iptm":0.7}', 'summary.json', NATIVE, {}, options)
    source, evidence = result['bundle']['entities']
    assert options == before and options['conditions'] == literal
    conditions = source['options']['conditions']
    assert type(conditions['integer']) is int and type(conditions['floating']) is float
    assert math.copysign(1, conditions['negative_zero']) == -1
    assert [type(v) for v in conditions['nested']] == [int, float, float, bool, type(None)]
    assert math.copysign(1, conditions['nested'][2]) == -1
    assert evidence['conditions'] == {**conditions, 'structure_model': 1}
    store = Store(tmp_path / 'source.sqlite3')
    store.import_bundle(bundle)
    store.import_bundle(result['bundle'])
    fresh = Store(tmp_path / 'fresh.sqlite3')
    fresh.import_bundle(json.loads(json.dumps(store.bundle(bundle['project']['id']))))
    restored = next(e for e in fresh.bundle(bundle['project']['id'])['entities'] if e['type'] == 'prediction_file')
    assert json.dumps(restored, sort_keys=True) == json.dumps(source, sort_keys=True)


@pytest.mark.parametrize('literal', ['{', '{"x":1,"x":2}', '{"x":NaN}', '{"x":1e999}',
                                   '{"x":1e-999}', '[]', 'true', '25.0', '"{}"',
                                   '{"structure_model":1.0}', '{"structure_model":-0.0}'])
def test_malformed_wrong_shape_and_reserved_model_literals_reject(native_input, literal):
    bundle, options = native_input
    options['conditions'] = literal
    before = copy.deepcopy(options)
    with pytest.raises(ValidationError):
        prediction_preview(bundle, '{"iptm":0.7}', 'summary.json', NATIVE, {}, options)
    assert options == before


def test_null_dto_is_allowed_but_persisted_string_or_canonical_options_are_rejected(native_input, tmp_path):
    bundle, options = native_input
    options['conditions'] = 'null'
    result = prediction_preview(bundle, '{"iptm":0.7}', 'summary.json', NATIVE, {}, options)
    source, evidence = result['bundle']['entities']
    assert source['options']['conditions'] is None and evidence['conditions'] == {'structure_model': 1}
    store = Store(tmp_path / 'direct.sqlite3')
    store.import_bundle(bundle)
    source['options']['conditions'] = 'null'
    with pytest.raises(ValidationError):
        store.import_bundle(result['bundle'])
    assert store.bundle(bundle['project']['id']) == bundle
    with pytest.raises(ValidationError):
        prediction_preview(bundle, '{"schema_version":"computed-evidence/1","records":[]}',
                           'canonical.json', CANONICAL, {}, {'conditions': '{"x":25.0}'})


def test_http_parameter_literal_is_typed_in_authoritative_bundle(native_input, tmp_path):
    bundle, options = native_input
    options['conditions'] = '{"integer":25,"floating":25.0,"negative_zero":-0.0}'
    server = make_server(tmp_path / 'http.sqlite3', 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        browser = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))
        browser.open(server.origin + '/').close()
        with browser.open(server.origin + '/api/bootstrap') as response:
            boot = json.load(response)
        server.store.import_bundle(bundle)
        body = {'project_id': bundle['project']['id'], 'text': '{"iptm":0.7}', 'filename': 'summary.json',
                'file_format': NATIVE, 'bindings': {}, 'options': options, 'bindings_text_sha256': None}
        headers = {'Content-Type': 'application/json', 'Origin': server.origin, 'X-CSRF-Token': boot['csrf']}
        with browser.open(urllib.request.Request(server.origin + '/api/prediction-preview',
                          data=json.dumps(body).encode('utf-8'), headers=headers)) as response:
            reviewed = json.load(response)
        authoritative = json.loads(reviewed['serialized_bundle'])
        source, evidence = authoritative['entities']
        for conditions in [source['options']['conditions'], evidence['conditions']]:
            assert type(conditions['integer']) is int and type(conditions['floating']) is float
            assert math.copysign(1, conditions['negative_zero']) == -1
        assert server.store.bundle(bundle['project']['id']) == bundle
        with browser.open(urllib.request.Request(server.origin + '/api/import',
                          data=reviewed['serialized_bundle'].encode('utf-8'), headers=headers)) as response:
            assert json.load(response)['imported'] == 2
        stored = next(e for e in server.store.bundle(bundle['project']['id'])['entities'] if e['id'] == evidence['id'])
        assert json.dumps(stored, sort_keys=True) == json.dumps(evidence, sort_keys=True)
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
