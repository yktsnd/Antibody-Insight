/* Transport guard probes use the actual app API; Unicode export uses native controls. */
const {chromium}=require('playwright'),{spawn,spawnSync}=require('node:child_process');
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),temp=fs.mkdtempSync(path.join(os.tmpdir(),'antibody-numeric-guards-')),out=path.join(root,'TEST_EVIDENCE');
const python=process.env.PYTHON||path.join(root,'.venv','Scripts','python.exe'),database=path.join(temp,'guards.sqlite3');let server,browser,page,origin;const results=[],errors=[],imports=[];
function py(code,args=[]){const r=spawnSync(python,['-c',code,...args],{cwd:root,windowsHide:true,encoding:'utf8'});assert.equal(r.status,0,r.stderr);return JSON.parse(r.stdout);}
const fixture=py(`import sys,json
sys.path.insert(0,'tests')
from numeric_transport_fixture import transport_bundle,inspect_transport
from workspace_app.storage import Store
seed=transport_bundle('guard-seed');unicode=transport_bundle('guard-unicode');direct=transport_bundle('guard-direct')
unicode['project']['title']='[SYNTHETIC FIXTURE] 温度・構成 μM Å'
for e in unicode['entities']:
    if e['type']=='evidence' and e['kind']=='measured':
        e['description']='試験注釈: μM / µM / Å; numeric spelling stays source-scoped.'
        e['conditions']['label']='温度 25.0 °C / μM / µM'
Store(sys.argv[1]).import_bundle(seed)
print(json.dumps({'seed_id':seed['project']['id'],'seed_expected':inspect_transport(seed),'unicode_json':json.dumps(unicode,ensure_ascii=False),'unicode_id':unicode['project']['id'],'unicode_expected':inspect_transport(unicode),'direct_json':json.dumps(direct),'direct_id':direct['project']['id']}))`,[database]);
async function check(name,fn){const t=Date.now();await fn();results.push({name,status:'PASS',duration_ms:Date.now()-t});console.log('PASS',name);}
async function raw(id){return page.evaluate(async(id)=>await(await fetch('/api/bundle?project_id='+id)).text(),id);}
async function projects(){return page.evaluate(async()=>(await(await fetch('/api/bootstrap')).json()).projects.map((p)=>p.id));}
function inspect(text,label){const target=path.join(temp,label+'.json');fs.writeFileSync(target,text);return py("import sys,json;from pathlib import Path;sys.path.insert(0,'tests');from numeric_transport_fixture import inspect_transport;print(json.dumps(inspect_transport(json.loads(Path(sys.argv[1]).read_text(encoding='utf-8')))))",[target]);}
function request(text){return{text,format:'json',filename:'synthetic-guard.json',project_id:null,title:'',goal:'',data_class:'synthetic_fixture'};}
(async()=>{
 server=spawn(python,['-m','workspace_app.server','--database',database,'--port','0'],{cwd:root,windowsHide:true,stdio:['ignore','pipe','pipe']});origin=await new Promise((resolve,reject)=>{let log='';const timer=setTimeout(()=>reject(Error('Server timeout '+log)),15000);server.stdout.on('data',(d)=>{log+=d;const m=log.match(/http:\/\/127\.0\.0\.1:\d+/);if(m){clearTimeout(timer);resolve(m[0]);}});server.stderr.on('data',(d)=>log+=d);});
 browser=await chromium.launch({headless:true,channel:process.env.PLAYWRIGHT_CHANNEL||'chrome'});page=await browser.newPage({acceptDownloads:true});page.on('pageerror',(e)=>errors.push(e.message));page.on('request',(r)=>{if(r.url().endsWith('/api/import'))imports.push(r.postData());});await page.goto(origin);await page.waitForFunction(()=>!document.querySelector('#project-select').disabled);
 await check('edited approved root and nested snapshots fail closed before any import request',async()=>{
  const before=imports.length,rootError=await page.evaluate(async(id)=>{const b=await api('/api/bundle?project_id='+id);b.entities.find((e)=>e.type==='molecule').name='Edited root snapshot';try{await api('/api/import',b);return null;}catch(e){return e.message;}},fixture.seed_id);
  assert.match(rootError,/Reviewed records changed.*new preview/);const nestedError=await page.evaluate(async(input)=>{const preview=await api('/api/preview',input);preview.bundle.entities.find((e)=>e.type==='molecule').name='Edited after nested review';try{await api('/api/import',preview.bundle);return null;}catch(e){return e.message;}},request(fixture.unicode_json));assert.match(nestedError,/Reviewed records changed.*new preview/);assert.equal(imports.length,before);assert.deepEqual(await projects(),[fixture.seed_id]);assert.deepEqual(inspect(await raw(fixture.seed_id),'after-edits'),fixture.seed_expected);
 });
 await check('mismatched top-level nested raw companion is rejected before use',async()=>{
  const before=imports.length;await page.route('**/api/preview',async(route)=>{const response=await route.fetch(),envelope=await response.json();assert.equal(typeof envelope.serialized_bundle,'string');const wrong=JSON.parse(envelope.serialized_bundle);wrong.project.title+=' mismatched companion';envelope.serialized_bundle=JSON.stringify(wrong);await route.fulfill({response,json:envelope});});
  const error=await page.evaluate(async(input)=>{try{await api('/api/preview',input);return null;}catch(e){return e.message;}},request(fixture.unicode_json));await page.unroute('**/api/preview');assert.match(error,/Preview serialization differs/);assert.equal(imports.length,before);assert.deepEqual(await projects(),[fixture.seed_id]);
 });
 await check('unknown direct objects retain strict server validation and current explicit body',async()=>{
  const original=await raw(fixture.seed_id),before=imports.length,result=await page.evaluate(async(text)=>{const b=JSON.parse(text);b.client_extra='unsupported';try{await api('/api/import',b);return null;}catch(e){return e.message;}},fixture.direct_json);assert.match(result,/Unsupported fields/);assert.equal(imports.length,before+1);assert.deepEqual(await projects(),[fixture.seed_id]);
  const expected=await page.evaluate(async(text)=>{const b=JSON.parse(text);b.entities.find((e)=>e.type==='molecule').name='Explicit direct client declaration';for(const e of b.entities)if(e.type==='evidence'&&e.kind==='measured')e.conditions={assay:'SYNTHETIC direct client declaration',dose:1,nested:{values:[1,1,0,0]}};const sent=JSON.stringify(b);await api('/api/import',b);return sent;},fixture.direct_json);assert.deepEqual(inspect(await raw(fixture.direct_id),'direct-stored'),inspect(expected,'direct-expected'));assert.equal(await raw(fixture.seed_id),original);
 });
 await check('Unicode nested source numbers signed zero and native fresh export preserve exact typed records',async()=>{
  await page.evaluate(async(input)=>{const preview=await api('/api/preview',input);await api('/api/import',preview.bundle);},request(fixture.unicode_json));assert.deepEqual(inspect(await raw(fixture.unicode_id),'unicode-stored'),fixture.unicode_expected);
  await page.reload();await page.waitForFunction(()=>!document.querySelector('#project-select').disabled);await page.locator('#project-select').selectOption(fixture.unicode_id);await page.waitForFunction((id)=>!document.querySelector('#project-select').disabled&&document.querySelector('#project-select').value===id,fixture.unicode_id);const waiting=page.waitForEvent('download');await page.locator('#export-button').click();const download=await waiting,file=path.join(temp,'unicode-export.json');await download.saveAs(file);assert.deepEqual(inspect(fs.readFileSync(file,'utf8'),'unicode-export'),fixture.unicode_expected);const storage=await page.evaluate(()=>Object.values(localStorage));assert.ok(!storage.some((v)=>v.includes('試験注釈')||v.includes('synthetic_transport_context')||v.includes('serialized_bundle')));
 });
 assert.deepEqual(errors,[]);fs.writeFileSync(path.join(out,'M4-numeric-transport-guards-results.json'),JSON.stringify({status:'PASS',timestamp:new Date().toISOString(),browser:await browser.version(),scope:'Raw-snapshot mutation/pairing/direct-body guards and Unicode typed-source transport',results,no_javascript_errors:true},null,2));
})().catch((error)=>{console.error(error);fs.writeFileSync(path.join(out,'M4-numeric-transport-guards-failure.json'),JSON.stringify({status:'FAIL',timestamp:new Date().toISOString(),error:String(error),results,errors},null,2));process.exitCode=1;}).finally(async()=>{if(browser)await browser.close();if(server&&server.exitCode===null)await new Promise((resolve)=>{server.once('exit',resolve);server.kill();});});
