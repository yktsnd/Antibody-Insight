"""F21/F22 P03/P08 J03/J08: source fidelity, exact identity and full replay."""

import copy
import hashlib
import json
import math
import threading
import urllib.error
import urllib.request
from http.cookiejar import CookieJar

import pytest

import workspace_app.domain as domain
from workspace_app.domain import ValidationError, new_id, validate_graph
from workspace_app.fixtures import STAMP, example_bundle
from workspace_app.predictions import CANONICAL, NATIVE, prediction_preview, prediction_targets
from workspace_app.storage import Store
from workspace_app.server import make_server
from workspace_app.structure_fixtures import structure_bundle


def computed_row(subject, **changes):
    return {'kind':'computed','subject_ref':subject,'metric':'synthetic_computed_property','value':-0.0,'unit':'arbitrary source unit',
            'source':{'name':'SYNTHETIC external result; no model executed','version':'fixture1'},'timestamp':STAMP,
            'conditions':{'assay':'SYNTHETIC computation fixture','parameter':25.0},**changes}


def canonical_text(rows, **extra):
    return json.dumps({'schema_version':CANONICAL,'records':rows,**extra},ensure_ascii=False,allow_nan=False)


def native_options(bundle, **changes):
    structure=next(e for e in bundle['entities'] if e['type']=='structure')
    return {'structure_id':structure['id'],'model':1,'source':{'name':'SYNTHETIC AlphaFold3-like summary; no model run','version':None},
            'timestamp':STAMP,'conditions':{'assay':'SYNTHETIC confidence fixture','external_seed':7,'external_sample':0},**changes}


def test_canonical_mapping_bom_signed_zero_source_allocation_and_restart(tmp_path):
    b=example_bundle(3);subjects=[e for e in b['entities'] if e['type'] in ('molecule','construct','material')][:3]
    raw='\ufeff'+canonical_text([computed_row('__proto__ / ~ α'),computed_row(subjects[1]['id'],value=0),
                                 computed_row(subjects[2]['id'],value=None,unit=None)]).replace(', ', ',\r\n ')
    bindings={'__proto__ / ~ α':subjects[0]['id']};sha=hashlib.sha256(raw.encode('utf-8')).hexdigest()
    original=copy.deepcopy(b);result=prediction_preview(b,raw,'original.json',CANONICAL,bindings,{},sha)
    source,*values=result['bundle']['entities'];assert b==original and result['report']['valid_rows']==3
    assert source['content']==raw and source['sha256']==sha and len(source['allocations'])==3
    assert source['source']['name']=='Antibody Insight computed JSON importer'
    assert [e['subject_id'] for e in values]==[e['id'] for e in subjects]
    assert math.copysign(1,values[0]['value'])==-1 and type(values[0]['value']) is float
    assert type(values[0]['conditions']['parameter']) is float and type(values[1]['value']) is int and values[2]['value'] is None
    assert all(e['kind']=='computed' and e['timestamp']==STAMP for e in values)
    assert all(e['prediction_origin']['json_pointer']==f'/records/{i}/value' for i,e in enumerate(values))
    store=Store(tmp_path/'source.sqlite3');store.import_bundle(b);store.import_bundle(result['bundle'])
    exported=Store(store.path).bundle(b['project']['id']);fresh=Store(tmp_path/'fresh.sqlite3');fresh.import_bundle({**exported,'entities':list(reversed(exported['entities']))})
    assert {e['id']:json.dumps(e,sort_keys=True,ensure_ascii=False) for e in exported['entities']}=={e['id']:json.dumps(e,sort_keys=True,ensure_ascii=False) for e in fresh.bundle(b['project']['id'])['entities']}
    assert next(e for e in exported['entities'] if e['type']=='prediction_file')['content']==raw


def test_native_scalar_scope_unknown_version_retained_unmapped_and_no_boolean_conversion(tmp_path):
    b=structure_bundle();raw=json.dumps({'ptm':0,'iptm':None,'fraction_disordered':0.2,'ranking_score':-99.5,
        'has_clash':True,'chain_ids':['H','L'],'chain_pair_iptm':[[0.3,0.6],[0.6,0.4]],'new/unmapped~field':{'note':'<script>α</script>'}},ensure_ascii=False)
    options=native_options(b);result=prediction_preview(b,raw,'sample-summary.json',NATIVE,{},options)
    source,*values=result['bundle']['entities'];assert len(values)==4 and result['report']['source_files_added']==1
    assert source['content']==raw and source['options']==options
    assert result['report']['retained_unmapped_paths']==['/chain_ids','/chain_pair_iptm','/has_clash','/new~1unmapped~0field']
    assert all(e['subject_id']==options['structure_id'] and e['conditions']['structure_model']==1 for e in values)
    assert all(e['unit']=='1' and e['kind']=='computed' and e['source']['version'] is None for e in values)
    assert next(e for e in values if e['metric']=='ptm')['value']==0
    assert next(e for e in values if e['metric']=='iptm')['value'] is None
    assert not any(e['metric']=='has_clash' for e in values)
    store=Store(tmp_path/'native.sqlite3');store.import_bundle(b);store.import_bundle(result['bundle'])
    assert Store(store.path).bundle(b['project']['id'])['entities'][-5:]==result['bundle']['entities']
    targets=prediction_targets(b);assert targets['structures'][0]['models']==[1,2]


@pytest.mark.parametrize('metric,value',[('ptm',True),('iptm',1.1),('fraction_disordered',-0.01),('ranking_score',-100.01),('ptm',[0.5]),('iptm','ND')])
def test_malformed_recognized_native_scalar_rejects_whole_summary(metric,value):
    b=structure_bundle();raw=json.dumps({'ptm':0.5,'iptm':0.6,metric:value})
    with pytest.raises(ValidationError):prediction_preview(b,raw,'bad.json',NATIVE,{},native_options(b))


@pytest.mark.parametrize('case',['unknown_structure','unknown_model','model_bool','model_float','experimental','unknown_origin','conflicting_model','missing_time','unknown_time','bindings'])
def test_native_does_not_guess_coordinate_model_sample_or_time(case):
    b=structure_bundle();options=native_options(b);bindings={};raw='{"iptm":0.8}'
    if case=='unknown_structure':options['structure_id']=new_id('structure')
    elif case=='unknown_model':options['model']=3
    elif case=='model_bool':options['model']=True
    elif case=='model_float':options['model']=1.0
    elif case=='experimental':next(e for e in b['entities'] if e['id']==options['structure_id'])['origin_kind']='experimental'
    elif case=='unknown_origin':next(e for e in b['entities'] if e['id']==options['structure_id'])['origin_kind']='unknown'
    elif case=='conflicting_model':options['conditions']['structure_model']=2
    elif case=='missing_time':options['timestamp']=''
    elif case=='unknown_time':options['timestamp']=None
    elif case=='bindings':bindings={'external':options['structure_id']}
    with pytest.raises(ValidationError):prediction_preview(b,raw,'bad.json',NATIVE,bindings,options,hashlib.sha256(raw.encode()).hexdigest())


def test_all_unknown_canonical_schema_pointers_block_otherwise_valid_row_subset():
    b=example_bundle(1);subject=next(e['id'] for e in b['entities'] if e['type']=='molecule')
    good=computed_row(subject);bad=computed_row('unknown');extra=computed_row(subject,source={'name':'declared','version':None,'unknown/a~b':1},extra_field=2)
    with pytest.raises(ValidationError) as exc:prediction_preview(b,canonical_text([good,bad,extra],root_extra=3),'extra.json',CANONICAL,{}, {})
    assert exc.value.details==['/records/2/extra_field','/records/2/source/unknown~1a~0b','/root_extra']
    result=prediction_preview(b,canonical_text([good,bad]),'known.json',CANONICAL,{}, {})
    assert result['report']['valid_rows']==1 and len(result['report']['excluded'])==1 and result['report']['unresolved_refs']==['unknown']
    assert result['bundle']['entities'][0]['allocations']==[{'json_pointer':'/records/0/value','evidence_id':result['bundle']['entities'][1]['id']}]


@pytest.mark.parametrize('case',['measured','bad_unit','bad_iptm','bad_time','array_value','bool_value','bad_residue','bad_model'])
def test_known_canonical_row_errors_are_excluded_not_reclassified_or_imputed(case):
    b=structure_bundle();subject=next(e for e in b['entities'] if e['type']=='structure');row=computed_row(subject['id'])
    if case=='measured':row['kind']='measured'
    elif case=='bad_unit':row['unit']=None
    elif case=='bad_iptm':row.update(metric='iptm',unit='1',value=2)
    elif case=='bad_time':row['timestamp']='2026-11-04T10:00:00'
    elif case=='array_value':row['value']=[0.5]
    elif case=='bool_value':row['value']=False
    elif case=='bad_residue':row['residue_refs']=[{'chain_id':'H','sequence_index':999}]
    else:row['conditions']['structure_model']=999
    result=prediction_preview(b,canonical_text([row]),'bad.json',CANONICAL,{}, {})
    assert result['report']['valid_rows']==0 and len(result['report']['excluded'])==1 and result['bundle']['entities']==[]


@pytest.mark.parametrize('reference',['mol_not-a-uuid','mol_00000000-0000-4000-8000-000000000009','prj_00000000-0000-4000-8000-000000000009'])
def test_reserved_missing_malformed_or_wrong_type_subject_cannot_be_redirected(reference):
    b=example_bundle(1);subject=next(e['id'] for e in b['entities'] if e['type']=='molecule');raw=canonical_text([computed_row(reference)])
    with pytest.raises(ValidationError):prediction_preview(b,raw,'reserved.json',CANONICAL,{reference:subject},{},hashlib.sha256(raw.encode()).hexdigest())
    result=prediction_preview(b,raw,'reserved.json',CANONICAL,{}, {})
    assert result['report']['valid_rows']==0 and result['report']['unresolved_refs']==[]


def test_external_mapping_digest_unused_and_foreign_subject_reject():
    b=example_bundle(1);target=next(e['id'] for e in b['entities'] if e['type']=='molecule');raw=canonical_text([computed_row('external')]);sha=hashlib.sha256(raw.encode()).hexdigest()
    for bindings,digest in [({'external':target},'a'*64),({'unused':target},sha),({'external':new_id('molecule')},sha)]:
        with pytest.raises(ValidationError):prediction_preview(b,raw,'mapped.json',CANONICAL,bindings,{},digest)


@pytest.mark.parametrize('case',['value_sign','value_type','condition_type','source_version','description','pointer','allocation','missing_file','missing_evidence','duplicate_allocation','hash','source_text'])
def test_direct_import_rejects_forged_source_origin_and_allocation_atomically(tmp_path,case):
    b=example_bundle(1);target=next(e['id'] for e in b['entities'] if e['type']=='molecule')
    result=prediction_preview(b,canonical_text([computed_row(target),computed_row(target)]),'same.json',CANONICAL,{}, {})
    original=copy.deepcopy(result['bundle']);source,evidence,second=result['bundle']['entities']
    assert evidence['id']!=second['id'] and evidence['prediction_origin']['json_pointer']!=second['prediction_origin']['json_pointer']
    if case=='value_sign':evidence['value']=0.0
    elif case=='value_type':evidence['value']=0
    elif case=='condition_type':evidence['conditions']['parameter']=25
    elif case=='source_version':evidence['source']['version']='other'
    elif case=='description':evidence['description']='source did not say this'
    elif case=='pointer':evidence['prediction_origin']['json_pointer']='/records/1/value'
    elif case=='allocation':source['allocations'][0]['json_pointer']='/records/1/value'
    elif case=='missing_file':result['bundle']['entities'].remove(source)
    elif case=='missing_evidence':result['bundle']['entities'].remove(second)
    elif case=='duplicate_allocation':source['allocations'].append(copy.deepcopy(source['allocations'][0]))
    elif case=='hash':source['sha256']='0'*64
    elif case=='source_text':source['content']=source['content'].replace('25.0','25') # Same displayed number, wrong digest/content/type.
    store=Store(tmp_path/'source.sqlite3');store.import_bundle(b)
    with pytest.raises(ValidationError):store.import_bundle(result['bundle'])
    assert Store(store.path).bundle(b['project']['id'])==b
    store.import_bundle(original);assert len(store.bundle(b['project']['id'])['entities'])==len(b['entities'])+3


@pytest.mark.parametrize('raw',['{"ptm":NaN}','{"ptm":1e999}','{"ptm":1e-999}','{"ptm":0.5,"ptm":0.6}','{"pae":[[1,2]]}'])
def test_invalid_native_json_never_synthesizes_confidence(raw):
    b=structure_bundle()
    with pytest.raises(ValidationError):prediction_preview(b,raw,'bad.json',NATIVE,{},native_options(b))


def test_escaped_project_size_is_checked_before_source_can_be_accepted():
    b=structure_bundle();raw=json.dumps({'iptm':0.5,'unmapped_blob':'"'*(9*1024*1024)})
    assert len(raw.encode())<24*1024*1024
    with pytest.raises(ValidationError,match='JSON-escaped project'):prediction_preview(b,raw,'amplified.json',NATIVE,{},native_options(b))


def test_both_atomic_append_paths_enforce_full_wrapper_and_existing_read_is_unchanged(tmp_path,monkeypatch):
    b=example_bundle(1);store=Store(tmp_path/'bounded.sqlite3');store.import_bundle(b)
    evidence=next(e for e in b['entities'] if e['type']=='evidence');extra={**copy.deepcopy(evidence),'id':new_id('evidence')}
    original_limit=domain.MAX_BUNDLE_BYTES;assert original_limit==32*1024*1024
    exact=domain.validate_transport_size(b['project'],[*b['entities'],extra])
    monkeypatch.setattr(domain,'MAX_BUNDLE_BYTES',exact-1)
    with pytest.raises(ValidationError,match='JSON-escaped project'):store.import_bundle({**b,'entities':[extra]})
    assert Store(store.path).bundle(b['project']['id'])==b
    monkeypatch.setattr(domain,'MAX_BUNDLE_BYTES',exact)
    store.import_bundle({**b,'entities':[extra]});current=Store(store.path).bundle(b['project']['id'])
    monkeypatch.setattr(domain,'MAX_BUNDLE_BYTES',1)
    assert Store(store.path).bundle(b['project']['id'])==current # Existing over-limit workspace remains readable/exportable.
    with pytest.raises(ValidationError,match='JSON-escaped project'):
        store.save_shortlist(b['project']['id'],[next(e['id'] for e in b['entities'] if e['type']=='molecule')],[evidence['id']],'Explicit reason')
    assert Store(store.path).bundle(b['project']['id'])==current


def test_authenticated_prediction_preview_source_save_and_rejected_inputs_do_not_modify_project(tmp_path):
    server=make_server(tmp_path/'api.sqlite3',0);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        browser=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))
        def request(route,data=None,headers=None):
            return json.load(browser.open(urllib.request.Request(server.origin+route,
                data=json.dumps(data).encode() if data is not None else None,headers=headers or {})))
        browser.open(server.origin+'/').close();boot=request('/api/bootstrap')
        headers={'Content-Type':'application/json','Origin':server.origin,'X-CSRF-Token':boot['csrf']}
        b=structure_bundle();server.store.import_bundle(b)
        targets=request('/api/prediction-targets',{'project_id':b['project']['id']},headers)
        assert len(targets['structures'])==2 and targets['structures'][0]['models']==[1,2]
        data={'project_id':b['project']['id'],'text':'{"iptm":-0.0,"ptm":null,"has_clash":false}',
              'filename':'summary.json','file_format':NATIVE,'bindings':{},'options':native_options(b),'bindings_text_sha256':None}
        result=request('/api/prediction-preview',data,headers)
        assert result['report']['valid_rows']==2 and server.store.bundle(b['project']['id'])==b
        authoritative=json.loads(result['serialized_bundle']);assert math.copysign(1,authoritative['entities'][2]['value'])==-1
        request('/api/import',authoritative,headers);stored=server.store.bundle(b['project']['id'])
        for route,body,head,code in [('/api/prediction-targets',{'project_id':b['project']['id']},{},403),
                                    ('/api/prediction-preview',{**data,'options':{**data['options'],'model':99}},headers,422),
                                    ('/api/prediction-preview',{**data,'verified':True},headers,422)]:
            with pytest.raises(urllib.error.HTTPError) as exc:request(route,body,head)
            assert exc.value.code==code
        assert Store(server.store.path).bundle(b['project']['id'])==stored
    finally:
        server.shutdown();thread.join(timeout=5);server.server_close()


@pytest.mark.parametrize('key', ['\\ud800', '\\udfff'])
@pytest.mark.parametrize('duplicate', [False, True])
def test_escaped_invalid_unicode_in_error_diagnostics_returns_complete_422_without_writes(tmp_path,key,duplicate):
    """AC-J08: malformed/unknown input must reject, not break the connection."""
    server=make_server(tmp_path/'unicode-error.sqlite3',0)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        b=example_bundle(1);server.store.import_bundle(b)
        client=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))
        client.open(server.origin+'/').close()
        boot=json.load(client.open(server.origin+'/api/bootstrap'))
        subject=next(e['id'] for e in b['entities'] if e['type']=='molecule')
        raw=canonical_text([computed_row(subject)])
        raw=raw[:-1]+',"'+key+'":1'+(',"'+key+'":2' if duplicate else '')+'}'
        request={'project_id':b['project']['id'],'text':raw,'filename':'rejected-unicode.json',
                 'file_format':CANONICAL,'bindings':{},'options':{},'bindings_text_sha256':None}
        headers={'Content-Type':'application/json','Origin':server.origin,'X-CSRF-Token':boot['csrf']}
        with pytest.raises(urllib.error.HTTPError) as exc:
            client.open(urllib.request.Request(server.origin+'/api/prediction-preview',
                data=json.dumps(request).encode('utf-8'),headers=headers))
        assert exc.value.code==422
        body=exc.value.read();result=json.loads(body.decode('utf-8'))
        assert result['error'] and key.encode('ascii') in body
        assert server.store.bundle(b['project']['id'])==b
        # A subsequent valid request on the same actual session still succeeds.
        request['text']=canonical_text([computed_row(subject)])
        response=json.load(client.open(urllib.request.Request(server.origin+'/api/prediction-preview',
            data=json.dumps(request).encode('utf-8'),headers=headers)))
        assert response['report']['valid_rows']==1 and server.store.bundle(b['project']['id'])==b
    finally:
        server.shutdown();thread.join(timeout=5);server.server_close()
