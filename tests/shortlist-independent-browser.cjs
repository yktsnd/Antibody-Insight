/* Independent P01/P07 J01/J07 AC-J01/AC-J07 draft-retention/ownership review.
 * Labelled synthetic fixtures; no scientific or human-usability acceptance. */
const {chromium}=require('playwright'),{spawn,spawnSync}=require('node:child_process');
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),temp=fs.mkdtempSync(path.join(os.tmpdir(),'antibody-shortlist-independent-'));
const python=process.env.PYTHON||path.join(root,'.venv','Scripts','python.exe'),database=path.join(temp,'review.sqlite3');
const output=path.join(root,'TEST_EVIDENCE',process.env.SHORTLIST_REVIEW_OUTPUT||'M6-shortlist-independent-browser-v1.json');
const sourcePaths=['web/app.js','workspace_app/server.py','workspace_app/storage.py','workspace_app/domain.py','tests/shortlist-independent-browser.cjs'];
const sourceHashes=()=>Object.fromEntries(sourcePaths.map((p)=>[p,crypto.createHash('sha256').update(fs.readFileSync(path.join(root,p))).digest('hex')]));
const initialSourceHashes=sourceHashes();
const setup=spawnSync(python,['-c',`import copy,json,sys
from workspace_app.fixtures import example_bundle
from workspace_app.domain import new_id
from workspace_app.storage import Store
b=example_bundle();mapping={b['project']['id']:new_id('project'),**{e['id']:new_id(e['type']) for e in b['entities']}}
def rekey(v):
 if isinstance(v,str):return mapping.get(v,v)
 if isinstance(v,list):return [rekey(x) for x in v]
 if isinstance(v,dict):return {k:rekey(x) for k,x in v.items()}
 return v
other=rekey(copy.deepcopy(b));other['project']['title']='[SYNTHETIC] independent second project'
s=Store(sys.argv[1]);s.import_bundle(b);s.import_bundle(other)
print(json.dumps({'first':b,'other':other}))`,database],{cwd:root,encoding:'utf8',windowsHide:true});
assert.equal(setup.status,0,setup.stderr);const seed=JSON.parse(setup.stdout),first=seed.first,other=seed.other;
const mols=(b)=>b.entities.filter((e)=>e.type==='molecule');
const results=[],errors=[],outbound=[],gates=[];let server,browser,page,context,origin;
async function check(name,fn){const start=Date.now();await fn();results.push({name,status:'PASS',duration_ms:Date.now()-start});console.log('PASS',name);}
async function settle(){await page.evaluate(()=>new Promise((r)=>requestAnimationFrame(()=>requestAnimationFrame(r))));}
async function nav(s){await page.locator(`nav [data-screen="${s}"]`).click();}
async function project(b){await page.locator('#project-select').selectOption(b.project.id);await page.waitForFunction(()=>!document.querySelector('#project-select').disabled);}
async function choose(b,indices){await nav('E');for(const [i,m] of mols(b).entries())await page.locator(`[data-select="${m.id}"]`).setChecked(indices.includes(i));await nav('R');}
async function preview(){await page.locator('#review-shortlist').click();await page.locator('#shortlist-dialog').waitFor({state:'visible'});return JSON.parse(await page.locator('#shortlist-preview pre').textContent());}
async function close(){await page.keyboard.press('Escape');await page.locator('#shortlist-dialog').waitFor({state:'hidden'});await settle();}
async function read(b=first){return page.evaluate(async(id)=>(await(await fetch('/api/bundle?project_id='+id)).json()),b.project.id);}
async function gate(suffix,fulfill){let mark,release;const opened=new Promise((r)=>mark=r),held=new Promise((r)=>release=r);gates.push({suffix,mark,held,fulfill});return{opened,async finish(){const done=page.waitForResponse((r)=>r.url().endsWith(suffix));release();await done;await settle();}};}
function write(status,error){fs.writeFileSync(output,JSON.stringify({status,results,error:error?String(error.stack||error):null,errors,outbound,initial_source_sha256:initialSourceHashes,final_source_sha256:sourceHashes(),timestamp:new Date().toISOString(),scope:'Actual Chrome, temporary SQLite, synthetic fixtures. Engineering edges only; not human or scientific validation.'},null,2));}
(async()=>{
 server=spawn(python,['-m','workspace_app.server','--database',database,'--port','0'],{cwd:root,windowsHide:true,stdio:['ignore','pipe','pipe']});
 origin=await new Promise((resolve,reject)=>{let log='';const timer=setTimeout(()=>reject(Error(log)),15000);server.stdout.on('data',(d)=>{log+=d;const m=log.match(/http:\/\/127\.0\.0\.1:\d+/);if(m){clearTimeout(timer);resolve(m[0]);}});server.stderr.on('data',(d)=>log+=d);server.on('exit',(c)=>{clearTimeout(timer);reject(Error('Server exited '+c+' '+log));});});
 browser=await chromium.launch({headless:true,channel:process.env.PLAYWRIGHT_CHANNEL||'chrome'});context=await browser.newContext({viewport:{width:1500,height:1000}});page=await context.newPage();page.on('pageerror',(e)=>errors.push(e.message));
 await context.route('**/*',async(route)=>{if(!route.request().url().startsWith(origin+'/')){outbound.push(route.request().url());await route.abort();}else await route.continue();});
 await page.route(origin+'/api/*',async(route)=>{const i=gates.findIndex((g)=>route.request().url().endsWith(g.suffix));if(i<0){await route.continue();return;}const g=gates.splice(i,1)[0];g.mark();await g.held;if(g.fulfill)await route.fulfill(g.fulfill);else await route.continue();});
 await page.goto(origin);await page.waitForFunction(()=>!document.querySelector('#project-select').disabled);
 let excluded,expected,reason='PRIVATE <script>window.invalid=true</script> & exact reason; next: repeat assay on original lots.';
 await check('R-W-R retains reason and excluded evidence IDs; preview and saved snapshot exact',async()=>{
  await project(first);await choose(first,[0,1]);assert.equal(await page.locator('[data-evidence]').count(),3);excluded=await page.locator('[data-evidence]').nth(1).getAttribute('data-evidence');await page.locator(`[data-evidence="${excluded}"]`).uncheck();await page.locator('#shortlist-reason').fill(reason);
  expected=await page.locator('[data-evidence]:checked').evaluateAll((xs)=>xs.map((x)=>x.dataset.evidence));await nav('W');await nav('R');assert.equal(await page.locator('#shortlist-reason').inputValue(),reason);assert.equal(await page.locator(`[data-evidence="${excluded}"]`).isChecked(),false);assert.equal(await page.evaluate(()=>window.invalid),undefined);const p=await preview();assert.equal(p.reason,reason);assert.deepEqual(p.evidence_ids,expected);await close();
 });
 await check('candidate-set switch isolates text and choices; returning in reverse selection order restores draft',async()=>{
  await choose(first,[0]);assert.equal(await page.locator('#shortlist-reason').inputValue(),'');await page.locator('#shortlist-reason').fill('PRIVATE one-candidate separate question');await page.locator('[data-evidence]').first().uncheck();
  await choose(first,[]);await nav('E');await page.locator(`[data-select="${mols(first)[1].id}"]`).check();await page.locator(`[data-select="${mols(first)[0].id}"]`).check();await nav('R');assert.equal(await page.locator('#shortlist-reason').inputValue(),reason);assert.deepEqual(await page.locator('[data-evidence]:checked').evaluateAll((xs)=>xs.map((x)=>x.dataset.evidence)),expected);
 });
 await check('different project isolates drafts and return restores original candidate set',async()=>{
  await project(other);await choose(other,[0,1]);assert.equal(await page.locator('#shortlist-reason').inputValue(),'');await page.locator('#shortlist-reason').fill('OTHER PRIVATE separate project');assert.equal(await page.locator('[data-evidence]:checked').count(),3);await project(first);await nav('R');assert.equal(await page.locator('#shortlist-reason').inputValue(),reason);assert.equal(await page.locator(`[data-evidence="${excluded}"]`).isChecked(),false);
 });
 await check('all evidence can remain excluded and blank reason cannot preview or write',async()=>{
  await choose(first,[2]);for(const el of await page.locator('[data-evidence]').all())await el.uncheck();await page.locator('#shortlist-reason').fill('PRIVATE explicitly no evidence; next measure missing result');await nav('W');await nav('R');assert.equal(await page.locator('[data-evidence]:checked').count(),0);const p=await preview();assert.deepEqual(p.evidence_ids,[]);await close();await page.locator('#shortlist-reason').fill('   ');const before=await read();await page.locator('#review-shortlist').click();assert.equal(await page.locator('#shortlist-dialog[open]').count(),0);assert.deepEqual(await read(),before);await choose(first,[0,1]);
 });
 await check('successful save freezes selected exact evidence while newer in-flight draft edit survives',async()=>{
  const p=await preview(),held=await gate('/api/shortlist');await page.locator('#confirm-shortlist').click();await held.opened;await close();await page.locator('#shortlist-reason').fill('PRIVATE newer unsaved edit while old save pending');await page.locator(`[data-evidence="${excluded}"]`).check();await held.finish();
  assert.equal(await page.locator('#shortlist-reason').inputValue(),'PRIVATE newer unsaved edit while old save pending');await nav('W');await nav('R');assert.equal(await page.locator('#shortlist-reason').inputValue(),'PRIVATE newer unsaved edit while old save pending');assert.equal(await page.locator(`[data-evidence="${excluded}"]`).isChecked(),true);
  const saved=(await read()).entities.filter((e)=>e.type==='decision');assert.equal(saved.length,1);assert.equal(saved[0].reason,p.reason);assert.deepEqual(saved[0].evidence_snapshot.map((e)=>e.id),p.evidence_ids);
 });
 await check('a rejected late save preserves revised draft and suppresses obsolete error',async()=>{
  await preview();const held=await gate('/api/shortlist',{status:422,contentType:'application/json',body:JSON.stringify({error:'OBSOLETE late rejection'})});await page.locator('#confirm-shortlist').click();await held.opened;await close();await page.locator('#shortlist-reason').fill('PRIVATE current draft after rejected old save');await held.finish();await nav('W');await nav('R');assert.equal(await page.locator('#shortlist-reason').inputValue(),'PRIVATE current draft after rejected old save');assert.doesNotMatch(await page.locator('#notification').textContent(),/OBSOLETE/);
 });
 await check('delayed post-save bundle cannot replace a newer project or its draft',async()=>{
  await page.locator('#shortlist-reason').fill('PRIVATE save original project before late bundle');const p=await preview(),held=await gate('/api/bundle?project_id='+first.project.id);await page.locator('#confirm-shortlist').click();await held.opened;await page.locator('#shortlist-dialog').waitFor({state:'hidden'});await project(other);await page.locator('#shortlist-reason').fill('OTHER PRIVATE newest question while previous bundle waits');await held.finish();assert.equal(await page.locator('#project-select').inputValue(),other.project.id);assert.equal(await page.locator('#shortlist-reason').inputValue(),'OTHER PRIVATE newest question while previous bundle waits');assert.match(await page.locator('#breadcrumb').textContent(),/independent second project/);assert.equal((await read()).entities.some((e)=>e.type==='decision'&&e.reason===p.reason),true);
 });
 await check('ordinary successful save persists exact snapshot and clears only submitted draft',async()=>{
  await project(first);await choose(first,[0,1]);await page.locator('#shortlist-reason').fill('PRIVATE final ordinary save; next compare original materials');await page.locator(`[data-evidence="${excluded}"]`).uncheck();const p=await preview();await page.locator('#confirm-shortlist').click();await page.locator('#shortlist-dialog').waitFor({state:'hidden'});await page.locator('.saved-draft').filter({hasText:p.reason}).waitFor();const record=(await read()).entities.find((e)=>e.type==='decision'&&e.reason===p.reason);assert.ok(record);assert.deepEqual(record.evidence_snapshot.map((e)=>e.id),p.evidence_ids);assert.equal(await page.locator('#shortlist-reason').inputValue(),'');await nav('W');await nav('R');assert.equal(await page.locator('#shortlist-reason').inputValue(),'');
 });
 await check('successful persistence remains explicit when the subsequent bundle refresh fails',async()=>{
  const reason='PRIVATE persisted despite refresh rejection';await page.locator('#shortlist-reason').fill(reason);const p=await preview(),held=await gate('/api/bundle?project_id='+first.project.id,{status:422,contentType:'application/json',body:JSON.stringify({error:'INDEPENDENT refresh rejected after save'})});await page.locator('#confirm-shortlist').click();await held.opened;await held.finish();const saved=(await read()).entities.find((e)=>e.type==='decision'&&e.reason===p.reason);assert.ok(saved);assert.match(await page.locator('#notification').textContent(),new RegExp(saved.id));
 });
 await check('scientific text stays out of localStorage',async()=>{const raw=await page.evaluate(()=>JSON.stringify({...localStorage}));for(const token of ['PRIVATE','OTHER PRIVATE','exact reason','repeat assay'])assert.equal(raw.includes(token),false);assert.deepEqual(outbound,[]);assert.deepEqual(errors,[]);});
 assert.deepEqual(sourceHashes(),initialSourceHashes,'Reviewed source must not change during browser replay');await page.screenshot({path:output.replace(/\.json$/,'.png'),fullPage:true});write('PASS');
})().catch((e)=>{console.error(e);write('FAIL',e);process.exitCode=1;}).finally(async()=>{await browser?.close();if(server&&server.exitCode===null)await new Promise((r)=>{server.once('exit',r);server.kill();});});
