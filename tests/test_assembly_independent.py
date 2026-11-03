"""Independent F14/F15 domain/API edges; no complete-J05 acceptance claim."""

import copy
import json
import threading
import urllib.error
import urllib.request
from http.cookiejar import CookieJar

import pytest

from workspace_app.assembly import composition_context, composition_preview
from workspace_app.domain import ValidationError, new_id
from workspace_app.fixtures import STAMP, composition_bundle, example_bundle
from workspace_app.server import make_server


def paired_sources():
    bundle=composition_bundle()
    unit={'id':new_id('binding_unit'),'type':'binding_unit','project_id':bundle['project']['id'],'created_at':STAMP,
          'name':'Synthetic independent paired source','topology':'paired','source':{'name':'SYNTHETIC independent source','version':'1'},
          'chains':[{'id':'VH','role':'declared source H','sequence':'ACDE','origin':None},
                    {'id':'VL','role':'declared source L','sequence':'FGHIK','origin':None}]}
    equal=copy.deepcopy(unit);equal.update(id=new_id('binding_unit'),name='Equal-sequence distinct source')
    bundle['entities'].extend([unit,equal])
    return bundle,unit,equal


def part(unit,component,chain='VH',start=1,end=4):
    return {'id':component,'role':'explicit source part','source':{'kind':'binding_unit','binding_unit_id':unit['id'],
            'chain_id':chain,'start':start,'end':end}}


def recipe(unit):
    return {'name':'Synthetic independent recipe','external_id':'INDEPENDENT-COMPOSITION','format':'explicit synthetic layout',
            'parent_id':None,'reason':None,'note':'Researcher annotation only; assembly and activity remain unverified.',
            'chains':[{'id':'out-H','role':'declared chain','copies':2,'components':[part(unit,'whole')]}], 'connections':[]}


def test_overlapping_partial_instances_never_become_complete_source_or_merge_equal_units():
    bundle,unit,equal=paired_sources();original=copy.deepcopy(bundle);d=recipe(unit)
    d['chains'][0]['components'].extend([part(unit,'overlap',start=2),part(unit,'split-a',end=2),part(unit,'split-b',start=3),part(equal,'equal-source')])
    d['chains'].append({'id':'out-L','role':'declared partner','copies':1,'components':[part(unit,'light','VL',1,5)]})
    preview=composition_preview(bundle,d);molecule=preview['entities'][0]
    assert molecule['chains'][0]['sequence']=='ACDE'+'CDE'+'AC'+'DE'+'ACDE'
    context=composition_context({**bundle,'entities':[*bundle['entities'],*preview['entities']]},molecule['id'])
    assert {u['unit']['id'] for u in context['source_units']}=={unit['id'],equal['id']}
    paired=next(u for u in context['source_units'] if u['unit']['id']==unit['id']);heavy,light=paired['chains']
    assert [u['component_id'] for u in heavy['usages']]==['whole','overlap','split-a','split-b']
    assert [u['is_full_source_chain'] for u in heavy['usages']]==[True,False,False,False]
    assert heavy['full_source_chain_occurrences']==2 and light['full_source_chain_occurrences']==1
    assert [(u['start'],u['end'],u['copies']) for u in heavy['usages']]==[(1,4,2),(2,4,2),(1,2,2),(3,4,2)]
    assert 'valency' not in context and 'complete_units' not in paired
    context['source_units'][0]['unit']['chains'][0]['sequence']='CHANGED'
    assert bundle==original


@pytest.mark.parametrize('extra',[False,True])
def test_assembled_chain_boundaries_reject_sum_overflow_without_clipping(extra):
    bundle,unit,_=paired_sources();d=recipe(unit);d['chains'][0]['components']=[
        {'id':'first','role':'explicit long fixture','source':{'kind':'sequence','sequence':'A'*60000}},
        {'id':'second','role':'explicit long fixture','source':{'kind':'sequence','sequence':'C'*40000}}]
    if extra:d['chains'][0]['components'].append({'id':'overflow','role':'explicit extra residue','source':{'kind':'sequence','sequence':'G'}})
    before=copy.deepcopy((bundle,d))
    if extra:
        with pytest.raises(ValidationError,match='Assembled chain exceeds'):composition_preview(bundle,d)
    else:
        molecule=composition_preview(bundle,d)['entities'][0]
        assert len(molecule['chains'][0]['sequence'])==100000 and molecule['chains'][0]['sequence'].endswith('C'*40000)
    assert (bundle,d)==before


def test_reordered_components_keep_exact_connection_identity_and_deleted_endpoint_rejects():
    bundle,unit,equal=paired_sources();d=recipe(unit)
    d['chains'][0]['components'].append(part(equal,'second'))
    d['connections']=[{'left':{'chain_id':'out-H','component_id':'whole'},'right':{'chain_id':'out-H','component_id':'second'},'kind':'declared_pairing'}]
    d['chains'][0]['components'].reverse()
    molecule=composition_preview(bundle,d)['entities'][0]
    assert [p['id'] for p in molecule['component_graph']['chains'][0]['components']]==['second','whole']
    assert molecule['component_graph']['connections']==d['connections']
    d['chains'][0]['components'].pop()
    with pytest.raises(ValidationError,match='endpoint'):composition_preview(bundle,d)


@pytest.fixture
def assembly_http(tmp_path):
    server=make_server(tmp_path/'independent-assembly.sqlite3',0);worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
    yield server
    server.shutdown();worker.join(timeout=5);server.server_close()


def client(server):
    opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))
    opener.open(server.origin+'/',timeout=5).close()
    with opener.open(server.origin+'/api/bootstrap',timeout=5) as response:boot=json.load(response)
    return opener,{'Content-Type':'application/json','Origin':server.origin,'X-CSRF-Token':boot['csrf']}


def post(server,opener,headers,path,value):
    with opener.open(urllib.request.Request(server.origin+path,data=json.dumps(value).encode(),headers=headers),timeout=5) as response:
        return response.status,json.load(response)


def test_actual_http_preview_is_readonly_save_atomic_and_new_context_authenticated(assembly_http):
    server=assembly_http;bundle,unit,_=paired_sources();server.store.import_bundle(bundle);opener,headers=client(server);d=recipe(unit)
    query='/api/composition-context?project_id='+bundle['project']['id']+'&molecule_id='+bundle['entities'][0]['id']
    with pytest.raises(urllib.error.HTTPError) as error:urllib.request.urlopen(server.origin+query,timeout=5)
    assert error.value.code==401
    for changed in ({**headers,'X-CSRF-Token':'wrong'},{**headers,'Origin':'http://foreign.invalid'}):
        with pytest.raises(urllib.error.HTTPError) as error:post(server,opener,changed,'/api/composition-preview',{'project_id':bundle['project']['id'],'definition':d})
        assert error.value.code==403
    status,preview=post(server,opener,headers,'/api/composition-preview',{'project_id':bundle['project']['id'],'definition':d})
    assert status==200 and server.store.bundle(bundle['project']['id'])==bundle
    molecule,note=preview['entities'];assert note['kind']=='annotation' and note['value'] is None and note['subject_id']==molecule['id']
    bad=copy.deepcopy(preview);bad['entities'][1].update(kind='measured',value=1,unit='nM')
    with pytest.raises(urllib.error.HTTPError) as error:post(server,opener,headers,'/api/import',bad)
    assert error.value.code==422 and server.store.bundle(bundle['project']['id'])==bundle
    assert post(server,opener,headers,'/api/import',preview)[0]==200
    after=server.store.bundle(bundle['project']['id']);assert after['entities'][:len(bundle['entities'])]==bundle['entities']
    assert after['entities'][len(bundle['entities']):]==preview['entities']
    with pytest.raises(urllib.error.HTTPError) as error:post(server,opener,headers,'/api/import',preview)
    assert error.value.code==422 and server.store.bundle(bundle['project']['id'])==after
    query='/api/composition-context?project_id='+bundle['project']['id']+'&molecule_id='+molecule['id']
    with opener.open(server.origin+query,timeout=5) as response:context=json.load(response)
    assert context['molecule']['id']==molecule['id'] and context['source_units'][0]['unit']['id']==unit['id']


def test_http_existing_foreign_source_and_malicious_extra_fields_cannot_save(assembly_http):
    server=assembly_http;bundle,unit,_=paired_sources();foreign=example_bundle(9);server.store.import_bundle(bundle);server.store.import_bundle(foreign)
    opener,headers=client(server);d=recipe(unit)
    for request in [
        {'project_id':foreign['project']['id'],'definition':d},
        {'project_id':bundle['project']['id'],'definition':{**d,'source':{'name':'fake authenticated person','version':'fake'}}},
        {'project_id':bundle['project']['id'],'definition':d,'molecule_id':bundle['entities'][0]['id']},
    ]:
        with pytest.raises(urllib.error.HTTPError) as error:post(server,opener,headers,'/api/composition-preview',request)
        assert error.value.code==422
    spoof=copy.deepcopy(d);spoof['chains'][0]['components'][0]['source']['sequence']='ACDE'
    with pytest.raises(urllib.error.HTTPError) as error:post(server,opener,headers,'/api/composition-preview',{'project_id':bundle['project']['id'],'definition':spoof})
    assert error.value.code==422
    assert server.store.bundle(bundle['project']['id'])==bundle and server.store.bundle(foreign['project']['id'])==foreign


def test_combined_http_review_derives_partial_usage_readonly_and_rejects_supplied_context(assembly_http):
    server=assembly_http;bundle,unit,_=paired_sources();server.store.import_bundle(bundle);opener,headers=client(server);d=recipe(unit)
    d['chains'][0]['components'][0]['source']['end']=2
    request={'project_id':bundle['project']['id'],'definition':d}
    with pytest.raises(urllib.error.HTTPError) as error:post(server,opener,{**headers,'X-CSRF-Token':'wrong'},'/api/composition-review',request)
    assert error.value.code==403
    with pytest.raises(urllib.error.HTTPError) as error:post(server,opener,headers,'/api/composition-review',{**request,'context':{'complete_units':100}})
    assert error.value.code==422
    status,review=post(server,opener,headers,'/api/composition-review',request)
    assert status==200 and set(review)=={'bundle','context'}
    candidate=review['bundle']['entities'][0];assert candidate['chains'][0]['sequence']=='AC'
    assert review['context']==composition_context({**bundle,'entities':[*bundle['entities'],*review['bundle']['entities']]},candidate['id'])
    heavy,light=review['context']['source_units'][0]['chains']
    assert heavy['full_source_chain_occurrences']==0 and heavy['usages'][0]['is_full_source_chain'] is False
    assert heavy['usages'][0]['copies']==2 and light['usages']==[]
    assert server.store.bundle(bundle['project']['id'])==bundle
