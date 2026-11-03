"""Independent F12 exact-null source and immutable legacy Evidence checks."""

import copy
import hashlib

import pytest

from workspace_app.domain import ValidationError
from workspace_app.fixtures import example_bundle
from workspace_app.hypotheses import hypothesis_preview
from workspace_app.storage import Store
from workspace_app.structures import RESIDUE_FIELDS, parse_structure
from observation_review_fixture import boundary_bundle


def definition(bundle, model=1):
    molecule,structure=bundle['entities'][:2]
    residue=next(r for r in parse_structure(structure['content'],'mmcif')['residues'] if r['auth_chain']=='H' and r['auth_number']==4)
    return {'text':'Synthetic unknown alternate observation, not a scientific conclusion.',
            'question':'Obtain an independently resolved source before assigning a sequence effect.',
            'limitations':None,'molecule_ids':[molecule['id']],'related_evidence_ids':[],'lineage_ids':[],'residue_refs':[],
            'structure_refs':[{'structure_id':structure['id'],'model':model,'structure_map_id':None,
                               'residue':{'source_key':{field:residue[field] for field in RESIDUE_FIELDS},'altloc':None}}]}


@pytest.mark.parametrize('case',['segment_blank','number_float','model_bool','model_float','wrong_name','wrong_alt'])
def test_actual_null_and_typed_source_key_cannot_be_normalized_to_neighbour(case):
    bundle=boundary_bundle(); d=definition(bundle); residue=d['structure_refs'][0]['residue']
    assert residue['source_key']['segment'] is None
    if case=='segment_blank': residue['source_key']['segment']=''
    elif case=='number_float': residue['source_key']['auth_number']=4.0
    elif case=='model_bool': residue['source_key']['model']=True
    elif case=='model_float': residue['source_key']['model']=1.0
    elif case=='wrong_name': residue['source_key']['residue_name']='GLY'
    elif case=='wrong_alt': residue['altloc']='B'
    with pytest.raises(ValidationError): hypothesis_preview(bundle,d)


def test_unknown_source_model_alt_occupancy_and_b_fields_remain_null_after_save_restart(tmp_path):
    bundle=boundary_bundle();structure=bundle['entities'][1]
    structure['content']='\n'.join(line.rsplit(' ',1)[0]+' ?' if line.startswith(('ATOM ','HETATM ')) else line for line in structure['content'].splitlines())+'\n'
    structure['sha256']=hashlib.sha256(structure['content'].encode()).hexdigest();bundle['entities']=bundle['entities'][:2]
    d=definition(bundle,None); record=hypothesis_preview(bundle,d)
    assert record['entities'][0]['structure_refs'][0]['residue']['source_key']['model'] is None
    assert record['entities'][0]['structure_refs'][0]['residue']['altloc'] is None
    store=Store(tmp_path/'unknown.sqlite3');store.import_bundle(bundle);store.import_bundle(record)
    restored=Store(store.path).bundle(bundle['project']['id'])
    parsed=parse_structure(restored['entities'][1]['content'],'mmcif')
    assert parsed['models']==[None]
    assert all(a['occupancy'] is None and a['b_value'] is None for a in parsed['atoms'])
    assert restored['entities'][-1]==record['entities'][0]
    d['structure_refs'][0]['model']=1
    with pytest.raises(ValidationError): hypothesis_preview(bundle,d)


def test_source_reported_measured_anchor_retains_whole_material_zero_and_legacy_absence(tmp_path):
    bundle=example_bundle();legacy=copy.deepcopy(bundle)
    evidence=next(e for e in bundle['entities'] if e['type']=='evidence' and e['kind']=='measured' and e['value']==0)
    evidence.update(description='<img src=x onerror="invent()"> Source note; no residue-localized measurement.',residue_refs=[{'chain_id':'chain-1','sequence_index':1}])
    store=Store(tmp_path/'legacy.sqlite3');store.import_bundle(bundle);restored=Store(store.path).bundle(bundle['project']['id'])
    assert restored==bundle
    saved=next(e for e in restored['entities'] if e['id']==evidence['id'])
    assert saved['kind']=='measured' and saved['value']==0 and saved['subject_id'].startswith('mat_')
    for before,after in zip(legacy['entities'],restored['entities']):
        if before['id']!=evidence['id']: assert after==before
    fresh=Store(tmp_path/'fresh.sqlite3');fresh.import_bundle(restored)
    assert fresh.bundle(bundle['project']['id'])==restored
