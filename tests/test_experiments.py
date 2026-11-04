"""F17/F18 domain: actual Construct/Material identities, not inferred expression effects."""

import copy

import pytest

from workspace_app.domain import ValidationError, new_id, validate_graph
from workspace_app.experiments import construct_context, metadata_preview
from workspace_app.fixtures import STAMP, example_bundle
from workspace_app.storage import Store


def experiment_bundle():
    b=example_bundle(3); m=next(e for e in b['entities'] if e['type']=='molecule')
    constructs=[e for e in b['entities'] if e['type']=='construct' and e['molecule_id']==m['id']]
    old=[e for e in b['entities'] if e['type']=='material' and e['construct_id'] in {c['id'] for c in constructs}]
    third={**old[1],'id':new_id('material'),'lot':'SYNTHETIC third lot','name':'Synthetic independent third material'}
    b['entities'].append(third)
    for i,material in enumerate([*old,third]):
        b['entities'].append({'id':new_id('evidence'),'type':'evidence','project_id':b['project']['id'],'created_at':STAMP,
            'subject_id':material['id'],'kind':'measured','metric':'synthetic_yield','source':{'name':'SYNTHETIC assay; no experiment','version':'1'},
            'timestamp':STAMP,'conditions':None if i==2 else {'assay':'synthetic expression assay','temperature_C':25},
            'value':[0,12,None][i],'unit':'mg/L'})
    return b,m,constructs,[*old,third]


def test_manual_metadata_preview_and_exact_restart_without_invented_experiments(tmp_path):
    b,m,_,_=experiment_bundle(); original=copy.deepcopy(b)
    first=metadata_preview(b,{'type':'construct','molecule_id':m['id'],'name':'Explicit CDS declaration','cds':'GAG','vector':None,'signal_peptide':None})
    construct=first['entities'][0]
    assert construct['source']['name']=='Antibody Insight local researcher metadata entry'
    assert construct['molecule_id']==m['id'] and construct['vector'] is None
    joined={**b,'entities':b['entities']+first['entities']}
    second=metadata_preview(joined,{'type':'material','construct_id':construct['id'],'name':'Explicit material','lot':'supplied lot'})
    assert second['entities'][0]['construct_id']==construct['id']
    assert b==original
    store=Store(tmp_path/'metadata.sqlite3');store.import_bundle(b);store.import_bundle(first);store.import_bundle(second)
    actual=Store(store.path).bundle(b['project']['id'])
    assert actual['entities'][:len(b['entities'])]==original['entities']
    assert actual['entities'][-2:]==first['entities']+second['entities']
    assert all(e['type']!='evidence' for e in actual['entities'][-2:])
    assert all('source' not in e for e in actual['entities'][:len(b['entities'])] if e['type'] in ('construct','material'))
    fresh=Store(tmp_path/'fresh.sqlite3');fresh.import_bundle(actual);assert fresh.bundle(b['project']['id'])==actual


@pytest.mark.parametrize('case',['unknown_molecule','wrong_type','source_spoof','lowercase_cds','missing_lot','foreign_construct'])
def test_metadata_does_not_guess_source_or_missing_id(case):
    b,m,constructs,_=experiment_bundle()
    d={'type':'construct','molecule_id':m['id'],'name':'Must not save','cds':None,'vector':None,'signal_peptide':None}
    if case=='unknown_molecule':d['molecule_id']=new_id('molecule')
    elif case=='wrong_type':d['molecule_id']=constructs[0]['id']
    elif case=='source_spoof':d['source']={'name':'fabricated authenticated person','version':'1'}
    elif case=='lowercase_cds':d['cds']='gaa'
    elif case=='missing_lot':d={'type':'material','construct_id':constructs[0]['id'],'name':'Missing actual lot','lot':''}
    elif case=='foreign_construct':d={'type':'material','construct_id':new_id('construct'),'name':'Unknown construct','lot':'actual supplied lot'}
    original=copy.deepcopy(b)
    with pytest.raises(ValidationError):metadata_preview(b,d)
    assert b==original


def test_two_constructs_three_materials_original_rows_and_no_causality_inference():
    b,m,constructs,materials=experiment_bundle();original=copy.deepcopy(b)
    result=construct_context(b,m['id'],constructs[0]['id'],constructs[1]['id'])
    assert len(result['constructs'])==2 and len(result['materials'])==3
    assert {r['id'] for r in result['materials']}=={r['id'] for r in materials}
    assert result['comparison']['cds']['raw_differences']==[{'raw_dna_index':3,'left':'A','right':'G'}]
    assert result['comparison']['signal_peptide']['status']=='unavailable'
    assert all(e['subject_id'] in {x['id'] for x in materials} for e in result['observations'])
    assert not any(e['subject_id']==m['id'] for e in result['observations'])
    assert any(e['value']==0 for e in result['observations']) and any(e['value'] is None for e in result['observations'])
    yield_cohort=next(c for c in result['cohorts'] if c['metric']=='synthetic_yield')
    assert len(yield_cohort['evidence_ids'])==2
    # Any actual member resolves the same exact context, not an implicit first/latest row.
    chosen=construct_context(b,m['id'],constructs[0]['id'],constructs[1]['id'],yield_cohort['evidence_ids'][-1])
    assert set(chosen['context_evidence_ids'])==set(yield_cohort['evidence_ids'])
    unknown=next(e for e in result['observations'] if e['metric']=='synthetic_yield' and e['conditions'] is None)
    assert any(x['evidence_id']==unknown['id'] for x in result['ineligible'])
    assert b==original


@pytest.mark.parametrize('left,right',[(None,None),(None,'GAG'),('GAA',None)])
def test_unknown_cds_never_appears_identical(left,right):
    b,m,constructs,_=experiment_bundle();constructs[0]['cds']=left;constructs[1]['cds']=right
    result=construct_context(b,m['id'],constructs[0]['id'],constructs[1]['id'])['comparison']['cds']
    assert result['status']=='unavailable' and result['raw_differences']==[]
    assert result['left_length'] is None if left is None else result['left_length']==len(left)


def test_equal_sequences_on_different_molecules_do_not_authorize_foreign_construct_comparison():
    b,m,constructs,_=experiment_bundle();other=next(e for e in b['entities'] if e['type']=='molecule' and e['id']!=m['id'])
    assert other['chains'][0]['sequence']==m['chains'][0]['sequence']
    foreign=next(e for e in b['entities'] if e['type']=='construct' and e['molecule_id']==other['id'])
    with pytest.raises(ValidationError,match='exact Molecule'):construct_context(b,m['id'],constructs[0]['id'],foreign['id'])
    with pytest.raises(ValidationError,match='distinct actual'):construct_context(b,m['id'],constructs[0]['id'],constructs[0]['id'])


def test_different_units_and_unknown_conditions_do_not_share_context():
    b,m,constructs,_=experiment_bundle();base=next(e for e in b['entities'] if e['type']=='evidence' and e['metric']=='synthetic_yield')
    other={**copy.deepcopy(base),'id':new_id('evidence'),'unit':'µg/mL'};b['entities'].append(other)
    validate_graph(b['project'],b['entities'])
    result=construct_context(b,m['id'],constructs[0]['id'],constructs[1]['id'])
    assert len([c for c in result['cohorts'] if c['metric']=='synthetic_yield'])==2
    chosen=construct_context(b,m['id'],constructs[0]['id'],constructs[1]['id'],base['id'])
    assert other['id'] not in chosen['context_evidence_ids']


@pytest.mark.parametrize('field,value',[('record_index',True),('line_number',1),('text_utf8_sha256','A'*64),('importer',None)])
def test_recorded_import_origin_is_strict_and_not_authenticated_file_proof(field,value):
    b,_,_,_=experiment_bundle();e=next(e for e in b['entities'] if e['type']=='evidence')
    e['import_origin']={'file_name':'supplied.csv','text_utf8_sha256':'a'*64,'record_index':1,'line_number':2,
                        'source_material_ref':'original sample token','importer':{'name':'Declared importer','version':None}}
    validate_graph(b['project'],b['entities'])
    e['import_origin'][field]=value
    with pytest.raises(ValidationError):validate_graph(b['project'],b['entities'])
