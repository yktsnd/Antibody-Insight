"""F14/F15 domain slice only; full J05 UI/independent acceptance is still pending."""

import copy

import pytest

from workspace_app.assembly import composition_context, composition_preview
from workspace_app.domain import ValidationError, new_id
from workspace_app.fixtures import composition_bundle, example_bundle
from workspace_app.storage import Store


def definition(bundle):
    units = [e for e in bundle['entities'] if e['type'] == 'binding_unit']
    def part(unit, key):
        chain = unit['chains'][0]
        return {'id': key, 'role': 'declared source segment', 'source': {'kind': 'binding_unit', 'binding_unit_id': unit['id'],
                'chain_id': chain['id'], 'start': 1, 'end': len(chain['sequence'])}}
    return {'name': 'Synthetic independently declared composition', 'external_id': 'COMPOSED-NEW', 'format': 'declared synthetic multichain',
            'parent_id': None, 'reason': None, 'note': 'Researcher design annotation; physical assembly is unverified.',
            'chains': [{'id': 'tandem', 'role': 'declared tandem', 'copies': 2, 'components': [part(units[0], 'part-A'),
                {'id': 'linker', 'role': 'explicit linker', 'source': {'kind': 'sequence', 'sequence': 'GGS'}}, part(units[1], 'part-B')]},
                {'id': 'partner', 'role': 'independent declared fragment', 'copies': 1, 'components': [
                    {'id': 'independent', 'role': 'explicit fragment', 'source': {'kind': 'sequence', 'sequence': 'ACDE'}}]}],
            'connections': [{'left': {'chain_id': 'tandem', 'component_id': 'part-A'},
                             'right': {'chain_id': 'partner', 'component_id': 'independent'}, 'kind': 'declared_pairing'}]}


def test_exact_sources_order_copies_annotation_and_restart_without_inheritance(tmp_path):
    bundle = composition_bundle(); original = copy.deepcopy(bundle); request = definition(bundle); request_copy = copy.deepcopy(request)
    result = composition_preview(bundle, request); molecule, note = result['entities']
    parts = molecule['component_graph']['chains'][0]['components']
    assert molecule['chains'][0]['sequence'] == parts[0]['sequence'] + 'GGS' + parts[2]['sequence']
    assert [p['id'] for p in parts] == ['part-A', 'linker', 'part-B']
    assert parts[0]['sequence'] == parts[2]['sequence']
    assert parts[0]['origin']['binding_unit_id'] != parts[2]['origin']['binding_unit_id']
    assert [c['copies'] for c in molecule['component_graph']['chains']] == [2, 1]
    assert note['kind'] == 'annotation' and note['subject_id'] == molecule['id'] and note['value'] is None
    assert note['description'] == request['note'] and note['source']['name'] == 'Antibody Insight local researcher composition entry'
    assert bundle == original and request == request_copy
    store = Store(tmp_path / 'design.sqlite3'); store.import_bundle(bundle); store.import_bundle(result)
    restored = Store(store.path).bundle(bundle['project']['id'])
    assert restored['entities'][:len(original['entities'])] == original['entities']
    assert restored['entities'][-2:] == result['entities']
    assert not any(e['type'] in ('construct', 'material', 'structure', 'residue_map') and e.get('molecule_id') == molecule['id'] for e in restored['entities'])
    assert not any(e['type'] == 'evidence' and e['kind'] == 'measured' and e['subject_id'] == molecule['id'] for e in restored['entities'])
    fresh = Store(tmp_path / 'fresh.sqlite3'); fresh.import_bundle(restored); assert fresh.bundle(bundle['project']['id']) == restored


@pytest.mark.parametrize('case', ['no_chains', 'duplicate_chain', 'empty_components', 'missing_copies', 'boolean_copies', 'zero_copies',
    'missing_sequence', 'empty_sequence', 'unknown_unit', 'wrong_type', 'wrong_chain', 'boolean_start', 'float_start', 'range',
    'spoof_sequence', 'duplicate_component', 'dangling_connection', 'new_parent_reason', 'parent_without_reason', 'unknown_parent'])
def test_incomplete_recipe_and_wrong_sources_never_autocomplete_or_save(tmp_path, case):
    bundle = composition_bundle(); d = definition(bundle); chain = d['chains'][0]; source = chain['components'][0]['source']
    if case == 'no_chains': d['chains'] = []
    elif case == 'duplicate_chain': d['chains'].append(copy.deepcopy(chain))
    elif case == 'empty_components': chain['components'] = []
    elif case == 'missing_copies': del chain['copies']
    elif case == 'boolean_copies': chain['copies'] = True
    elif case == 'zero_copies': chain['copies'] = 0
    elif case == 'missing_sequence': del chain['components'][1]['source']['sequence']
    elif case == 'empty_sequence': chain['components'][1]['source']['sequence'] = ''
    elif case == 'unknown_unit': source['binding_unit_id'] = new_id('binding_unit')
    elif case == 'wrong_type': source['binding_unit_id'] = next(e['id'] for e in bundle['entities'] if e['type'] == 'molecule')
    elif case == 'wrong_chain': source['chain_id'] = 'not-this-chain'
    elif case == 'boolean_start': source['start'] = True
    elif case == 'float_start': source['start'] = 1.0
    elif case == 'range': source['end'] = 99999
    elif case == 'spoof_sequence': chain['components'][0]['sequence'] = 'FAKE'
    elif case == 'duplicate_component': chain['components'][1]['id'] = chain['components'][0]['id']
    elif case == 'dangling_connection': d['chains'].pop()
    elif case == 'new_parent_reason': d['reason'] = 'Must not be silently discarded'
    elif case == 'parent_without_reason': d['parent_id'] = next(e['id'] for e in bundle['entities'] if e['type'] == 'molecule')
    elif case == 'unknown_parent': d.update(parent_id=new_id('molecule'), reason='Explicit unavailable source')
    store = Store(tmp_path / 'atomic.sqlite3'); store.import_bundle(bundle)
    with pytest.raises(ValidationError): composition_preview(bundle, d)
    assert store.bundle(bundle['project']['id']) == bundle


def test_explicit_parent_exact_composition_lineage_and_no_metadata_only_change():
    bundle = composition_bundle(); d = definition(bundle)
    parent = next(e for e in bundle['entities'] if e['type'] == 'molecule' and 'component_graph' in e)
    d.update(parent_id=parent['id'], reason='Explicitly compare another source layout', note=None)
    molecule, lineage = composition_preview(bundle, d)['entities']
    assert lineage['parent_id'] == parent['id'] and lineage['child_id'] == molecule['id']
    assert lineage['change_set']['before']['component_graph'] == parent['component_graph']
    assert lineage['change_set']['after']['component_graph'] == molecule['component_graph']
    d.update(format=parent['format'], chains=[])
    for c in parent['chains']:
        graph_chain = next(g for g in parent['component_graph']['chains'] if g['chain_id'] == c['id'])
        parts = []
        for component in graph_chain['components']:
            source = {'kind': 'binding_unit', **component['origin']} if component['origin'] is not None else {'kind': 'sequence', 'sequence': component['sequence']}
            parts.append({'id': component['id'], 'role': component['role'], 'source': source})
        d['chains'].append({'id': c['id'], 'role': c['role'], 'copies': graph_chain['copies'], 'components': parts})
    d['connections'] = copy.deepcopy(parent['component_graph']['connections'])
    with pytest.raises(ValidationError, match='actual composition change'): composition_preview(bundle, d)


def test_partial_paired_usage_is_per_source_instance_not_complete_unit_or_valency():
    bundle = composition_bundle(); units = [e for e in bundle['entities'] if e['type'] == 'binding_unit']
    units[0]['topology'] = 'paired'; units[0]['chains'].append({'id': 'explicit-partner', 'role': 'declared partner', 'sequence': 'GGC', 'origin': None})
    d = definition(bundle); source = d['chains'][0]['components'][0]['source']; source['end'] -= 1
    result = composition_preview(bundle, d); combined = {**bundle, 'entities': bundle['entities'] + result['entities']}
    context = composition_context(combined, result['entities'][0]['id'])
    unit_context = next(u for u in context['source_units'] if u['unit']['id'] == units[0]['id'])
    first, absent = unit_context['chains']
    assert first['full_source_chain_occurrences'] == 0 and first['usages'][0]['copies'] == 2
    assert first['usages'][0]['is_full_source_chain'] is False
    assert absent['chain_id'] == 'explicit-partner' and absent['usages'] == []
    assert all(c['id'] != 'explicit-partner' for c in result['entities'][0]['chains'])
    assert all('valency' not in u and 'complete_units' not in u for u in context['source_units'])
    context['molecule']['chains'][0]['sequence'] = 'CHANGED'
    assert combined['entities'][-2]['chains'][0]['sequence'] != 'CHANGED'


def test_declared_connection_cycle_is_not_a_provenance_cycle():
    bundle = composition_bundle(); d = definition(bundle); ids = ['part-A', 'linker', 'part-B']
    d['connections'] = [{'left': {'chain_id': 'tandem', 'component_id': ids[i]},
                         'right': {'chain_id': 'tandem', 'component_id': ids[(i + 1) % 3]}, 'kind': 'declared_pairing'} for i in range(3)]
    assert composition_preview(bundle, d)['entities'][0]['component_graph']['connections'] == d['connections']


def test_undefined_composition_is_not_filled_from_format_or_equal_sequences():
    bundle = example_bundle(); m = next(e for e in bundle['entities'] if e['type'] == 'molecule')
    context = composition_context(bundle, m['id'])
    assert context['status'] == 'undefined' and context['source_units'] == []
    assert 'component_graph' not in context['molecule']
