"""F19/F20, P07/P08, J07/J08: retained reasons, exact observations and revisions."""

import copy
import json
import threading
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from http.cookiejar import CookieJar

import pytest

from workspace_app.decisions import decision_context, decision_review
from workspace_app.domain import ValidationError, new_id, validate_graph
from workspace_app.fixtures import STAMP, example_bundle
from workspace_app.storage import Store
from workspace_app.server import make_server


def decision_bundle():
    b=example_bundle(3);b['entities']=[e for e in b['entities'] if e['type']!='evidence']
    molecules=[e for e in b['entities'] if e['type']=='molecule'];index={e['id']:e for e in b['entities']}
    materials=[next(e for e in b['entities'] if e['type']=='material' and index[e['construct_id']]['molecule_id']==m['id']) for m in molecules]
    metrics=[('binding_KD','nM',[0,3,8]),('aggregate_fraction','%',[1,2,3]),('expression_yield','mg/L',[12,15,None])]
    choices=[]
    for metric,unit,values in metrics:
        group=[]
        for material,value in zip(materials,values):
            evidence={'id':new_id('evidence'),'type':'evidence','project_id':b['project']['id'],'created_at':STAMP,
                'subject_id':material['id'],'kind':'measured','metric':metric,'unit':unit,'value':value,'timestamp':STAMP,
                'conditions':{'assay':'SYNTHETIC study; no experiment','temperature_C':25.0},
                'source':{'name':'SYNTHETIC assay fixture; no experiment','version':'1'}}
            b['entities'].append(evidence);group.append(evidence)
        choices.append(group)
    definition={'candidate_ids':[m['id'] for m in molecules],'chosen_candidate_ids':[molecules[0]['id']],
                'criteria':[{'key':key,'name':metric,'weight':weight,'required':required,'preference':preference,
                             'anchor_evidence_id':group[0]['id'],'evidence_choices':{m['id']:e['id'] for m,e in zip(molecules,group)}}
                    for (key,metric,weight,required,preference),group in zip([
                        ('binding','Original binding KD',1.0,True,'lower'),('property','Original aggregate fraction',2,False,'lower'),
                        ('expression','Original expression yield',0,False,'inspect')],choices)],
                'hypothesis_ids':[],'supporting_evidence_ids':[],'reason':'Synthetic researcher choice: compare original binding/property/expression and retain missing expression result.',
                'status':'finalized','supersedes':None}
    return b,molecules,materials,choices,definition


def test_final_choice_preserves_originals_types_missingness_restart_and_revision(tmp_path):
    b,molecules,_,groups,d=decision_bundle();original=copy.deepcopy(b)
    result=decision_review(b,d);record=result['bundle']['entities'][0]
    assert b==original and record['status']=='finalized' and record['revision']==1
    assert record['chosen_candidate_ids']==[molecules[0]['id']] and len(record['candidate_ids'])==3
    assert result['review']['ready_to_finalize'] and not result['review']['blockers']
    assert result['review']['criteria'][0]['rows'][0]['value']==0
    assert result['review']['criteria'][2]['rows'][2]['status']=='value missing'
    assert len(record['evidence_snapshot'])==9 and all(e['subject_id'].startswith('mat_') for e in record['evidence_snapshot'])
    assert type(record['criteria'][0]['weight']) is float
    assert all(type(e['conditions']['temperature_C']) is float for e in record['evidence_snapshot'])
    store=Store(tmp_path/'decisions.sqlite3');store.import_bundle(b);store.import_bundle(result['bundle'])
    later={**copy.deepcopy(groups[0][0]),'id':new_id('evidence'),'value':99};store.import_bundle({**b,'entities':[later]})
    current=Store(store.path).bundle(b['project']['id']);assert next(e for e in current['entities'] if e['id']==record['id'])==record
    revised=copy.deepcopy(d);revised['supersedes']=record['id'];revised['criteria'][0]['weight']=3.0
    revised['criteria'][0]['evidence_choices'][molecules[0]['id']]=later['id'];revised['reason']='Explicit revised synthetic trade-off and new original observation.'
    second=decision_review(current,revised);revision=second['bundle']['entities'][0]
    assert revision['revision']==2 and revision['supersedes']==record['id'] and revision['id']!=record['id']
    assert any(change['field']=='criteria' for change in second['review']['changes'])
    assert any(change['field']=='reason' for change in second['review']['changes'])
    store.import_bundle(second['bundle']);exported=Store(store.path).bundle(b['project']['id'])
    fresh=Store(tmp_path/'fresh.sqlite3');fresh.import_bundle({**exported,'entities':list(reversed(exported['entities']))})
    assert {e['id']:json.dumps(e,sort_keys=True) for e in fresh.bundle(b['project']['id'])['entities']}=={e['id']:json.dumps(e,sort_keys=True) for e in exported['entities']}


@pytest.mark.parametrize('case',['null_choice','null_scalar','zero_weight_required','unchosen_missing'])
def test_required_missing_blocks_finalization_but_draft_retains_original_missingness(case):
    b,molecules,_,groups,d=decision_bundle();criterion=d['criteria'][0]
    if case=='null_scalar':groups[0][2]['value']=None
    else:criterion['evidence_choices'][molecules[2]['id']]=None
    if case=='zero_weight_required':criterion['weight']=0
    # Candidate3 is unchosen and still part of the declared completeness policy.
    with pytest.raises(ValidationError,match='finalization blocked'):decision_review(b,d)
    d['status']='draft';draft=decision_review(b,d)
    assert not draft['review']['ready_to_finalize'] and draft['bundle']['entities'][0]['criteria'][0]['evidence_choices'][molecules[2]['id']]==criterion['evidence_choices'][molecules[2]['id']]
    assert draft['review']['criteria'][0]['rows'][0]['status']=='observed'
    assert draft['review']['criteria'][0]['rows'][0]['value']==0


def test_no_implicit_sole_observation_choice_and_all_optional_final_retains_unknowns():
    b,molecules,_,_,d=decision_bundle()
    for criterion in d['criteria']:
        criterion['required']=False;criterion['evidence_choices']={m['id']:None for m in molecules}
    result=decision_review(b,d)
    assert result['review']['ready_to_finalize']
    assert all(row['evidence_id'] is None and row['value'] is None and row['status']=='choose observation' for c in result['review']['criteria'] for row in c['rows'])
    assert len(result['bundle']['entities'][0]['evidence_snapshot'])==3 # Anchors, not fabricated selected values.


@pytest.mark.parametrize('case',['unit','kind','typed_condition','source_version','unknown_assay','foreign_candidate','out_of_project','missing_key','extra_key'])
def test_incompatible_or_partial_choice_mapping_rejects_even_a_draft(case):
    b,molecules,_,groups,d=decision_bundle();d['status']='draft';base=groups[0][1];other={**copy.deepcopy(base),'id':new_id('evidence')}
    if case=='unit':other['unit']='µM'
    elif case=='kind':other['kind']='computed'
    elif case=='typed_condition':other['conditions']['temperature_C']=25
    elif case=='source_version':other['source']['version']='2'
    elif case=='unknown_assay':other['conditions']=None
    elif case=='foreign_candidate':other['subject_id']=groups[0][0]['subject_id']
    elif case=='out_of_project':other['id']=new_id('evidence')
    elif case=='missing_key':del d['criteria'][0]['evidence_choices'][molecules[1]['id']]
    elif case=='extra_key':d['criteria'][0]['evidence_choices'][new_id('molecule')]=None
    if case not in ('missing_key','extra_key'):
        if case!='out_of_project':b['entities'].append(other)
        d['criteria'][0]['evidence_choices'][molecules[1]['id']]=other['id']
    with pytest.raises(ValidationError):decision_review(b,d)


@pytest.mark.parametrize('weight',[True,-1,float('inf'),float('nan'),'','1e-999','1e999','9007199254740992'])
def test_invalid_or_underflow_weight_never_becomes_zero(weight):
    b,_,_,_,d=decision_bundle();d['criteria'][0]['weight']=weight
    with pytest.raises(ValidationError):decision_review(b,d)


def test_explicit_decimal_weight_text_stores_number_and_missing_criteria_remain_draft():
    b,_,_,_,d=decision_bundle();d['criteria'][0]['weight']='1.0'
    assert type(decision_review(b,d)['bundle']['entities'][0]['criteria'][0]['weight']) is float
    d['criteria']=[];d['chosen_candidate_ids']=[];d['status']='draft'
    result=decision_review(b,d);assert len(result['review']['blockers'])==2
    d['status']='finalized'
    with pytest.raises(ValidationError,match='finalization blocked'):decision_review(b,d)


@pytest.mark.parametrize('case',['unknown_source_version','unknown_conditions','literature'])
def test_anchor_must_establish_real_exact_context_even_in_saved_draft(case):
    b,_,_,groups,d=decision_bundle();d['status']='draft'
    if case=='unknown_source_version':groups[0][0]['source']['version']=None
    elif case=='unknown_conditions':groups[0][0]['conditions']=None
    else:groups[0][0]['kind']='literature'
    with pytest.raises(ValidationError,match='anchor'):decision_review(b,d)


def test_hypothesis_sources_close_snapshot_union_and_out_of_scope_rejects():
    b,molecules,_,groups,d=decision_bundle()
    note={**copy.deepcopy(groups[0][0]),'id':new_id('evidence'),'kind':'annotation','metric':'source_note','value':None,'unit':None,'description':'Synthetic qualitative source note'}
    hypothesis={'id':new_id('hypothesis'),'type':'hypothesis','project_id':b['project']['id'],'created_at':STAMP,
       'text':'Synthetic proposed explanation, not a fact','question':'Compare separately prepared materials','limitations':'No biological validation',
       'molecule_ids':[molecules[0]['id']],'related_evidence_ids':[note['id']],'lineage_ids':[],'residue_refs':[],'structure_refs':[],
       'status':'proposed','source':{'name':'Synthetic research hypothesis','version':'1'}}
    b['entities']+=[note,hypothesis];d['hypothesis_ids']=[hypothesis['id']]
    result=decision_review(b,d);record=result['bundle']['entities'][0]
    assert record['hypothesis_ids']==[hypothesis['id']] and note in record['evidence_snapshot']
    damaged=copy.deepcopy(record);damaged['evidence_snapshot']=[e for e in damaged['evidence_snapshot'] if e['id']!=note['id']]
    with pytest.raises(ValidationError,match='omits'):validate_graph(b['project'],[*b['entities'],damaged])
    d['candidate_ids']=d['candidate_ids'][1:];d['chosen_candidate_ids']=[d['candidate_ids'][0]]
    for criterion in d['criteria']:
        criterion['evidence_choices'].pop(molecules[0]['id']);criterion['anchor_evidence_id']=criterion['evidence_choices'][d['candidate_ids'][0]]
    with pytest.raises(ValidationError,match='Hypothesis'):decision_review(b,d)


def test_legacy_shortlist_is_preserved_and_can_have_one_new_contract_successor(tmp_path):
    b,molecules,_,groups,d=decision_bundle();store=Store(tmp_path/'legacy.sqlite3');store.import_bundle(b)
    old=store.save_shortlist(b['project']['id'],[m['id'] for m in molecules],[groups[0][0]['id']],'Synthetic legacy shortlist')
    assert not {'source','chosen_candidate_ids','hypothesis_ids'}.intersection(old)
    d['supersedes']=old['id'];successor=decision_review(store.bundle(b['project']['id']),d)['bundle']
    assert successor['entities'][0]['revision']==2;store.import_bundle(successor)
    assert next(e for e in Store(store.path).bundle(b['project']['id'])['entities'] if e['id']==old['id'])==old
    for field in ('source','chosen_candidate_ids','hypothesis_ids'):
        partial=copy.deepcopy(successor['entities'][0]);del partial[field]
        with pytest.raises(ValidationError):validate_graph(b['project'],[*b['entities'],old,partial])


def test_reverse_order_imported_fork_and_racing_successors_reject_atomically(tmp_path):
    b,_,_,_,d=decision_bundle();root=decision_review(b,d)['bundle']['entities'][0]
    previous={**b,'entities':[*b['entities'],root]};d['supersedes']=root['id'];d['reason']='Explicit first revision'
    one=decision_review(previous,d)['bundle'];d['reason']='Explicit competing revision';two=decision_review(previous,d)['bundle']
    empty=Store(tmp_path/'fork.sqlite3')
    with pytest.raises(ValidationError,match='successor'):empty.import_bundle({**b,'entities':[two['entities'][0],one['entities'][0],root,*b['entities']]})
    assert empty.projects()==[]
    store=Store(tmp_path/'race.sqlite3');store.import_bundle(previous)
    def save(bundle):
        try:store.import_bundle(bundle);return 'saved'
        except ValidationError:return 'rejected'
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(save,[one,two]))
    assert sorted(results)==['rejected','saved']
    current=Store(store.path).bundle(b['project']['id']);assert len([e for e in current['entities'] if e['type']=='decision'])==2
    assert next(e for e in current['entities'] if e['id']==root['id'])==root


def test_context_options_are_scoped_without_ranking_or_reassigning_materials():
    b,molecules,_,groups,_=decision_bundle();extra={**copy.deepcopy(groups[0][0]),'id':new_id('evidence'),'conditions':None};b['entities'].append(extra)
    context=decision_context(b,[molecules[0]['id'],molecules[1]['id']])
    assert context['candidate_ids']==[molecules[0]['id'],molecules[1]['id']]
    assert len(context['cohorts'])==3 and all(len(c['evidence_ids'])==2 for c in context['cohorts'])
    assert any(e['evidence_id']==extra['id'] for e in context['ineligible'])
    with pytest.raises(ValidationError):decision_context(b,[new_id('molecule')])


def test_live_decision_routes_preview_without_writes_then_revalidate_direct_import(tmp_path):
    server=make_server(tmp_path/'http.sqlite3',0);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        browser=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))
        def request(path,data=None,headers=None):
            return json.load(browser.open(urllib.request.Request(server.origin+path,
                data=None if data is None else json.dumps(data,allow_nan=False).encode(),headers=headers or {})))
        browser.open(server.origin+'/').close();boot=request('/api/bootstrap')
        headers={'Content-Type':'application/json','Origin':server.origin,'X-CSRF-Token':boot['csrf']}
        b,molecules,_,_,d=decision_bundle();server.store.import_bundle(b)
        context=request('/api/decision-context',{'project_id':b['project']['id'],'candidate_ids':[m['id'] for m in molecules]},headers)
        assert len(context['cohorts'])==3 and context['candidate_ids']==d['candidate_ids']
        result=request('/api/decision-review',{'project_id':b['project']['id'],'definition':d},headers)
        assert server.store.bundle(b['project']['id'])==b and result['review']['ready_to_finalize']
        assert json.dumps(json.loads(result['serialized_bundle']),sort_keys=True)==json.dumps(result['bundle'],sort_keys=True)
        saved=request('/api/import',json.loads(result['serialized_bundle']),headers);assert saved['imported']==1
        frozen=server.store.bundle(b['project']['id'])
        bad=copy.deepcopy(result['bundle']);bad['entities'][0]['id']=new_id('decision')
        bad['entities'][0]['criteria'][0]['evidence_choices'][molecules[2]['id']]=None
        cases=[('/api/decision-context',{'project_id':b['project']['id'],'candidate_ids':d['candidate_ids']},{},403),
               ('/api/decision-review',{'project_id':b['project']['id'],'definition':d,'ready_to_finalize':True},headers,422),
               ('/api/import',bad,headers,422)]
        for route,data,head,status in cases:
            with pytest.raises(urllib.error.HTTPError) as exc:request(route,data,head)
            assert exc.value.code==status
        assert Store(server.store.path).bundle(b['project']['id'])==frozen
    finally:
        server.shutdown();thread.join(timeout=5);server.server_close()
