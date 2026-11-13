/* Independently proposed composition endpoint and asynchronous draft ownership edges. */
const {chromium}=require('playwright'),{spawn,spawnSync}=require('node:child_process');
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),temp=fs.mkdtempSync(path.join(os.tmpdir(),'antibody-composition-independent-'));
const python=process.env.PYTHON||path.join(root,'.venv','Scripts','python.exe'),database=path.join(temp,'review.sqlite3'),results=[],errors=[];
const setup=spawnSync(python,['-c',`import copy,json,sys
sys.path.insert(0,'tests')
from composition_journey_fixture import composition_journey_bundle
from workspace_app.domain import new_id
from workspace_app.storage import Store
b=composition_journey_bundle();other=copy.deepcopy(b)
mapping={b['project']['id']:new_id('project'),**{e['id']:new_id(e['type']) for e in b['entities']}}
def replace(v):
    if isinstance(v,str):return mapping.get(v,v)
    if isinstance(v,list):return [replace(x) for x in v]
    if isinstance(v,dict):return {k:replace(x) for k,x in v.items()}
    return v
other=replace(other);other['project']['title']='[SYNTHETIC FIXTURE] Other composition project'
store=Store(sys.argv[1]);store.import_bundle(b);store.import_bundle(other)
print(json.dumps({'first':b,'other':other}))`,database],{cwd:root,windowsHide:true,encoding:'utf8'});assert.equal(setup.status,0,setup.stderr);
const seeded=JSON.parse(setup.stdout),fixture=seeded.first,other=seeded.other,unit=fixture.entities.find((e)=>e.type==='binding_unit');let browser,server,origin,page;
const chain=(i=0)=>page.locator(`fieldset[data-recipe-chain="${i}"]`),part=(i,j)=>page.locator(`.composition-part[data-recipe-chain="${i}"][data-recipe-part="${j}"]`);
async function check(name,fn){const start=Date.now();await fn();results.push({name,status:'PASS',duration_ms:Date.now()-start});console.log('PASS',name);}
async function bundle(id=fixture.project.id){return page.evaluate(async(id)=>await(await fetch('/api/bundle?project_id='+id)).json(),id);}
async function ready(){await page.waitForFunction(()=>!document.querySelector('#project-select').disabled);}
async function project(b){await page.locator('#project-select').selectOption(b.project.id);await ready();}
async function nav(s){await page.locator(`nav [data-screen="${s}"]`).click();}
async function openComposition(){await nav('D');await page.getByRole('button',{name:'Molecular composition',exact:true}).click();if((await page.locator('#composition-design').getAttribute('open'))===null)await page.locator('#composition-design > summary').click();}
async function independentPart(i,j,sequence,role='Explicit independent sequence'){
 await page.locator(`[data-part-add="${i}"]`).click();await part(i,j).locator('[data-part-field="role"]').fill(role);
 await part(i,j).locator('[data-part-source-kind]').selectOption('sequence');await part(i,j).locator('[data-part-sequence]').fill(sequence);
 return part(i,j).locator('[data-part-field="id"]').inputValue();
}
async function top(name,id){await page.locator('#composition-name').fill(name);await page.locator('#composition-external').fill(id);await page.locator('#composition-format').fill('declared synthetic independent layout');}
async function preview(){await page.getByRole('button',{name:'Review new composition before saving',exact:true}).click();await page.locator('#composition-preview-dialog').waitFor({state:'visible'});return JSON.parse(await page.locator('#composition-preview-content > pre').textContent());}
async function closePreview(){await page.getByRole('button',{name:'Close composition preview',exact:true}).click();}
async function gate(path){let release,markHeld;const opened=new Promise((r)=>markHeld=r),held=new Promise((r)=>release=r);await page.route('**'+path,async(route)=>{markHeld();await held;await route.continue();});return{opened,async finish(){const response=page.waitForResponse((r)=>r.url().endsWith(path));release();await response;await page.unroute('**'+path);await page.evaluate(()=>new Promise((r)=>requestAnimationFrame(()=>requestAnimationFrame(r))));}};}
(async()=>{
 server=spawn(python,['-m','workspace_app.server','--database',database,'--port','0'],{cwd:root,windowsHide:true,stdio:['ignore','pipe','pipe']});origin=await new Promise((resolve,reject)=>{let log='';const timer=setTimeout(()=>reject(Error('Server timeout '+log)),15000);server.stdout.on('data',(d)=>{log+=d;const m=log.match(/http:\/\/127\.0\.0\.1:\d+/);if(m){clearTimeout(timer);resolve(m[0]);}});server.stderr.on('data',(d)=>log+=d);});
 browser=await chromium.launch({headless:true,channel:process.env.PLAYWRIGHT_CHANNEL||'chrome'});page=await browser.newPage({viewport:{width:1450,height:1000}});page.on('pageerror',(e)=>errors.push(e.message));await page.goto(origin);await ready();
 await page.locator(`[data-unit-select="${unit.id}"]`).check();await openComposition();await top('Independent endpoint check','INDEPENDENT-ENDPOINT');await page.getByRole('button',{name:'Add an explicit chain',exact:true}).click();await chain().locator('[data-chain-field="id"]').fill('out');await chain().locator('[data-chain-field="role"]').fill('declared test chain');await chain().locator('[data-chain-field="copies"]').fill('1');
 let firstId,secondId;
 await check('deleted component identity is not automatically recycled into a dangling connection',async()=>{
  firstId=await independentPart(0,0,'AC');secondId=await independentPart(0,1,'DE');await page.getByRole('button',{name:'Add an explicit connection',exact:true}).click();assert.equal(await page.locator('[data-connection-kind]').inputValue(),'','No connection kind is inferred');await page.locator('[data-connection-kind]').selectOption('declared_pairing');await page.locator('[data-connection-side="left"]').selectOption(JSON.stringify({chain_id:'out',component_id:firstId}));await page.locator('[data-connection-side="right"]').selectOption(JSON.stringify({chain_id:'out',component_id:secondId}));
  await part(0,0).getByRole('button',{name:'Remove part (connections must be reviewed)',exact:true}).click();assert.match(await page.locator('[data-connection-side="left"] option:checked').textContent(),/Missing endpoint/);
  const replacement=await independentPart(0,1,'FG');assert.notEqual(replacement,firstId,'Automatic IDs cannot recycle the deleted endpoint into an unrelated new part');assert.match(await page.locator('[data-connection-side="left"] option:checked').textContent(),/Missing endpoint/);assert.deepEqual(await bundle(),fixture);
  await page.locator('[data-connection-side="left"]').selectOption(JSON.stringify({chain_id:'out',component_id:replacement}));await part(0,1).getByRole('button',{name:'Move up',exact:true}).click();const incoming=await preview();assert.equal(incoming.entities[0].component_graph.connections[0].left.component_id,replacement);assert.equal(incoming.entities[0].chains[0].sequence,'FGDE');await closePreview();
 });
 await check('late composition review is discarded on task or project change and drafts remain',async()=>{
  const held=await gate('/api/composition-review');await page.getByRole('button',{name:'Review new composition before saving',exact:true}).click();await held.opened;await page.getByRole('button',{name:'Source-numbered substitutions',exact:true}).click();await held.finish();assert.equal(await page.locator('#composition-preview-dialog[open]').count(),0);await openComposition();assert.equal(await page.locator('#composition-external').inputValue(),'INDEPENDENT-ENDPOINT');
  const foreignHeld=await gate('/api/composition-review');await page.getByRole('button',{name:'Review new composition before saving',exact:true}).click();await foreignHeld.opened;await project(other);await openComposition();await top('Other project unsaved draft','OTHER-UNSAVED');await foreignHeld.finish();assert.equal(await page.locator('#composition-preview-dialog[open]').count(),0);assert.equal(await page.locator('#composition-external').inputValue(),'OTHER-UNSAVED');assert.deepEqual(await bundle(other.project.id),other);await project(fixture);await openComposition();assert.equal(await page.locator('#composition-external').inputValue(),'INDEPENDENT-ENDPOINT');assert.deepEqual(await bundle(),fixture);
 });
 await check('late successful save retains newer same-project recipe and current task',async()=>{
  await preview();const held=await gate('/api/import');await page.getByRole('button',{name:'Save reviewed composition records',exact:true}).click();await held.opened;await closePreview();await page.locator('#composition-name').fill('A newer unsaved same-project recipe');await page.locator('#composition-external').fill('NEWER-UNSAVED');await part(0,0).locator('[data-part-sequence]').fill('GH');await page.getByRole('button',{name:'Source-numbered substitutions',exact:true}).click();await held.finish();await ready();assert.equal(await page.locator('[data-design-task="substitution"]').getAttribute('aria-pressed'),'true');await openComposition();assert.equal(await page.locator('#composition-external').inputValue(),'NEWER-UNSAVED');assert.equal(await part(0,0).locator('[data-part-sequence]').inputValue(),'GH');const saved=await bundle();assert.equal(saved.entities.filter((e)=>e.type==='molecule'&&e.external_id==='INDEPENDENT-ENDPOINT').length,1);assert.equal(saved.entities.some((e)=>e.external_id==='NEWER-UNSAVED'),false);
 });
 await check('late successful save in another project cannot erase its draft or change current project',async()=>{
  await page.locator('#composition-external').fill('PENDING-ORIGINAL-PROJECT');await preview();const held=await gate('/api/import');await page.getByRole('button',{name:'Save reviewed composition records',exact:true}).click();await held.opened;await closePreview();await project(other);await openComposition();assert.equal(await page.locator('#composition-external').inputValue(),'OTHER-UNSAVED');await held.finish();assert.equal(await page.locator('#project-select').inputValue(),other.project.id);assert.equal(await page.locator('#composition-external').inputValue(),'OTHER-UNSAVED');assert.deepEqual(await bundle(other.project.id),other);const original=await bundle();assert.equal(original.entities.filter((e)=>e.external_id==='PENDING-ORIGINAL-PROJECT').length,1);assert.equal(original.entities.some((e)=>e.external_id==='NEWER-UNSAVED'),false);
 });
 await check('late rejected save cannot enable a newer pending save or inject its old error into the new review',async()=>{
  await project(fixture);await openComposition();await top('Older save whose response is delayed','STALE-FAILURE');await preview();
  let oldRelease,newRelease,oldHeld,newHeld;const oldGate=new Promise((r)=>oldRelease=r),newGate=new Promise((r)=>newRelease=r),oldStarted=new Promise((r)=>oldHeld=r),newStarted=new Promise((r)=>newHeld=r);
  await page.route('**/api/import',async(route)=>{const id=route.request().postDataJSON().entities[0].external_id;if(id==='STALE-FAILURE'){oldHeld();await oldGate;await route.fulfill({status:422,contentType:'application/json',body:JSON.stringify({error:'Injected obsolete save rejection'})});}else{newHeld();await newGate;await route.continue();}});
  await page.getByRole('button',{name:'Save reviewed composition records',exact:true}).click();await oldStarted;await closePreview();await top('New current review must own its pending save','CURRENT-SAVE');await preview();await page.getByRole('button',{name:'Save reviewed composition records',exact:true}).click();await newStarted;
  const oldResponse=page.waitForResponse((r)=>r.url().endsWith('/api/import')&&r.status()===422);oldRelease();await oldResponse;await page.evaluate(()=>new Promise((r)=>requestAnimationFrame(()=>requestAnimationFrame(r))));
  try{assert.equal(await page.locator('#save-composition').isDisabled(),true,'An old failure must not enable the shared button owned by a newer in-flight save');assert.doesNotMatch(await page.locator('#composition-preview-dialog').textContent(),/Injected obsolete save rejection/);}
  finally{const response=page.waitForResponse((r)=>r.url().endsWith('/api/import')&&r.status()===200);newRelease();await response;await page.unroute('**/api/import');await ready();}
 });
 await check('undefined and declared compositions compare by actual identity format and role without inferred graph',async()=>{
  await openComposition();const undefinedMolecule=fixture.entities.find((e)=>e.type==='molecule'&&!e.component_graph),after=await bundle(),current=after.entities.find((e)=>e.external_id==='CURRENT-SAVE');assert.ok(current);
  await page.locator('[data-composition-compare="left"]').selectOption(undefinedMolecule.id);await page.locator('[data-composition-compare="right"]').selectOption(current.id);const left=page.locator('#composition-contexts > article').nth(0),right=page.locator('#composition-contexts > article').nth(1);await left.filter({hasText:undefinedMolecule.external_id}).waitFor();await right.filter({hasText:'CURRENT-SAVE'}).waitFor();assert.match(await left.textContent(),/Composition undefined; nothing was completed from the format/);assert.equal(await left.getByRole('button',{name:'Use this design as parent recipe',exact:true}).isDisabled(),true);assert.match(await right.textContent(),/declared synthetic independent layout/);assert.match(await right.textContent(),/declared test chain/);assert.deepEqual(await bundle(),after);
  assert.equal(await left.getByRole('heading',{name:'Declared component connections'}).count(),0);
  assert.deepEqual(current.component_graph.connections,[]);
  assert.equal(await right.getByText('No connections declared.',{exact:true}).isVisible(),true);
  assert.equal(await right.getByRole('table',{name:'Declared component connections'}).count(),0);
 });
 assert.deepEqual(errors,[]);fs.writeFileSync(path.join(root,'TEST_EVIDENCE/M3-composition-independent-browser-results.json'),JSON.stringify({status:'PASS',timestamp:new Date().toISOString(),browser:await browser.version(),scope:'Independent source endpoint and asynchronous ownership edges, not full-J05/scientific validity',results},null,2));
})().catch((error)=>{console.error(error);fs.writeFileSync(path.join(root,'TEST_EVIDENCE/M3-composition-independent-browser-failure.json'),JSON.stringify({status:'FAIL',timestamp:new Date().toISOString(),error:String(error),results,errors},null,2));process.exitCode=1;}).finally(async()=>{if(browser)await browser.close();if(server&&server.exitCode===null)await new Promise((resolve)=>{server.once('exit',resolve);server.kill();});});
