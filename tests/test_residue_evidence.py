"""F12: explicit source associations, never inferred residue-level measurements."""

import copy

import pytest

from workspace_app.domain import ValidationError
from workspace_app.fixtures import example_bundle
from workspace_app.hypotheses import hypothesis_preview
from workspace_app.storage import Store
from workspace_app.structure_fixtures import structure_bundle
from workspace_app.structures import RESIDUE_FIELDS, parse_structure
from test_hypotheses import definition


def test_optional_note_and_reported_positions_roundtrip_without_rewriting_legacy(tmp_path):
    bundle = example_bundle(); original = copy.deepcopy(bundle)
    evidence = next(e for e in bundle['entities'] if e['type'] == 'evidence' and e['kind'] == 'measured')
    evidence.update(description='Source reports this position; no residue-level measurement implied.',
                    residue_refs=[{'chain_id': 'chain-1', 'sequence_index': 1}])
    store = Store(tmp_path / 'anchors.sqlite3'); store.import_bundle(bundle)
    restored = Store(store.path).bundle(bundle['project']['id'])
    assert restored == bundle
    assert evidence['value'] == next(e for e in original['entities'] if e['id'] == evidence['id'])['value']
    assert all('residue_refs' not in e for e in restored['entities'] if e['type'] == 'evidence' and e['id'] != evidence['id'])
    fresh = Store(tmp_path / 'copy.sqlite3'); fresh.import_bundle(restored)
    assert fresh.bundle(bundle['project']['id']) == restored


@pytest.mark.parametrize('positions', [None, [{'chain_id':'chain-1', 'sequence_index':True}],
    [{'chain_id':'chain-1','sequence_index':0}], [{'chain_id':'wrong','sequence_index':1}],
    [{'chain_id':'chain-1','sequence_index':99999}], [{'chain_id':'chain-1','sequence_index':1}] * 2,
    [{'chain_id':'chain-1','sequence_index':1,'molecule_id':'invented'}]])
def test_invalid_positions_reject_entire_import(tmp_path, positions):
    bundle = example_bundle()
    next(e for e in bundle['entities'] if e['type']=='evidence')['residue_refs'] = positions
    store = Store(tmp_path / 'reject.sqlite3')
    with pytest.raises(ValidationError): store.import_bundle(bundle)
    assert store.projects() == []


def test_anchor_cannot_reach_another_molecule_chain_through_equal_sequence(tmp_path):
    bundle = example_bundle()
    molecules = [e for e in bundle['entities'] if e['type']=='molecule']
    molecules[-1]['chains'][0]['id'] = 'other-only'
    evidence = next(e for e in bundle['entities'] if e['type']=='evidence' and e['kind']=='measured')
    evidence['residue_refs'] = [{'chain_id':'other-only','sequence_index':1}]
    with pytest.raises(ValidationError, match='own molecule'): Store(tmp_path/'wrong.sqlite3').import_bundle(bundle)


def structural_definition():
    bundle = structure_bundle(); result = definition(bundle)
    structure = next(e for e in bundle['entities'] if e['type']=='structure')
    parsed = parse_structure(structure['content'], structure['file_format'])
    residue = next(r for r in parsed['residues'] if r['model']==1 and r['auth_chain']=='T')
    result['structure_refs'] = [{'structure_id':structure['id'],'model':1,'structure_map_id':None,
                                'residue':{'source_key':{k:residue[k] for k in RESIDUE_FIELDS},'altloc':''}}]
    result['residue_refs'] = []
    return bundle, result


def test_source_only_antigen_context_is_preserved_without_sequence_attribution(tmp_path):
    bundle, d = structural_definition(); proposal = hypothesis_preview(bundle, d)
    assert proposal['entities'][0]['residue_refs'] == []
    assert proposal['entities'][0]['structure_refs'] == d['structure_refs']
    store=Store(tmp_path/'source.sqlite3'); store.import_bundle(bundle); store.import_bundle(proposal)
    assert Store(store.path).bundle(bundle['project']['id'])['entities'][-1] == proposal['entities'][0]


@pytest.mark.parametrize('case', ['wrong_model','wrong_alt','wrong_residue','bool_model','wrong_source'])
def test_structural_residue_never_falls_back_to_neighbour(case):
    bundle, d=structural_definition(); ref=d['structure_refs'][0]
    if case=='wrong_model': ref['residue']['source_key']['model']=2
    elif case=='wrong_alt': ref['residue']['altloc']='B'
    elif case=='wrong_residue': ref['residue']['source_key']['auth_number']=9999
    elif case=='bool_model': ref['residue']['source_key']['model']=True
    elif case=='wrong_source': ref['structure_id']=next(e['id'] for e in reversed(bundle['entities']) if e['type']=='structure')
    with pytest.raises(ValidationError): hypothesis_preview(bundle,d)
