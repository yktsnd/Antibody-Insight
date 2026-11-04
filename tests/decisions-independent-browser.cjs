/* Independent F19/F20 P07/P08 J07/J08 AC-J07/AC-J08: exact choices and async ownership. */
const {chromium}=require('playwright'),{spawn,spawnSync}=require('node:child_process');
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),out=path.join(root,'TEST_EVIDENCE'),temp=fs.mkdtempSync(path.join(os.tmpdir(),'antibody-decisions-independent-'));
const python=process.env.PYTHON||path.join(root,'.venv','Scripts','python.exe'),database=path.join(temp,'independent.sqlite3');
const results=[],errors=[],outbound=[],gates=[];let server,browser,page,context,origin;
const setup=spawnSync(python,['-c',`import copy,json,sys
sys.path.insert(0,'tests')
from decision_journey_fixture import decision_journey_bundle
from workspace_app.domain import new_id,shortlist,validate_graph
from workspace_app.storage import Store
b=decision_journey_bundle();m=[e for e in b['entities'] if e['type']=='molecule']
original=[e for e in b['entities'] if e['type']=='evidence' and e['kind']=='measured' and e['metric']=='binding_KD']
base=next(e for e in original if e['value']==0)
computed={**copy.deepcopy(base),'id':new_id('evidence'),'kind':'computed','value':4}
other_unit={**copy.deepcopy(base),'id':new_id('evidence'),'unit':'µM','value':0.004}
integer_condition={**copy.deepcopy(base),'id':new_id('evidence'),'conditions':{**base['conditions'],'temperature_C':25}}
b['entities'] += [computed,other_unit,integer_condition]
legacy=shortlist(b['project'],b['entities'],[x['id'] for x in m],[base['id']],'SYNTHETIC immutable legacy shortlist; no final decision')
b['entities'].append(legacy);validate_graph(b['project'],b['entities'])
mapping={b['project']['id']:new_id('project'),**{e['id']:new_id(e['type']) for e in b['entities']}}
def rekey(v):
 if isinstance(v,str):return mapping.get(v,v)
 if isinstance(v,list):return [rekey(x) for x in v]
 if isinstance(v,dict):return {k:rekey(x) for k,x in v.items()}
 return v
other=rekey(copy.deepcopy(b));other['project']['title']='[SYNTHETIC] other independent decision project'
s=Store(sys.argv[1]);s.import_bundle(b);s.import_bundle(other)
print(json.dumps({'first':b,'other':other,'molecules':m,'legacy':legacy,'base':base,
 'binding_anchor':min(e['id'] for e in original),'computed':computed,'other_unit':other_unit,'integer_condition':integer_condition}))`,database],{cwd:root,encoding:'utf8',windowsHide:true,maxBuffer:16*1024*1024});
assert.equal(setup.status,0,setup.stderr);const seed=JSON.parse(setup.stdout),fixture=seed.first,other=seed.other;
const molecules=seed.molecules;
async function settle(){await page.evaluate(()=>new Promise((r)=>requestAnimationFrame(()=>requestAnimationFrame(r))));}
async function check(name,fn){const start=Date.now();await fn();results.push({name,status:'PASS',duration_ms:Date.now()-start});console.log('PASS',name);}
async function read(id=fixture.project.id){return page.evaluate(async(id)=>await(await fetch('/api/bundle?project_id='+id)).json(),id);}
async function nav(s){await page.locator(`nav [data-screen="${s}"]`).click();}
async function project(b){await page.locator('#project-select').selectOption(b.project.id);await page.waitForFunction(()=>!document.querySelector('#project-select').disabled);}
async function decision(b=fixture){await nav('E');for(const m of b.entities.filter((e)=>e.type==='molecule'))await page.locator(`[data-select="${m.id}"]`).check();await nav('R');await page.getByRole('button',{name:'Criteria and decision versions',exact:true}).click();}
async function fresh(reason){await page.locator('#decision-new').click();await page.locator('#decision-reason').fill(reason);}
async function review(){await page.locator('[data-decision-status="draft"]').click();await page.locator('#decision-preview-dialog').waitFor({state:'visible'});return JSON.parse(await page.locator('#decision-preview-content > details').last().locator('pre').textContent());}
async function close(){await page.keyboard.press('Escape');await page.locator('#decision-preview-dialog').waitFor({state:'hidden'});await settle();}
async function save(){await page.locator('#save-decision').click();await page.locator('#decision-preview-dialog').waitFor({state:'hidden'});await page.locator('#notification').filter({hasText:'Saved immutable'}).waitFor();}
async function gate(suffix,fulfill){let mark,release;const opened=new Promise((r)=>mark=r),held=new Promise((r)=>release=r);
 gates.push({suffix,mark,held,fulfill});
 return {opened,async finish(){const response=page.waitForResponse((r)=>r.url().endsWith(suffix));release();await response;await settle();}};
}
const criterion=()=>page.locator('[data-decision-criterion="0"]');
function write(status,error){fs.writeFileSync(path.join(out,'M4-decisions-independent-browser-results.json'),JSON.stringify({status,results,error:error?String(error):null,errors,outbound,scope:'Independent synthetic decision ownership/source/version edges; full frozen integration and scientific/user gates remain separate',timestamp:new Date().toISOString()},null,2));}
(async()=>{
 server=spawn(python,['-m','workspace_app.server','--database',database,'--port','0'],{cwd:root,windowsHide:true,stdio:['ignore','pipe','pipe']});origin=await new Promise((resolve,reject)=>{let text='';const timer=setTimeout(()=>reject(Error(text)),15000);server.stdout.on('data',(d)=>{text+=d;const found=text.match(/http:\/\/127\.0\.0\.1:\d+/);if(found){clearTimeout(timer);resolve(found[0]);}});server.stderr.on('data',(d)=>text+=d);server.on('exit',(c)=>{clearTimeout(timer);reject(Error('server exit'+c+' '+text));});});
 browser=await chromium.launch({headless:true,channel:process.env.PLAYWRIGHT_CHANNEL||'chrome'});context=await browser.newContext({viewport:{width:1600,height:1000}});page=await context.newPage();page.on('pageerror',(e)=>errors.push(e.message));await context.route('**/*',async(route)=>{if(!route.request().url().startsWith(origin+'/')){outbound.push(route.request().url());await route.abort();}else await route.continue();});
 await page.route(origin+'/api/*',async(route)=>{const i=gates.findIndex((g)=>route.request().url().endsWith(g.suffix));if(i<0){await route.continue();return;}const g=gates.splice(i,1)[0];g.mark();await g.held;if(g.fulfill)await route.fulfill(g.fulfill);else await route.continue();});
 await page.goto(origin);await page.waitForFunction(()=>!document.querySelector('#project-select').disabled);
 await check('delayed exact contexts retain new reason and chosen subset without automatic source or weight',async()=>{
  const held=await gate('/api/decision-context');await decision();await held.opened;
  await page.locator('#decision-reason').fill('PRIVATE independent reason typed while source contexts load');await page.locator(`[data-decision-chosen="${molecules[0].id}"]`).check();await held.finish();await page.locator('#decision-add-context').waitFor();
  assert.equal(await page.locator('#decision-reason').inputValue(),'PRIVATE independent reason typed while source contexts load');assert.equal(await page.locator(`[data-decision-chosen="${molecules[0].id}"]`).isChecked(),true);
  assert.equal(await page.locator('#decision-add-context option').count(),7); // Three original contexts plus three explicit incompatible contexts.
  await page.locator('#decision-add-context').selectOption(seed.binding_anchor);await page.locator('#decision-add-criterion').click();
  assert.equal(await criterion().locator('[data-criterion-field="weight"]').inputValue(),'');assert.equal(await criterion().locator('[data-criterion-field="preference"]').inputValue(),'');
  for(const m of molecules)assert.equal(await criterion().locator(`[data-criterion-choice="${m.id}"]`).inputValue(),'');
  const options=await criterion().locator(`[data-criterion-choice="${molecules[0].id}"] option`).evaluateAll((xs)=>xs.map((x)=>x.value));
  for(const id of [seed.computed.id,seed.other_unit.id,seed.integer_condition.id])assert.equal(options.includes(id),false);
  await criterion().locator('[data-criterion-field="weight"]').fill('4.25');await criterion().locator('[data-criterion-field="preference"]').selectOption('inspect');await criterion().locator(`[data-criterion-choice="${molecules[0].id}"]`).selectOption(seed.base.id);
  assert.match(await criterion().textContent(),new RegExp(seed.base.subject_id));assert.match(await criterion().textContent(),/Original lot:/);assert.match(await criterion().textContent(),/0 \/ nM/);
  assert.equal((await read()).entities.filter((e)=>e.type==='decision').length,1);
 });
 await check('late preview cannot replace an edited reason or a different project decision draft',async()=>{
  const before=await read(),held=await gate('/api/decision-review');await page.locator('[data-decision-status="draft"]').click();await held.opened;await page.locator('#decision-reason').fill('PRIVATE revised reason outranks earlier preview');await held.finish();assert.equal(await page.locator('#decision-preview-dialog[open]').count(),0);assert.equal(await page.locator('#decision-reason').inputValue(),'PRIVATE revised reason outranks earlier preview');assert.deepEqual(await read(),before);
  const current=await review();assert.equal(current.entities[0].reason,'PRIVATE revised reason outranks earlier preview');await close();
  const old=await gate('/api/decision-review');await page.locator('[data-decision-status="draft"]').click();await old.opened;await project(other);await decision(other);await page.locator('#decision-reason').fill('OTHER PRIVATE project decision reason');await old.finish();assert.equal(await page.locator('#decision-preview-dialog[open]').count(),0);assert.equal(await page.locator('#decision-reason').inputValue(),'OTHER PRIVATE project decision reason');assert.deepEqual(await read(),before);await project(fixture);await decision();
 });
 await check('old rejected save cannot unlock or report its error in a newer pending review',async()=>{
  await fresh('PRIVATE old rejected draft');await review();const old=await gate('/api/import',{status:422,contentType:'application/json',body:JSON.stringify({error:'OBSOLETE independent save rejection'})});await page.locator('#save-decision').click();await old.opened;await close();await page.locator('#decision-reason').fill('PRIVATE current saved draft');const current=await review();const pending=await gate('/api/import');await page.locator('#save-decision').click();await pending.opened;assert.equal(await page.locator('#save-decision').isDisabled(),true);await old.finish();assert.equal(await page.locator('#save-decision').isDisabled(),true);assert.doesNotMatch(await page.locator('#decision-preview-dialog').textContent(),/OBSOLETE/);assert.doesNotMatch(await page.locator('#notification').textContent(),/OBSOLETE/);await pending.finish();await page.locator('#decision-preview-dialog').waitFor({state:'hidden'});assert.equal((await read()).entities.some((e)=>e.id===current.entities[0].id),true);assert.equal((await read()).entities.some((e)=>e.type==='decision'&&e.reason==='PRIVATE old rejected draft'),false);
 });
 await check('submitted save retains a newer project and its unsaved criteria decision',async()=>{
  await fresh('PRIVATE original project submitted version');const old=await review(),held=await gate('/api/import');await page.locator('#save-decision').click();await held.opened;await close();await project(other);await decision(other);await page.locator('#decision-reason').fill('OTHER PRIVATE newer project reason survives successful save');const before=await read(other.project.id);await held.finish();assert.equal(await page.locator('#project-select').inputValue(),other.project.id);assert.equal(await page.locator('#decision-reason').inputValue(),'OTHER PRIVATE newer project reason survives successful save');assert.deepEqual(await read(other.project.id),before);assert.equal((await read()).entities.some((e)=>e.id===old.entities[0].id),true);await project(fixture);await decision();
 });
 await check('actual legacy continuation remains draft and a concurrently advanced head rejects stale UI save',async()=>{
  await page.getByRole('button',{name:'Evidence and research questions',exact:true}).click();const legacy=page.locator('.saved-draft').filter({has:page.locator(`[data-revise-decision="${seed.legacy.id}"]`)});assert.match(await legacy.textContent(),/Draft · immutable record/);await page.locator(`[data-revise-decision="${seed.legacy.id}"]`).click();assert.equal(await page.locator('[data-decision-criterion]').count(),0);assert.match(await page.locator('#decision-editor').textContent(),new RegExp(seed.legacy.id));await page.locator('#decision-reason').fill('PRIVATE explicit legacy continuation; unresolved comparison remains draft');const continuation=await review();assert.equal(continuation.entities[0].revision,2);assert.equal(continuation.entities[0].status,'draft');assert.equal(continuation.entities[0].supersedes,seed.legacy.id);await save();assert.deepEqual((await read()).entities.find((e)=>e.id===seed.legacy.id),seed.legacy);
  const second=continuation.entities[0];await page.locator(`[data-revise-decision="${second.id}"]`).click();await page.locator('#decision-reason').fill('PRIVATE stale revision must never fork the recorded head');let sent;page.once('request',(r)=>{if(r.url().endsWith('/api/decision-review'))sent=r.postDataJSON();});const stale=await review();assert.ok(sent);const competitor=await page.evaluate(async(data)=>{const boot=await(await fetch('/api/bootstrap')).json();const headers={'Content-Type':'application/json','Origin':location.origin,'X-CSRF-Token':boot.csrf};data.definition.reason='SYNTHETIC competing explicit revision from another session';const reviewed=await fetch('/api/decision-review',{method:'POST',headers,body:JSON.stringify(data)});const result=await reviewed.json();if(!reviewed.ok)throw Error(JSON.stringify(result));const saved=await fetch('/api/import',{method:'POST',headers,body:result.serialized_bundle});if(!saved.ok)throw Error(await saved.text());return result.bundle.entities[0];},sent);
  assert.equal(competitor.revision,3);await page.locator('#save-decision').click();await page.locator('#notification').filter({hasText:/successor|fork|head|revision/i}).waitFor();await page.waitForFunction(()=>!document.querySelector('#save-decision').disabled);const actual=await read();assert.equal(actual.entities.some((e)=>e.id===stale.entities[0].id),false);assert.equal(actual.entities.filter((e)=>e.type==='decision'&&e.supersedes===second.id).length,1);assert.deepEqual(actual.entities.find((e)=>e.id===seed.legacy.id),seed.legacy);await close();await page.reload();await page.waitForFunction(()=>!document.querySelector('#project-select').disabled);await nav('R');await page.getByRole('button',{name:'Criteria and decision versions',exact:true}).click();assert.equal(await page.locator(`[data-revise-decision="${second.id}"]`).isDisabled(),true);await page.locator(`[data-view-decision="${competitor.id}"]`).click();assert.match(await page.locator('#decision-preview-title').textContent(),/Frozen draft revision 3/);assert.equal(await page.locator('#save-decision').isVisible(),false);await page.screenshot({path:path.join(out,'M4-decisions-independent-frozen-draft.png'),fullPage:true});await close();
 });
 await check('late three-candidate preview preserves a newer two-candidate draft and both original scopes',async()=>{
  await fresh('PRIVATE original three-candidate question');const before=await read(),held=await gate('/api/decision-review');await page.locator('[data-decision-status="draft"]').click();await held.opened;await nav('E');await page.locator(`[data-select="${molecules[2].id}"]`).uncheck();await nav('R');await page.locator('#decision-reason').fill('PRIVATE two-candidate comparison has an independent question');await held.finish();assert.equal(await page.locator('#decision-preview-dialog[open]').count(),0);assert.equal(await page.locator('#selection-count').textContent(),'2 selected');assert.equal(await page.locator('#decision-reason').inputValue(),'PRIVATE two-candidate comparison has an independent question');assert.deepEqual(await read(),before);await nav('E');await page.locator(`[data-select="${molecules[2].id}"]`).check();await nav('R');assert.equal(await page.locator('#decision-reason').inputValue(),'PRIVATE original three-candidate question');assert.equal(await page.locator('#selection-count').textContent(),'3 selected');
 });
 const local=await page.evaluate(()=>JSON.stringify({...localStorage}));for(const token of ['PRIVATE','OTHER PRIVATE','binding_KD','temperature_C','evidence_choices'])assert.equal(local.includes(token),false,'No private scientific draft in localStorage');assert.deepEqual(errors,[]);assert.deepEqual(outbound,[]);write('PASS');
})().catch((e)=>{console.error(e);write('FAIL',e);process.exitCode=1;}).finally(async()=>{await browser?.close();if(server&&server.exitCode===null)await new Promise((r)=>{server.once('exit',r);server.kill();});});
