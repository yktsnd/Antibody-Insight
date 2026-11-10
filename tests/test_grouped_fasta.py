"""Explicit ordinary-file registration, distinct from prepared awx examples."""

import copy
import hashlib

import pytest

from workspace_app.adapters import new_project, preview
from workspace_app.domain import ValidationError, validate_graph
from workspace_app.fixtures import research_example_bundle
from workspace_app.storage import Store


RAW = '>uninterpreted header\nEVQL\n>uninterpreted header\nDIQM\n'


def options(raw=RAW):
    return {'assignments': [{'record_index': i, 'external_id': 'declared-Fab', 'chain_id': chain, 'role': role}
                            for i, (chain, role) in enumerate([('H', 'heavy'), ('L', 'light')])],
            'text_sha256': hashlib.sha256(raw.encode()).hexdigest(), 'molecular_format': 'declared Fab'}


def test_plain_fasta_remains_unpaired_and_grouped_preview_does_not_save(tmp_path):
    project = new_project('Local antibody study', 'Inspect actual chains')
    initial = preview(RAW, 'fasta_grouped', 'own.fa', project,
                      sequence_options={'assignments': None, 'text_sha256': None, 'molecular_format': 'unspecified'})
    assert initial['bundle']['entities'] == [] and len(initial['report']['sequence_records']) == 2
    store = Store(tmp_path / 'test.sqlite3')
    result = preview(RAW, 'fasta_grouped', 'own.fa', project, sequence_options=options())
    assert store.projects() == []
    molecule, = result['bundle']['entities']
    assert [c['id'] for c in molecule['chains']] == ['H', 'L']
    assert [c['sequence'] for c in molecule['chains']] == ['EVQL', 'DIQM']
    assert 'record 1, line 1' in molecule['source']['name'] and 'record 2, line 3' in molecule['source']['name']
    assert molecule['source']['version'] == 'sha256:' + hashlib.sha256(RAW.encode()).hexdigest()
    store.import_bundle(result['bundle'])
    assert Store(store.path).bundle(project['id']) == result['bundle']
    with pytest.raises(ValidationError, match='Duplicate internal ID'): store.import_bundle(result['bundle'])
    raw = RAW.replace('>uninterpreted header', '>H', 1).replace('>uninterpreted header', '>L', 1)
    unpaired = preview(raw, 'fasta', 'own.fa', new_project('Other', 'Unpaired'))
    assert len(unpaired['bundle']['entities']) == 2
    assert all(len(m['chains']) == 1 for m in unpaired['bundle']['entities'])


@pytest.mark.parametrize('case', ['duplicate_chain', 'duplicate_record', 'missing_record', 'boolean_index',
                                 'stale_text', 'blank_role', 'unknown_option', 'invalid_sequence'])
def test_grouping_rejects_ambiguous_incomplete_or_stale_assignments(case):
    opts = options(); raw = RAW
    if case == 'duplicate_chain': opts['assignments'][1]['chain_id'] = 'H'
    elif case == 'duplicate_record': opts['assignments'][1]['record_index'] = 0
    elif case == 'missing_record': opts['assignments'].pop()
    elif case == 'boolean_index': opts['assignments'][0]['record_index'] = False
    elif case == 'stale_text': raw += '\n'
    elif case == 'blank_role': opts['assignments'][0]['role'] = ''
    elif case == 'unknown_option': opts['auto_pair'] = True
    elif case == 'invalid_sequence': raw = RAW.replace('DIQM', 'DI*M')
    with pytest.raises(ValidationError):
        preview(raw, 'fasta_grouped', 'own.fa', new_project('Test', 'Negative'), sequence_options=opts)


def test_identical_chains_do_not_collapse_distinct_declared_candidates():
    opts = options(); opts['assignments'][1]['external_id'] = 'another-Fab'
    raw = RAW.replace('DIQM', 'EVQL'); opts['text_sha256'] = hashlib.sha256(raw.encode()).hexdigest()
    result = preview(raw, 'fasta_grouped', 'own.fa', new_project('Test', 'Identity'), sequence_options=opts)
    assert len(result['bundle']['entities']) == 2
    assert len({e['id'] for e in result['bundle']['entities']}) == 2


def test_research_example_has_paired_candidates_actual_material_paths_and_missingness(tmp_path):
    bundle = research_example_bundle(); original = copy.deepcopy(bundle)
    index = validate_graph(bundle['project'], bundle['entities'])
    molecules = [e for e in index.values() if e['type'] == 'molecule']
    assert len(molecules) == 2 and all({c['id'] for c in e['chains']} == {'H', 'L'} for e in molecules)
    measured = [e for e in index.values() if e['type'] == 'evidence' and e['kind'] == 'measured']
    assert len(measured) == 5 and any(e['value'] is None for e in measured)
    assert all(index[e['subject_id']]['type'] == 'material' for e in measured)
    assert any(e['conditions'].get('temperature_C') == 37 for e in measured)
    assert bundle['project']['data_class'] == 'synthetic_fixture'
    store = Store(tmp_path / 'example.sqlite3'); store.import_bundle(bundle)
    assert store.bundle(bundle['project']['id']) == original
