"""F16 P06/P08 J06/J08: actual samples, source rows and lossless measured values."""

import copy
import csv
import hashlib
import io
import json
import math
import threading
import urllib.error
import urllib.request
from http.cookiejar import CookieJar

import pytest

from workspace_app.domain import ValidationError, new_id
from workspace_app.measurements import measurement_preview
from workspace_app.server import make_server
from workspace_app.storage import Store
from test_experiments import experiment_bundle
from workspace_app.fixtures import STAMP


def csv_text(rows, extra=()):
    out=io.StringIO(newline='');writer=csv.writer(out)
    writer.writerow(['material_ref','metric','value','unit','timestamp',*extra])
    writer.writerows(rows)
    return out.getvalue()


def row(ref, value='1.0', unit='mg/L', timestamp=STAMP, *extra):
    return [ref,'synthetic_yield',value,unit,timestamp,*extra]


def test_mapped_measurements_keep_zero_null_conditions_types_provenance_and_restart(tmp_path):
    b,m,constructs,materials=experiment_bundle();original=copy.deepcopy(b)
    raw=csv_text([row('sample α','0.0','mg/L',STAMP,'{"assay":"synthetic","dose":1.0,"nested":[-0.0]}','Original\nsource note'),
                  row(materials[1]['id'],'','',STAMP,'','ND retained as deliberately curated null')],('conditions_json','description'))
    sha=hashlib.sha256(raw.encode('utf-8')).hexdigest()
    result=measurement_preview(b,raw,'actual.csv',{'sample α':materials[0]['id']},{'name':'SYNTHETIC assay','version':'v1'},sha)
    assert result['report']['valid_rows']==2 and not result['report']['excluded']
    a,z=result['bundle']['entities']
    assert type(a['value']) is float and a['value']==0.0 and z['value'] is None and z['unit'] is None
    assert type(a['conditions']['dose']) is float and math.copysign(1,a['conditions']['nested'][0])==-1
    assert a['subject_id']==materials[0]['id'] and z['subject_id']==materials[1]['id']
    assert a['import_origin']['line_number']==3 and a['import_origin']['record_index']==1
    assert z['import_origin']['line_number']==4 and z['import_origin']['record_index']==2
    assert a['import_origin']['text_utf8_sha256']==sha and a['timestamp']==STAMP
    assert a['source']=={'name':'SYNTHETIC assay','version':'v1'} and a['import_origin']['importer']['version']
    assert b==original
    store=Store(tmp_path/'source.sqlite3');store.import_bundle(b);store.import_bundle(result['bundle'])
    exported=Store(store.path).bundle(b['project']['id'])
    fresh=Store(tmp_path/'fresh.sqlite3');fresh.import_bundle(exported)
    assert json.dumps(fresh.bundle(b['project']['id']),sort_keys=True)==json.dumps(exported,sort_keys=True)
    assert exported['entities'][:len(b['entities'])]==original['entities']


@pytest.mark.parametrize('value',['ND','<0.1','>100','1,2',' 1','NaN','Infinity','1e999','1e-999','9007199254740992','1e'+'9'*100])
def test_qualified_unsafe_and_unsupported_numeric_values_excluded_without_fake_zero(value):
    b,_,_,materials=experiment_bundle();raw=csv_text([row(materials[0]['id'],value)])
    result=measurement_preview(b,raw,'source.csv')
    assert result['report']['valid_rows']==0 and len(result['report']['excluded'])==1
    assert result['bundle']['entities']==[]


@pytest.mark.parametrize('case',['unknown','molecule','construct','foreign','missing_time','naive_time','missing_unit','array_conditions','duplicate_json','short','long'])
def test_invalid_rows_never_attach_to_molecule_or_another_sample(case):
    b,m,constructs,materials=experiment_bundle();r=row(materials[0]['id']);extra=()
    if case=='unknown':r[0]='unknown sample'
    elif case=='molecule':r[0]=m['id']
    elif case=='construct':r[0]=constructs[0]['id']
    elif case=='foreign':r[0]=new_id('material')
    elif case=='missing_time':r[4]=''
    elif case=='naive_time':r[4]='2026-11-04T12:00:00'
    elif case=='missing_unit':r[3]=''
    elif case=='array_conditions':r.append('[]');extra=('conditions_json',)
    elif case=='duplicate_json':r.append('{"assay":"a","assay":"b"}');extra=('conditions_json',)
    elif case=='short':r.pop()
    elif case=='long':r.append('unexpected')
    result=measurement_preview(b,csv_text([r]),'source.csv')
    if extra:result=measurement_preview(b,csv_text([r],extra),'source.csv')
    assert not result['bundle']['entities'] and len(result['report']['excluded'])==1
    assert result['report']['unresolved_refs']==(['unknown sample'] if case=='unknown' else [])


@pytest.mark.parametrize('case',['known_id_remap','wrong_type_remap','unknown_canonical_remap','unused','wrong_target','foreign_target','stale_digest'])
def test_mapping_is_exact_file_scoped_and_respects_reserved_ids(case):
    b,m,_,materials=experiment_bundle();ref='external sample';target=materials[0]['id']
    if case=='known_id_remap':ref=materials[1]['id']
    elif case=='wrong_type_remap':ref=m['id']
    elif case=='unknown_canonical_remap':ref=new_id('material')
    elif case=='wrong_target':target=m['id']
    elif case=='foreign_target':target=new_id('material')
    raw=csv_text([row(ref)]);sha=hashlib.sha256(raw.encode()).hexdigest()
    mapping={('unused' if case=='unused' else ref):target}
    with pytest.raises(ValidationError):
        measurement_preview(b,raw,'source.csv',mapping,mapping_text_sha256='a'*64 if case=='stale_digest' else sha)


def test_all_unknown_headers_reported_and_source_pair_never_mixed():
    b,_,_,materials=experiment_bundle()
    with pytest.raises(ValidationError) as exc:
        measurement_preview(b,csv_text([row(materials[0]['id'], '1', 'mg/L', STAMP, 'a','b')],('unknown_a','unknown_b')),'source.csv')
    assert exc.value.details==['unknown_a','unknown_b']
    with pytest.raises(ValidationError,match='together'):
        measurement_preview(b,csv_text([row(materials[0]['id'],'1','mg/L',STAMP,'actual')],('source_name',)),'source.csv')
    raw=csv_text([row(materials[0]['id'],'1','mg/L',STAMP,'actual','')],('source_name','source_version'))
    result=measurement_preview(b,raw,'source.csv',file_source={'name':'unrelated','version':'do not borrow'})
    assert result['bundle']['entities'][0]['source']=={'name':'actual','version':None}
    raw=csv_text([row(materials[0]['id'],'1','mg/L',STAMP,'','v1')],('source_name','source_version'))
    assert measurement_preview(b,raw,'source.csv')['report']['valid_rows']==0


def test_potential_repeated_rows_remain_independent_records_without_aggregation():
    b,_,_,materials=experiment_bundle();raw=csv_text([row(materials[0]['id'])]*2)
    result=measurement_preview(b,raw,'same.csv');a,z=result['bundle']['entities']
    assert a['id']!=z['id'] and a['import_origin']['record_index']==1 and z['import_origin']['record_index']==2
    assert len(result['report']['duplicates'])==1 and result['report']['valid_rows']==2
    combined={**b,'entities':b['entities']+result['bundle']['entities']}
    again=measurement_preview(combined,raw,'same.csv')
    assert len(again['report']['duplicates'])==2 and len(again['bundle']['entities'])==2


@pytest.mark.parametrize('raw',['material_ref,metric,value,unit,timestamp,metric\n', 'material_ref,metric,value,unit,timestamp\n"unclosed', 'material_ref,metric,value,unit,timestamp\n'])
def test_invalid_whole_csv_rejects(raw):
    b,_,_,_=experiment_bundle()
    with pytest.raises(ValidationError):measurement_preview(b,raw,'source.csv')


def test_live_api_preview_save_context_and_strict_boundaries(tmp_path):
    server=make_server(tmp_path/'api.sqlite3',0);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        browser=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))
        def request(path,data=None,headers=None):
            return json.load(browser.open(urllib.request.Request(server.origin+path,data=None if data is None else json.dumps(data).encode(),headers=headers or {})))
        browser.open(server.origin+'/').close();boot=request('/api/bootstrap')
        headers={'Content-Type':'application/json','Origin':server.origin,'X-CSRF-Token':boot['csrf']}
        b,m,constructs,materials=experiment_bundle();request('/api/import',b,headers)
        request_data={'project_id':b['project']['id'],'text':csv_text([row(materials[0]['id'])]),'filename':'source.csv',
                      'mappings':{},'file_source':None,'mapping_text_sha256':None}
        result=request('/api/measurement-preview',request_data,headers)
        assert 'serialized_bundle' in result and len(server.store.bundle(b['project']['id'])['entities'])==len(b['entities'])
        request('/api/import',json.loads(result['serialized_bundle']),headers)
        definition={'type':'material','construct_id':constructs[0]['id'],'name':'Declared material','lot':'supplied'}
        metadata=request('/api/metadata-preview',{'project_id':b['project']['id'],'definition':definition},headers)
        request('/api/import',metadata,headers)
        query='/api/construct-context?project_id='+b['project']['id']+'&molecule_id='+m['id']+'&left_id='+constructs[0]['id']+'&right_id='+constructs[1]['id']
        context=request(query)
        assert len(context['materials'])==4 and context['comparison']['cds']['raw_differences']
        frozen=server.store.bundle(b['project']['id'])
        for path,data,head,status in [(query+'&left_id='+constructs[0]['id'],None,None,422),
                                       (query+'&invented=1',None,None,422),
                                       ('/api/measurement-preview',request_data,{},403),
                                       ('/api/metadata-preview',{'project_id':b['project']['id'],'definition':{**definition,'lot':''}},headers,422)]:
            with pytest.raises(urllib.error.HTTPError) as exc:request(path,data,head)
            assert exc.value.code==status
        assert server.store.bundle(b['project']['id'])==frozen
    finally:
        server.shutdown();thread.join(timeout=5);server.server_close()
