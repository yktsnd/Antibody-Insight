"""Independent F19/F20 domain/API review: P07/P08 J07/J08 AC-J07/AC-J08.

These synthetic cases test identity/provenance and persistence, not assay validity.
"""

import copy
import json
import math
import threading
import urllib.error
import urllib.request
from http.cookiejar import CookieJar

import pytest

from test_decisions import decision_bundle
from workspace_app.decisions import decision_review
from workspace_app.domain import ValidationError, new_id
from workspace_app.server import make_server
from workspace_app.storage import Store


@pytest.mark.parametrize('predecessor_kind', ['unknown_decision', 'evidence', 'self'])
def test_bad_predecessor_rolls_back_otherwise_valid_evidence_in_same_import(tmp_path, predecessor_kind):
    bundle, _, _, groups, definition = decision_bundle()
    record = decision_review(bundle, definition)['bundle']['entities'][0]
    record['revision'] = 2
    record['supersedes'] = (new_id('decision') if predecessor_kind == 'unknown_decision'
                            else groups[0][0]['id'] if predecessor_kind == 'evidence'
                            else record['id'])
    extra = {**copy.deepcopy(groups[0][0]), 'id': new_id('evidence'), 'value': 42}
    store = Store(tmp_path / 'atomic.sqlite3')
    store.import_bundle(bundle)
    before = store.bundle(bundle['project']['id'])
    with pytest.raises(ValidationError):
        store.import_bundle({**bundle, 'entities': [extra, record]})
    assert Store(store.path).bundle(bundle['project']['id']) == before
    assert extra['id'] not in {e['id'] for e in store.bundle(bundle['project']['id'])['entities']}


def test_null_anchor_and_explicit_alternate_lot_negative_zero_remain_separate(tmp_path):
    bundle, molecules, materials, groups, definition = decision_bundle()
    anchor = groups[0][0]
    anchor['value'] = None
    index = {e['id']: e for e in bundle['entities']}
    alternate_lot = next(e for e in bundle['entities'] if e['type'] == 'material'
                         and index[e['construct_id']]['molecule_id'] == molecules[0]['id']
                         and e['id'] != materials[0]['id'])
    selected = {**copy.deepcopy(anchor), 'id': new_id('evidence'),
                'subject_id': alternate_lot['id'], 'value': -0.0}
    bundle['entities'].append(selected)
    definition['criteria'][0]['evidence_choices'][molecules[0]['id']] = selected['id']
    result = decision_review(bundle, definition)
    record = result['bundle']['entities'][0]
    row = result['review']['criteria'][0]['rows'][0]
    assert row['status'] == 'observed' and row['subject_id'] == alternate_lot['id']
    assert row['evidence_id'] == selected['id'] and math.copysign(1, row['value']) == -1
    assert anchor in record['evidence_snapshot'] and selected in record['evidence_snapshot']
    assert next(e for e in record['evidence_snapshot'] if e['id'] == anchor['id'])['value'] is None
    store = Store(tmp_path / 'signed.sqlite3')
    store.import_bundle(bundle)
    store.import_bundle(result['bundle'])
    fresh = Store(tmp_path / 'fresh.sqlite3')
    fresh.import_bundle(json.loads(json.dumps(store.bundle(bundle['project']['id']), allow_nan=False)))
    frozen = next(e for e in fresh.bundle(bundle['project']['id'])['entities'] if e['id'] == record['id'])
    assert json.dumps(frozen, sort_keys=True) == json.dumps(record, sort_keys=True)


@pytest.mark.parametrize('changed_value', [True, 1.0])
def test_boolean_or_float_condition_does_not_match_integer_context(changed_value):
    bundle, _, _, groups, definition = decision_bundle()
    for evidence in groups[0]:
        evidence['conditions']['declared_group'] = 1
    groups[0][1]['conditions']['declared_group'] = changed_value
    definition['status'] = 'draft'
    with pytest.raises(ValidationError, match='incompatible'):
        decision_review(bundle, definition)


def test_adding_new_fields_to_legacy_cannot_bypass_required_snapshot_closure(tmp_path):
    bundle, molecules, _, groups, definition = decision_bundle()
    store = Store(tmp_path / 'legacy.sqlite3')
    store.import_bundle(bundle)
    legacy = store.save_shortlist(bundle['project']['id'], [m['id'] for m in molecules],
                                  [groups[0][0]['id']], 'Synthetic legacy selection')
    upgraded = copy.deepcopy(legacy)
    upgraded['id'] = new_id('decision')
    upgraded.update(chosen_candidate_ids=definition['chosen_candidate_ids'],
                    source={'name': 'Synthetic imported decision', 'version': '1'},
                    hypothesis_ids=[], criteria=definition['criteria'])
    # Draft is not a waiver for omitting the other original criterion choices.
    before = store.bundle(bundle['project']['id'])
    with pytest.raises(ValidationError, match='omits'):
        store.import_bundle({**bundle, 'entities': [upgraded]})
    assert store.bundle(bundle['project']['id']) == before


def test_http_rejects_duplicate_choices_underflow_and_wrong_kind_predecessor_without_writes(tmp_path):
    bundle, molecules, _, groups, definition = decision_bundle()
    server = make_server(tmp_path / 'strict-http.sqlite3', 0)
    server.store.import_bundle(bundle)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))
        client.open(server.origin + '/').close()
        bootstrap = json.load(client.open(server.origin + '/api/bootstrap'))
        headers = {'Content-Type': 'application/json', 'Origin': server.origin,
                   'X-CSRF-Token': bootstrap['csrf']}
        before = Store(server.store.path).bundle(bundle['project']['id'])
        request = {'project_id': bundle['project']['id'], 'definition': definition}
        raw = json.dumps(request)
        candidate = json.dumps(molecules[0]['id'])
        duplicate_choice = raw.replace(candidate + ': ', candidate + ': null, ' + candidate + ': ', 1)
        underflow = copy.deepcopy(request)
        underflow['definition']['criteria'][0]['weight'] = '1e-9999'
        wrong_kind = copy.deepcopy(request)
        wrong_kind['definition']['supersedes'] = groups[0][0]['id']
        for body in (duplicate_choice, json.dumps(underflow), json.dumps(wrong_kind)):
            with pytest.raises(urllib.error.HTTPError) as error:
                client.open(urllib.request.Request(server.origin + '/api/decision-review',
                                                  data=body.encode(), headers=headers))
            assert error.value.code == 422
            assert Store(server.store.path).bundle(bundle['project']['id']) == before
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
