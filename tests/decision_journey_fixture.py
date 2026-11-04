"""Clearly synthetic P07 comparison sources and a proposed explanation."""

import copy

from test_decisions import decision_bundle
from workspace_app.domain import new_id, validate_graph
from workspace_app.fixtures import STAMP


def decision_journey_bundle():
    bundle,molecules,materials,groups,_=decision_bundle()
    index={e['id']:e for e in bundle['entities']}
    alternate=next(e for e in bundle['entities'] if e['type']=='material' and e['id']!=materials[0]['id']
                   and index[e['construct_id']]['molecule_id']==molecules[0]['id'])
    repeat={**copy.deepcopy(groups[0][0]),'id':new_id('evidence'),'subject_id':alternate['id'],'value':2,
            'description':'SYNTHETIC alternative lot observation; no replicate independence inferred'}
    note={**copy.deepcopy(groups[0][0]),'id':new_id('evidence'),'kind':'annotation','metric':'decision_source_note',
          'value':None,'unit':None,'conditions':None,'description':'SYNTHETIC qualitative source note; no biological inference'}
    hypothesis={'id':new_id('hypothesis'),'type':'hypothesis','project_id':bundle['project']['id'],'created_at':STAMP,
        'text':'SYNTHETIC proposed binding/property trade-off; not an experimental conclusion',
        'question':'Compare distinct materials with matched binding/property/expression protocols',
        'limitations':'Synthetic engineering fixture; no biological validity or causality established',
        'molecule_ids':[molecules[0]['id'],molecules[1]['id']],'related_evidence_ids':[note['id']],
        'lineage_ids':[],'residue_refs':[],'structure_refs':[],'status':'proposed',
        'source':{'name':'SYNTHETIC proposed explanation','version':'1'}}
    bundle['entities'] += [repeat,note,hypothesis]
    validate_graph(bundle['project'],bundle['entities'])
    return bundle
