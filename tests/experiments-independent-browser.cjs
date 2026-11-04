/* Independent F16/F17/F18: P06/P08 J06/J08 AC-J06/AC-J08 ownership and identity. */
const {chromium}=require('playwright'),{spawn,spawnSync}=require('node:child_process');
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),temp=fs.mkdtempSync(path.join(os.tmpdir(),'antibody-experiments-independent-'));
const python=process.env.PYTHON||path.join(root,'.venv','Scripts','python.exe'),database=path.join(temp,'review.sqlite3');
const results=[],errors=[],outbound=[];let browser,server,origin,page;
const setup=spawnSync(python,['-c',`import copy,json,sys
sys.path.insert(0,'tests')
from test_experiments import experiment_bundle
from workspace_app.domain import new_id
from workspace_app.storage import Store
b,m,c,materials=experiment_bundle()
mapping={b['project']['id']:new_id('project'),**{e['id']:new_id(e['type']) for e in b['entities']}}
def replace(v):
 if isinstance(v,str):return mapping.get(v,v)
 if isinstance(v,list):return [replace(x) for x in v]
 if isinstance(v,dict):return {k:replace(x) for k,x in v.items()}
 return v
other=replace(copy.deepcopy(b));other['project']['title']='[SYNTHETIC] independent other expression project'
s=Store(sys.argv[1]);s.import_bundle(b);s.import_bundle(other)
print(json.dumps({'first':b,'other':other,'molecule':m,'constructs':c,'materials':materials}))`,database],{cwd:root,windowsHide:true,encoding:'utf8'});
assert.equal(setup.status,0,setup.stderr);const seed=JSON.parse(setup.stdout),fixture=seed.first,other=seed.other,m=seed.molecule;
async function settle(){await page.evaluate(()=>new Promise((r)=>requestAnimationFrame(()=>requestAnimationFrame(r))));}
async function check(name,fn){const start=Date.now();await fn();results.push({name,status:'PASS',duration_ms:Date.now()-start});console.log('PASS',name);}
async function read(id=fixture.project.id){return page.evaluate(async(id)=>await(await fetch('/api/bundle?project_id='+id)).json(),id);}
async function project(b){await page.locator('#project-select').selectOption(b.project.id);await page.waitForFunction(()=>!document.querySelector('#project-select').disabled);}
async function nav(s){await page.locator(`nav [data-screen="${s}"]`).click();}
async function expression(){await nav('D');await page.getByRole('button',{name:'Expression constructs',exact:true}).click();}
const form=()=>page.locator('[data-metadata-form="construct"]');
async function name(value){if(await form().locator('..').getAttribute('open')===null)await form().locator('..').locator('summary').click();await form().locator('[data-metadata-field="name"]').fill(value);}
async function review(){await form().getByRole('button',{name:'Review construct',exact:true}).click();await page.locator('#metadata-preview-dialog').waitFor({state:'visible'});}
async function backMetadata(){await page.locator('[data-metadata-close]').click();await page.locator('#metadata-preview-dialog').waitFor({state:'hidden'});}
async function gate(suffix,fulfill){let release,mark;const opened=new Promise((r)=>mark=r),held=new Promise((r)=>release=r);const pattern='**'+suffix;
 await page.route(pattern,async(route)=>{mark();await held;if(fulfill)await route.fulfill(fulfill);else await route.continue();});
 return {opened,async finish(){const response=page.waitForResponse((r)=>r.url().includes(suffix.replace('*','')));release();await response;await page.unroute(pattern);await settle();}};
}
function csv(ref,value='7'){return 'material_ref,metric,value,unit,timestamp,conditions_json\r\n'+JSON.stringify(ref)+',independent_yield,'+value+',mg/L,2026-11-04T09:00:00+09:00,\r\n';}
async function importForm(raw){await page.getByRole('button',{name:'Import data',exact:true}).click();await page.locator('#import-format').selectOption('measurement_csv');await page.locator('#import-text').fill(raw);}
async function validate(){await page.getByRole('button',{name:'Validate & preview',exact:true}).click();}
async function closeImport(){await page.keyboard.press('Escape');await page.locator('#import-dialog').waitFor({state:'hidden'});await settle();}
(async()=>{
 server=spawn(python,['-m','workspace_app.server','--database',database,'--port','0'],{cwd:root,windowsHide:true,stdio:['ignore','pipe','pipe']});
 origin=await new Promise((resolve,reject)=>{let log='';const timer=setTimeout(()=>reject(Error('Server timeout '+log)),15000);server.stdout.on('data',(d)=>{log+=d;const found=log.match(/http:\/\/127\.0\.0\.1:\d+/);if(found){clearTimeout(timer);resolve(found[0]);}});server.stderr.on('data',(d)=>log+=d);});
 browser=await chromium.launch({headless:true,channel:process.env.PLAYWRIGHT_CHANNEL||'chrome'});page=await browser.newPage({viewport:{width:1500,height:1050}});
 page.on('pageerror',(e)=>errors.push(e.message));await page.route('**/*',async(r)=>{if(!r.request().url().startsWith(origin+'/')){outbound.push(r.request().url());await r.abort();}else await r.continue();});
 await page.goto(origin);await page.waitForFunction(()=>!document.querySelector('#project-select').disabled);await project(fixture);await page.locator(`[data-select="${m.id}"]`).check();
 await check('delayed context readouts preserve metadata and shortlist text without rerender',async()=>{
  const held=await gate('/api/construct-context?*');await expression();await held.opened;await name('UNSAVED metadata while context loads');await held.finish();assert.equal(await form().locator('[data-metadata-field="name"]').inputValue(),'UNSAVED metadata while context loads');
  await page.locator('#expression-left').selectOption(seed.constructs[0].id);await page.locator('#expression-right').selectOption(seed.constructs[1].id);await page.locator('#construct-differences').waitFor();
  // A new bundle/context is not needed: selecting the blank comparison creates a fresh exact scope.
  await page.locator('#expression-left').selectOption('');const rHeld=await gate('/api/construct-context?*');await nav('R');await rHeld.opened;await page.locator('#shortlist-reason').fill('UNSAVED source-aware shortlist question');await rHeld.finish();assert.equal(await page.locator('#shortlist-reason').inputValue(),'UNSAVED source-aware shortlist question');
 });
 await check('late metadata preview cannot replace a changed task, input or project',async()=>{
  await expression();await name('OLD metadata preview');const held=await gate('/api/metadata-preview');await form().getByRole('button',{name:'Review construct',exact:true}).click();await held.opened;await name('NEWER metadata edit');await held.finish();assert.equal(await page.locator('#metadata-preview-dialog[open]').count(),0);assert.equal(await form().locator('[data-metadata-field="name"]').inputValue(),'NEWER metadata edit');
  const foreign=await gate('/api/metadata-preview');await form().getByRole('button',{name:'Review construct',exact:true}).click();await foreign.opened;await project(other);const om=other.entities.find((e)=>e.type==='molecule');await nav('E');await page.locator(`[data-select="${om.id}"]`).check();await expression();await name('OTHER project metadata draft');await foreign.finish();assert.equal(await page.locator('#metadata-preview-dialog[open]').count(),0);assert.equal(await form().locator('[data-metadata-field="name"]').inputValue(),'OTHER project metadata draft');assert.deepEqual(await read(other.project.id),other);await project(fixture);await expression();
 });
 await check('late rejected metadata save cannot unlock or annotate a newer pending save',async()=>{
  await name('OLD rejected metadata');await review();let oldRelease,newRelease,oldMark,newMark;
  const oldHeld=new Promise((r)=>oldMark=r),newHeld=new Promise((r)=>newMark=r),oldGate=new Promise((r)=>oldRelease=r),newGate=new Promise((r)=>newRelease=r);
  await page.route('**/api/import',async(route)=>{if(route.request().postDataJSON().entities[0].name==='OLD rejected metadata'){oldMark();await oldGate;await route.fulfill({status:422,contentType:'application/json',body:JSON.stringify({error:'OBSOLETE metadata save error'})});}else{newMark();await newGate;await route.continue();}});
  await page.locator('#save-metadata').click();await oldHeld;await backMetadata();await name('CURRENT approved metadata');await review();await page.locator('#save-metadata').click();await newHeld;
  const oldResponse=page.waitForResponse((r)=>r.url().endsWith('/api/import')&&r.status()===422);oldRelease();await oldResponse;await settle();assert.equal(await page.locator('#save-metadata').isDisabled(),true);assert.doesNotMatch(await page.locator('#metadata-preview-dialog').textContent(),/OBSOLETE/);assert.doesNotMatch(await page.locator('#notification').textContent(),/OBSOLETE/);
  const newResponse=page.waitForResponse((r)=>r.url().endsWith('/api/import')&&r.status()===200);newRelease();await newResponse;await page.locator('#metadata-preview-dialog').waitFor({state:'hidden'});await page.unroute('**/api/import');await page.locator('#notification').filter({hasText:'Saved distinct construct'}).waitFor();assert.equal((await read()).entities.filter((e)=>e.name==='CURRENT approved metadata').length,1);assert.equal((await read()).entities.some((e)=>e.name==='OLD rejected metadata'),false);
 });
 await check('late metadata save retains another project and its unsaved metadata',async()=>{
  await name('ORIGINAL project saved metadata');await review();const held=await gate('/api/import');await page.locator('#save-metadata').click();await held.opened;await backMetadata();await project(other);await expression();await name('OTHER newer unsaved metadata');await held.finish();assert.equal(await page.locator('#project-select').inputValue(),other.project.id);assert.equal(await form().locator('[data-metadata-field="name"]').inputValue(),'OTHER newer unsaved metadata');assert.deepEqual(await read(other.project.id),other);assert.equal((await read()).entities.filter((e)=>e.name==='ORIGINAL project saved metadata').length,1);await project(fixture);
 });
 await check('opaque prototype tokens map exactly, changed text loses mappings, invalid UTF-8 clears prior text',async()=>{
  const before=await read();await importForm(csv('__proto__'));await validate();await page.locator('[data-measurement-map="0"]').waitFor();assert.match(await page.locator('#measurement-mapping').textContent(),/__proto__/);await page.locator('[data-measurement-map="0"]').selectOption(seed.materials[2].id);await page.locator('#apply-measurement-mappings').click();await page.locator('.preview-summary').filter({hasText:'1 valid · 0 excluded'}).waitFor();const preview=await page.locator('#import-preview').textContent();assert.match(preview,new RegExp(seed.materials[2].id));await page.locator('#back-import').click();await page.locator('#import-text').fill(csv('constructor'));await validate();await page.locator('[data-measurement-map="0"]').waitFor();assert.match(await page.locator('.preview-summary').textContent(),/0 valid · 1 excluded/);assert.equal(await page.locator('#commit-import').isDisabled(),true);assert.equal(await page.locator('[data-measurement-map="0"]').inputValue(),'');await page.locator('#back-import').click();
  await page.locator('#import-file').setInputFiles({name:'invalid-utf8.csv',mimeType:'text/csv',buffer:Buffer.from([0xff,0xfe,0x61])});await page.locator('#notification').filter({hasText:/UTF-8|encoded data|encoding|decode/i}).waitFor();assert.equal(await page.locator('#import-text').inputValue(),'');await validate();await settle();assert.equal(await page.locator('#import-preview').isHidden(),true);assert.deepEqual(await read(),before);await closeImport();
 });
 await check('late measurement preview cannot replace newer text or a changed project',async()=>{
  await importForm(csv(seed.materials[0].id));const held=await gate('/api/measurement-preview');await validate();await held.opened;await page.locator('#import-text').fill('NEWER private CSV draft');await held.finish();assert.equal(await page.locator('#import-preview').isHidden(),true);assert.equal(await page.locator('#import-text').inputValue(),'NEWER private CSV draft');
  await page.locator('#import-text').fill(csv(seed.materials[0].id));const foreign=await gate('/api/measurement-preview');await validate();await foreign.opened;await closeImport();await project(other);await foreign.finish();assert.equal(await page.locator('#import-dialog[open]').count(),0);assert.equal(await page.locator('#project-select').inputValue(),other.project.id);assert.deepEqual(await read(other.project.id),other);await project(fixture);
 });
 await check('adding a lower-ID exact-context member retains the chosen cohort and original subjects',async()=>{
  await expression();await page.locator('#expression-left').selectOption('');await page.locator('#expression-right').selectOption('');await nav('R');await page.locator('#expression-cohort').waitFor();const selected=await page.locator('#expression-cohort option').filter({hasText:'synthetic_yield / mg/L /'}).getAttribute('value');assert.ok(selected);await page.locator('#expression-cohort').selectOption(selected);await page.waitForFunction(()=>document.querySelectorAll('[data-material-observation]').length===2);
  const before=await read(),original=before.entities.find((e)=>e.id===selected),newId=selected.split('_')[0]+'_00000000-0000-4000-8000-000000000001',added={...original,id:newId,description:'SYNTHETIC extra exact-context observation, not an independent replicate'};assert.ok(newId<selected);
  await page.getByRole('button',{name:'Import data',exact:true}).click();await page.locator('#import-format').selectOption('json');await page.locator('#import-text').fill(JSON.stringify({...before,entities:[added]}));await validate();await page.locator('#commit-import').click();await page.locator('#import-dialog').waitFor({state:'hidden'});await page.waitForFunction(()=>document.querySelectorAll('[data-material-observation]').length===3);assert.equal(await page.locator('#expression-cohort').inputValue(),newId);assert.equal((await read()).entities.find((e)=>e.id===newId).subject_id,original.subject_id);assert.deepEqual((await read()).entities.filter((e)=>e.type==='evidence'&&e.id!==newId),before.entities.filter((e)=>e.type==='evidence'));
  const unknownId=seed.first.entities.find((e)=>e.type==='evidence'&&e.subject_id===seed.materials[2].id).id;await page.reload();await page.waitForFunction(()=>document.querySelectorAll('[data-material-observation]').length===3);assert.equal(await page.locator('#expression-cohort').inputValue(),newId);assert.equal(await page.locator(`[data-material-observation="${unknownId}"]`).count(),0);await page.locator('#expression-cohort').selectOption('');await page.locator(`[data-material-observation="${unknownId}"]`).waitFor();assert.match(await page.locator('#expression-observations').textContent(),/Conditions unknown|Not supplied/);
 });
 await check('late failed file decode cannot report its obsolete error in a newer valid preview',async()=>{
  await importForm('');await page.evaluate(()=>{const original=File.prototype.arrayBuffer;File.prototype.arrayBuffer=function(){if(this.name==='slow-invalid.csv')return new Promise((resolve)=>{window.releaseOldFile=()=>resolve(new Uint8Array([0xff]).buffer);});return original.call(this);};});
  await page.locator('#import-file').setInputFiles({name:'slow-invalid.csv',mimeType:'text/csv',buffer:Buffer.from([0xff])});await page.waitForFunction(()=>typeof window.releaseOldFile==='function');await page.locator('#import-file').setInputFiles({name:'valid-new.csv',mimeType:'text/csv',buffer:Buffer.from(csv(seed.materials[0].id))});await page.waitForFunction(()=>document.querySelector('#import-text').value.includes('independent_yield'));await validate();await page.locator('#commit-import').waitFor();const before=await page.locator('#notification').textContent();await page.evaluate(()=>window.releaseOldFile());await settle();assert.equal(await page.locator('#notification').textContent(),before);assert.equal(await page.locator('#import-dialog > .dialog-error').count(),0);assert.equal(await page.locator('#commit-import').isEnabled(),true);await closeImport();
 });
 const local=await page.evaluate(()=>JSON.stringify({...localStorage}));for(const token of ['UNSAVED','OTHER newer','NEWER private','GAG','__proto__','independent_yield'])assert.equal(local.includes(token),false,'No scientific draft in localStorage: '+token);
 assert.deepEqual(errors,[]);assert.deepEqual(outbound,[]);
 fs.writeFileSync(path.join(root,'TEST_EVIDENCE','M4-experiments-independent-browser-results.json'),JSON.stringify({status:'PASS',results,errors,outbound,fixture:'Clearly labelled synthetic observations; no real expression experiment',timestamp:new Date().toISOString()},null,2));
})().catch((e)=>{console.error(e);fs.writeFileSync(path.join(root,'TEST_EVIDENCE','M4-experiments-independent-browser-results.json'),JSON.stringify({status:'FAIL',results,error:String(e),errors,outbound},null,2));process.exitCode=1;}).finally(async()=>{await browser?.close();if(server&&server.exitCode===null)await new Promise((r)=>{server.once('exit',r);server.kill();});});
