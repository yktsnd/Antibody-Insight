/* Independent F21/F22 P03/P08 J03/J08 AC-J03/AC-J08.
 * Actual domain-valid source + actual source-detail renderer/toggle handlers.
 * Read-only Node VM (not a replacement for frozen actual-browser replay).
 */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),crypto=require('node:crypto');
const {spawnSync}=require('node:child_process');
const root=path.resolve(__dirname,'..'),out=path.join(root,'TEST_EVIDENCE');
const python=process.env.PYTHON||path.join(root,'.venv','Scripts','python.exe');
const sourcePath=path.join(root,'web/predictions.js'),source=fs.readFileSync(sourcePath,'utf8');
const historical=fs.readFileSync(path.join(out,'M5-integration-independent-reviewed-pre-lazy-metadata.js'),'utf8');
const sha=(v)=>crypto.createHash('sha256').update(v).digest('hex');
const expectedHistorical='b987785e0ffcad6d6a37f97e140ab57273590b4b03e1fc7aef6603501a1d7cde';
const results=[];
function check(name,fn){const start=Date.now();fn();results.push({name,status:'PASS',duration_ms:Date.now()-start});console.log('PASS',name);}
function fixture(count){
 const p=spawnSync(python,['-c',String.raw`import hashlib,json,sys
from workspace_app.fixtures import example_bundle,STAMP
from workspace_app.predictions import prediction_preview,CANONICAL
from workspace_app.domain import validate_graph,validate_transport_size
b=example_bundle(1);m=next(e for e in b['entities'] if e['type']=='molecule')
token='SYNTHETIC <img src=x onerror=never()> α'
row={'kind':'computed','subject_ref':token,'metric':'SYNTHETIC parameter result','value':0.0,'unit':'synthetic unit','source':{'name':'SYNTHETIC review fixture; no model run','version':'1'},'timestamp':STAMP,'conditions':{'assay':'SYNTHETIC scale fixture','parameter':25.0,'negative_zero':-0.0}}
raw='\ufeff'+json.dumps({'schema_version':CANONICAL,'records':[row]*int(sys.argv[1])},ensure_ascii=False).replace(', ',',\r\n ')
p=prediction_preview(b,raw,'SYNTHETIC-source-detail-scale.json',CANONICAL,{token:m['id']},{},hashlib.sha256(raw.encode('utf8')).hexdigest())
complete={**b,'entities':b['entities']+p['bundle']['entities']};validate_graph(complete['project'],complete['entities']);size=validate_transport_size(complete['project'],complete['entities'])
print(json.dumps({'bundle':complete,'project_utf8_bytes':size,'source_utf8_bytes':len(raw.encode('utf8'))}))`,String(count)],{cwd:root,encoding:'utf8',windowsHide:true,maxBuffer:20*1024*1024,env:{...process.env,PYTHONUTF8:'1'}});
 assert.equal(p.status,0,String(p.error)+' '+p.stderr);return JSON.parse(p.stdout);
}
const escape=(v)=>String(v??'').replace(/[&<>"']/g,(c)=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function renderer(code,bundle){
 const listeners=[],context={document:{addEventListener(name,handler,capture){listeners.push({name,handler,capture});}}};
 vm.createContext(context);vm.runInContext(code+'\nglobalThis.reviewUI=PredictionUI;',context);
 let current=bundle,index=new Map(bundle.entities.map((e)=>[e.id,e]));
 const configure=()=>context.reviewUI.configure({bundle:()=>current,find:(id)=>index.get(id),esc:escape,pretty:(v)=>escape(JSON.stringify(v,null,2))});configure();
 return {ui:context.reviewUI,listeners,setBundle(next){current=next;index=new Map(next.entities.map((e)=>[e.id,e]));configure();}};
}
function detail(kind,id){
 const pre={textContent:''};Object.defineProperty(pre,'innerHTML',{set(){throw Error('Raw source/metadata must never use innerHTML');}});
 return {open:false,dataset:{[kind==='raw'?'predictionContent':'predictionMetadata']:id},
   matches(selector){return selector.includes(kind==='raw'?'data-prediction-content':'data-prediction-metadata');},
   hasAttribute(name){return name===(kind==='raw'?'data-prediction-content':'data-prediction-metadata');},
   querySelector(selector){assert.equal(selector,'pre');return pre;},pre};
}
let amplification;
try{
 assert.equal(sha(historical),expectedHistorical,'The old renderer is a byte-exact previously reviewed snapshot');
 const small=fixture(1),large=fixture(1000),bundle=large.bundle,original=JSON.stringify(bundle);
 const file=bundle.entities.find((e)=>e.type==='prediction_file'),values=bundle.entities.filter((e)=>e.prediction_origin?.file_id===file.id);
 const current=renderer(source,bundle),old=renderer(historical,bundle),smallUI=renderer(source,small.bundle);
 const first=values[0],last=values.at(-1),firstHtml=current.ui.origin(first);
 check('domain-valid thousand-value project fits the original transport ceiling',()=>{
  assert.equal(values.length,1000);assert.equal(file.allocations.length,1000);assert.ok(large.project_utf8_bytes<32*1024*1024);
  assert.ok(file.content.startsWith('\ufeff'));assert.ok(file.content.includes('\r\n'));
 });
 check('previously reviewed renderer reproduces allocation-metadata amplification on the same valid source',()=>{
  const previous=old.ui.origin(first),beforeTotal=values.reduce((n,e)=>n+old.ui.origin(e).length,0),afterTotal=values.reduce((n,e)=>n+current.ui.origin(e).length,0);
  assert.ok(previous.includes(file.allocations.at(-1).evidence_id));assert.ok(beforeTotal>100_000_000);
  assert.ok(afterTotal<2_000_000);assert.ok(beforeTotal>afterTotal*50);
  amplification={project_utf8_bytes:large.project_utf8_bytes,source_utf8_bytes:large.source_utf8_bytes,evidence_count:values.length,
   reviewed_before_origin_characters:previous.length,reviewed_before_total_origin_characters:beforeTotal,
   fixed_origin_characters:firstHtml.length,fixed_total_origin_characters:afterTotal};
 });
 check('initial fixed metadata/raw details are empty and markup scales with evidence rather than allocations squared',()=>{
  const smallFile=small.bundle.entities.find((e)=>e.type==='prediction_file'),smallValue=small.bundle.entities.find((e)=>e.prediction_origin?.file_id===smallFile.id);
  assert.ok(Math.abs(firstHtml.length-smallUI.ui.origin(smallValue).length)<100);
  assert.ok(firstHtml.includes('data-prediction-metadata="'+file.id+'"'));assert.ok(firstHtml.includes('data-prediction-content="'+file.id+'"'));
  assert.equal((firstHtml.match(/<pre><\/pre>/g)||[]).length,2);
  assert.ok(!firstHtml.includes(file.allocations.at(-1).evidence_id));assert.ok(!firstHtml.includes('<img src=x'));
  assert.ok(current.ui.origin(last).includes('/records/999/value'));
 });
 const toggle=current.listeners.find((e)=>e.name==='toggle');assert.ok(toggle&&toggle.capture===true);
 const raw=detail('raw',file.id),metadata=detail('metadata',file.id);
 check('raw and metadata open separately through textContent with all actual allocations and hostile tokens retained',()=>{
  raw.open=true;toggle.handler({target:raw});assert.equal(raw.pre.textContent,file.content);assert.equal(metadata.pre.textContent,'');
  metadata.open=true;toggle.handler({target:metadata});
  assert.deepEqual(JSON.parse(metadata.pre.textContent),{bindings:file.bindings,options:file.options,allocations:file.allocations});
  assert.ok(metadata.pre.textContent.includes(file.allocations.at(-1).evidence_id));assert.ok(metadata.pre.textContent.includes('<img src=x'));
  assert.equal(raw.pre.textContent,file.content);assert.notEqual(metadata.pre.textContent,file.content);
 });
 check('closing each native detail releases only its text and reopening preserves the exact original source',()=>{
  metadata.open=false;toggle.handler({target:metadata});assert.equal(metadata.pre.textContent,'');assert.equal(raw.pre.textContent,file.content);
  raw.open=false;toggle.handler({target:raw});assert.equal(raw.pre.textContent,'');raw.open=true;toggle.handler({target:raw});assert.equal(raw.pre.textContent,file.content);
  raw.open=false;toggle.handler({target:raw});assert.equal(raw.pre.textContent,'');assert.equal(JSON.stringify(bundle),original);
 });
 check('source-last imports use the existing identity index and never scan the entity list per detail',()=>{
  const reversed={...bundle,entities:[...bundle.entities].reverse()};
  reversed.entities.find=()=>{throw Error('Source detail must use the existing ID index, not repeatedly scan source-last entities');};
  const ordered=renderer(source,reversed),detailNode=detail('metadata',file.id);
  for(const e of values)assert.ok(ordered.ui.origin(e).includes(e.prediction_origin.json_pointer));
  detailNode.open=true;ordered.listeners.find((e)=>e.name==='toggle').handler({target:detailNode});
  assert.deepEqual(JSON.parse(detailNode.pre.textContent).allocations,file.allocations);
  ordered.ui.download(first.id); // Wrong-type Evidence ID must not trigger a download.
 });
 check('a changed project cannot disclose the previous source through stale detail nodes',()=>{
  current.setBundle({entities:[]});metadata.open=true;toggle.handler({target:metadata});assert.equal(metadata.pre.textContent,'Source unavailable');
  raw.open=true;toggle.handler({target:raw});assert.equal(raw.pre.textContent,'Source unavailable');metadata.open=false;toggle.handler({target:metadata});assert.equal(metadata.pre.textContent,'');
 });
 assert.equal(sha(fs.readFileSync(sourcePath)),sha(source),'Prediction module remained stable during independent replay');
 fs.writeFileSync(path.join(out,'M5-source-details-independent-results.json'),JSON.stringify({status:'PASS',scope:'Independent actual-domain fixture and renderer/toggle replay; frozen actual-browser integration remains separate',results,amplification,
   source_sha256:sha(source),historical_source_sha256:sha(historical),test_sha256:sha(fs.readFileSync(__filename)),fixture:'Synthetic engineering fixture; no model run or scientific validation',timestamp:new Date().toISOString()},null,2));
}catch(error){console.error(error);fs.writeFileSync(path.join(out,'M5-source-details-independent-results.json'),JSON.stringify({status:'FAIL',results,error:String(error),source_sha256:sha(source),timestamp:new Date().toISOString()},null,2));process.exitCode=1;}
