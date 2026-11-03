/* F08 actual local WebGL interaction; synthetic fixtures, no final journey claim. */
const {chromium}=require('playwright');
const {spawn}=require('node:child_process');
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),out=path.join(root,'TEST_EVIDENCE'),temp=fs.mkdtempSync(path.join(os.tmpdir(),'antibody-structure-'));
const python=process.env.PYTHON||path.join(root,'.venv','Scripts','python.exe'),database=path.join(temp,'source.sqlite3');
let child,origin,browser;const results=[];
async function start(db=database,port=0){child=spawn(python,['-m','workspace_app.server','--database',db,'--port',String(port)],{cwd:root,windowsHide:true,stdio:['ignore','pipe','pipe']});origin=await new Promise((resolve,reject)=>{let text='';const t=setTimeout(()=>reject(new Error('Server timeout '+text)),15000);child.stdout.on('data',(d)=>{text+=d;const m=text.match(/http:\/\/127\.0\.0\.1:\d+/);if(m){clearTimeout(t);resolve(m[0]);}});child.stderr.on('data',(d)=>text+=d);child.on('exit',(c)=>{clearTimeout(t);reject(new Error('Server exited '+c+' '+text));});});}
async function stop(){if(child&&child.exitCode===null)await new Promise((resolve)=>{child.once('exit',resolve);child.kill();});}
async function check(name,action){const t=Date.now();await action();results.push({name,status:'PASS',duration_ms:Date.now()-t});console.log('PASS',name);}
function record(name,value){const target=path.resolve(out,name),pending=path.resolve(out,name+'.pending-'+Date.now());assert.equal(path.dirname(target),out);fs.writeFileSync(pending,JSON.stringify(value,null,2));fs.renameSync(pending,target);}
async function api(page,route,data){return page.evaluate(async({route,data})=>{const boot=await(await fetch('/api/bootstrap')).json();const r=await fetch(route,{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':boot.csrf},body:JSON.stringify(data)});return{status:r.status,data:await r.json()};},{route,data});}
async function viewer(page,id){await page.waitForFunction((id)=>!!window.StructureUI?.contextFor(id)?.viewer,id);}
async function sourceClick(page,id,source){
  const host=page.locator(`[data-structure-host="${id}"] .coordinate-canvas`);await host.scrollIntoViewIfNeeded();
  const point=await page.evaluate(({id,source})=>{const c=StructureUI.contextFor(id);const atom=c.data.parsed.atoms.find((a)=>a.model===c.model&&a.auth_chain===source.chain&&a.auth_number===source.number&&(source.ins===undefined||a.insertion_code===source.ins)&&(source.alt===undefined||a.altloc===source.alt));if(!atom)throw new Error('Source atom not found');const rendered=c.viewer.selectedAtoms({serial:atom.index+1})[0];const p=c.viewer.modelToScreen(rendered);return{x:p.x-window.scrollX,y:p.y-window.scrollY};},{id,source});
  await page.mouse.click(point.x,point.y);
}

(async()=>{
 await start();browser=await chromium.launch({headless:true,channel:process.env.PLAYWRIGHT_CHANNEL||'chrome',args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const context=await browser.newContext({viewport:{width:1500,height:1000},acceptDownloads:true}),page=await context.newPage();const errors=[],outbound=[];
 page.on('pageerror',(e)=>errors.push(e.message));await context.route('**/*',async(r)=>{if(!r.request().url().startsWith(origin+'/')){outbound.push(r.request().url());await r.abort();}else await r.continue();});
 await page.goto(origin);let bundle,molecules,structures;
 await check('PDB and mmCIF fixture preview is local and explicit',async()=>{
  await page.getByRole('button',{name:'Import data',exact:true}).click();await page.getByRole('button',{name:'Preview structure fixture',exact:true}).click();
  await page.getByRole('button',{name:/Save \d+ valid rows/}).click();await page.locator('#candidate-count').filter({hasText:'2'}).waitFor();
  bundle=await page.evaluate(async()=>{const p=(await(await fetch('/api/bootstrap')).json()).projects[0];return await(await fetch('/api/bundle?project_id='+p.id)).json();});
  molecules=bundle.entities.filter((e)=>e.type==='molecule');structures=bundle.entities.filter((e)=>e.type==='structure');
  await page.getByRole('checkbox',{name:'Select STR-001',exact:true}).check();await page.getByRole('checkbox',{name:'Select STR-002',exact:true}).check();
  await page.locator('nav [data-screen="W"]').click();
  assert.equal(await page.locator('canvas').count(),0);
  await page.getByRole('combobox',{name:'Source model for STR-001',exact:true}).selectOption('1');await viewer(page,molecules[0].id);
  await page.getByRole('combobox',{name:'Source model for STR-002',exact:true}).selectOption('1');await viewer(page,molecules[1].id);
  await page.getByText('synthetic-fixture:TARGET-001',{exact:false}).first().waitFor();
  assert.equal(await page.locator('.coordinate-canvas canvas').count(),2);
 });
 await check('actual structure click distinguishes author chain and insertion then selects exact sequence',async()=>{
  await sourceClick(page,molecules[0].id,{chain:'H',number:3,ins:'A'});await viewer(page,molecules[0].id);
  await page.waitForFunction((id)=>StructureUI.contextFor(id)?.host.querySelector('.structure-selection').textContent.includes('Mapped H raw index 4'),molecules[0].id);
  assert.equal(await page.getByRole('combobox',{name:'Chain for STR-001',exact:true}).inputValue(),'H');
  await sourceClick(page,molecules[0].id,{chain:'L',number:1,ins:''});await viewer(page,molecules[0].id);
  assert.equal(await page.getByRole('combobox',{name:'Chain for STR-001',exact:true}).inputValue(),'L');
  assert.match(await page.locator(`[data-structure-host="${molecules[0].id}"] .structure-selection`).textContent(),/Mapped L raw index 1/);
  await sourceClick(page,molecules[1].id,{chain:'H-author',number:103,ins:'A'});await viewer(page,molecules[1].id);
  await page.waitForFunction((id)=>StructureUI.contextFor(id)?.host.querySelector('.structure-selection').textContent.includes('Mapped H raw index 4'),molecules[1].id);
  assert.match(await page.locator(`[data-structure-host="${molecules[1].id}"] .structure-selection`).textContent(),/label VH:4/);
  assert.equal(await page.locator('#selection-count').textContent(),'2 selected');
 });
 await check('sequence click highlights mapped source; missing coordinate and alternate B never fall back',async()=>{
  await page.getByRole('combobox',{name:'Chain for STR-001',exact:true}).selectOption('H');
  await page.getByRole('button',{name:'STR-001 H sequence index 2 C',exact:true}).click();await viewer(page,molecules[0].id);
  await page.waitForFunction((id)=>StructureUI.contextFor(id)?.host.querySelector('.structure-selection').textContent.includes('Mapped H raw index 2'),molecules[0].id);
  await page.getByRole('button',{name:'STR-001 H sequence index 3 D',exact:true}).click();await viewer(page,molecules[0].id);
  await page.waitForFunction((id)=>StructureUI.contextFor(id)?.host.querySelector('.structure-selection').textContent.includes('Mapping unavailable'),molecules[0].id);
  await sourceClick(page,molecules[0].id,{chain:'H',number:4,alt:'B'});await page.getByText('Structure selection is unmapped:',{exact:false}).waitFor();
  assert.equal(await page.locator('.residue.active').count(),0);
 });
 let savedView;
 await check('physical rotation links orientation and zoom while preserving separate centers',async()=>{
  await viewer(page,molecules[0].id);await viewer(page,molecules[1].id);
  await page.locator('[data-link-views]').first().check();
  assert.deepEqual(await page.locator('[data-link-views]').evaluateAll((nodes)=>nodes.map((n)=>n.checked)),[true,true]);
  const canvas=page.locator(`[data-structure-host="${molecules[0].id}"] .coordinate-canvas`);await canvas.scrollIntoViewIfNeeded();const r=await canvas.boundingBox();
  const beforeViews=await page.evaluate((ids)=>ids.map((id)=>StructureUI.viewerFor(id).getView()),molecules.map((m)=>m.id));
  const before=beforeViews[0];
  await page.mouse.move(r.x+r.width*.45,r.y+r.height*.55);await page.mouse.down();await page.mouse.move(r.x+r.width*.65,r.y+r.height*.65,{steps:10});await page.mouse.up();
  const rotated=await page.evaluate((id)=>StructureUI.viewerFor(id).getView(),molecules[0].id);
  assert.notDeepEqual(rotated.slice(4),before.slice(4));
  await page.mouse.wheel(0,-80);await page.waitForFunction(({id,z})=>StructureUI.viewerFor(id).getView()[3]!==z,{id:molecules[0].id,z:rotated[3]});
  const views=await page.evaluate((ids)=>ids.map((id)=>StructureUI.viewerFor(id).getView()),molecules.map((m)=>m.id));
  assert.deepEqual(views[0].slice(3),views[1].slice(3));assert.deepEqual(views[0].slice(0,3),beforeViews[0].slice(0,3));assert.deepEqual(views[1].slice(0,3),beforeViews[1].slice(0,3));
  assert.notDeepEqual(views[0].slice(0,3),views[1].slice(0,3));savedView=views[0];
  await page.evaluate(()=>window.scrollTo(0,0));await page.screenshot({path:path.join(out,'M2-structure-screen.png'),fullPage:true});
 });
 await check('model-scoped confidence differs and missing confidence never comes from B values',async()=>{
  const first=page.locator(`[data-structure-host="${molecules[0].id}"]`),second=page.locator(`[data-structure-host="${molecules[1].id}"]`);
  assert.match(await first.locator('.struct-confidence').textContent(),/0.82.*declared model 1/);assert.match(await second.locator('.struct-confidence').textContent(),/No model-scoped confidence/);
  await page.getByRole('combobox',{name:'Source model for STR-001',exact:true}).selectOption('2');await viewer(page,molecules[0].id);
  await page.waitForFunction((id)=>StructureUI.contextFor(id)?.model===2,molecules[0].id);assert.match(await first.locator('.struct-confidence').textContent(),/0.66.*declared model 2/);
  await viewer(page,molecules[1].id);
  const changedModelViews=await page.evaluate((ids)=>ids.map((id)=>StructureUI.viewerFor(id).getView().slice(3)),molecules.map((m)=>m.id));assert.deepEqual(changedModelViews[0],changedModelViews[1]);
  await page.getByRole('combobox',{name:'Source model for STR-001',exact:true}).selectOption('1');await viewer(page,molecules[0].id);
  await page.locator('nav [data-screen="R"]').click();await page.getByText('ipTM',{exact:true}).first().waitFor();
  assert.equal(await page.locator('.tag.measured').count(),0);await page.locator('nav [data-screen="W"]').click();await viewer(page,molecules[0].id);
  assert.deepEqual(await page.evaluate((id)=>StructureUI.viewerFor(id).getView(),molecules[0].id),savedView);
 });
 await check('newly imported model evidence refreshes the structural observation cache',async()=>{
  const source=structuredClone(bundle.entities.find((e)=>e.type==='evidence'));source.id='evd_c5588928-36fb-4770-8fd6-350ac0265c37';source.subject_id=structures[1].id;source.metric='pTM';source.value=.51;source.conditions={structure_model:1,purpose:'synthetic cache refresh'};
  await page.getByRole('button',{name:'Import data',exact:true}).click();await page.locator('#import-format').selectOption('json');await page.locator('#import-text').fill(JSON.stringify({schema_version:bundle.schema_version,project:bundle.project,entities:[source]}));
  await page.getByRole('button',{name:'Validate & preview',exact:true}).click();await page.getByRole('button',{name:'Save 1 valid rows',exact:true}).click();await page.locator('nav [data-screen="W"]').click();await viewer(page,molecules[1].id);
  await page.locator(`[data-structure-host="${molecules[1].id}"] .struct-confidence`).filter({hasText:'pTM: 0.51'}).waitFor();
 });
 await check('GUI reviews and saves an immutable explicit correspondence revision',async()=>{
  await page.locator(`[data-edit-correspondence="${molecules[0].id}"]`).click();
  await page.getByRole('button',{name:'Validate & review new map',exact:true}).click();await page.getByRole('heading',{name:'Review new immutable map',exact:true}).waitFor();
  const response=page.waitForResponse((r)=>r.url().endsWith('/api/import')&&r.request().method()==='POST');await page.getByRole('button',{name:'Save correspondence',exact:true}).click();assert.equal((await response).status(),200);
  await viewer(page,molecules[0].id);const after=await page.evaluate(async(id)=>await(await fetch('/api/bundle?project_id='+id)).json(),bundle.project.id);
  assert.equal(after.entities.filter((e)=>e.type==='structure_map').length,5);assert.deepEqual(after.entities.slice(0,bundle.entities.length),bundle.entities);
 });
 await check('raw PDB import and manual chain/residue pairing work without inferred correspondence',async()=>{
  await page.getByRole('button',{name:'Import data',exact:true}).click();await page.locator('#import-format').selectOption('pdb');
  await page.locator('#structure-molecule').selectOption(molecules[0].id);await page.locator('#structure-source').fill('SYNTHETIC raw coordinate import; no model run');
  await page.locator('#import-text').fill(structures[0].content);await page.getByRole('button',{name:'Validate & preview',exact:true}).click();
  const response=page.waitForResponse((r)=>r.url().endsWith('/api/import')&&r.request().method()==='POST');await page.getByRole('button',{name:'Save 1 valid rows',exact:true}).click();assert.equal((await response).status(),200);
  await page.locator('nav [data-screen="W"]').click();
  const updated=await page.evaluate(async(id)=>await(await fetch('/api/bundle?project_id='+id)).json(),bundle.project.id);
  const raw=updated.entities.find((e)=>e.type==='structure'&&!structures.some((s)=>s.id===e.id));assert.equal(raw.origin_kind,'unknown');assert.equal(raw.content,structures[0].content);
  await page.getByRole('combobox',{name:'Structure for STR-001',exact:true}).selectOption(raw.id);await page.getByRole('combobox',{name:'Source model for STR-001',exact:true}).selectOption('1');await viewer(page,molecules[0].id);
  await page.locator(`[data-edit-correspondence="${molecules[0].id}"]`).click();
  await page.locator('[data-map-role="0"]').selectOption('antibody');await page.locator('[data-map-chain="0"]').selectOption('H');
  await page.locator('[data-map-role="1"]').selectOption('antibody');await page.locator('[data-map-chain="1"]').selectOption('L');
  await page.locator('[data-map-role="2"]').selectOption('antigen');await page.locator('[data-target-namespace="2"]').fill('synthetic-fixture');await page.locator('[data-target-identifier="2"]').fill('TARGET-001');
  await page.locator('#map-pair-chain').selectOption('H');await page.locator('#map-pair-index').fill('2');
  const residue=await page.evaluate((id)=>StructureUI.contextFor(id).data.parsed.residues.find((r)=>r.model===1&&r.auth_chain==='H'&&r.auth_number===1).uid,molecules[0].id);
  await page.locator('#map-pair-residue').selectOption(residue);await page.getByRole('button',{name:'Add / replace explicit pair',exact:true}).click();
  await page.getByRole('button',{name:'Validate & review new map',exact:true}).click();await page.locator('#structure-map-dialog .dialog-error').filter({hasText:'amino acid differ'}).waitFor();
  await page.locator('#map-pair-index').fill('1');await page.getByRole('button',{name:'Add / replace explicit pair',exact:true}).click();
  // Remove the intentionally wrong index2 pair before saving the corrected index1 mapping.
  await page.locator('[data-map-remove="0"]').click();
  await page.getByRole('button',{name:'Validate & review new map',exact:true}).click();
  const savedResponse=page.waitForResponse((r)=>r.url().endsWith('/api/import')&&r.request().method()==='POST');
  await page.getByRole('button',{name:'Save correspondence',exact:true}).click();assert.equal((await savedResponse).status(),200);
  await page.locator('#structure-map-dialog').waitFor({state:'hidden'});
  // Wait for this saved revision, not a viewer from before the asynchronous save.
  await page.waitForFunction(({id,sourceId})=>{const c=StructureUI.contextFor(id);return c?.viewer&&c.data.structure.id===sourceId&&c.data.map?.residues.length===1;},{id:molecules[0].id,sourceId:raw.id});
  await page.getByRole('button',{name:'STR-001 H sequence index 1 A',exact:true}).click();await viewer(page,molecules[0].id);
  await page.waitForFunction((id)=>StructureUI.contextFor(id)?.host.querySelector('.structure-selection').textContent.includes('Mapped H raw index 1'),molecules[0].id);
  await sourceClick(page,molecules[0].id,{chain:'L',number:1});await page.getByText('Structure selection is unmapped:',{exact:false}).waitFor();
  // Return to the original comparison source/camera for the restart audit.
  await page.getByRole('combobox',{name:'Structure for STR-001',exact:true}).selectOption(structures[0].id);await viewer(page,molecules[0].id);
 });
 await check('missing CIF model identity remains unknown and viewable without invented model one',async()=>{
  const source=structuredClone(structures[1]);source.id='stc_b4a86cf6-c852-4d73-9b8f-2eedc7879184';source.name='Synthetic unknown-model CIF';source.origin_kind='unknown';
  source.content=source.content.split('\n').filter((line)=>line!=='_atom_site.pdbx_PDB_model_num'&&(!line.startsWith('ATOM ')||line.endsWith(' 1'))).map((line)=>line.startsWith('ATOM ')?line.split(' ').slice(0,-1).join(' '):line).join('\n');
  source.sha256=require('node:crypto').createHash('sha256').update(source.content).digest('hex');
  await page.getByRole('button',{name:'Import data',exact:true}).click();await page.locator('#import-format').selectOption('json');await page.locator('#import-text').fill(JSON.stringify({schema_version:bundle.schema_version,project:bundle.project,entities:[source]}));
  await page.getByRole('button',{name:'Validate & preview',exact:true}).click();await page.getByRole('button',{name:'Save 1 valid rows',exact:true}).click();await page.locator('nav [data-screen="W"]').click();
  await page.getByRole('combobox',{name:'Structure for STR-002',exact:true}).selectOption(source.id);await viewer(page,molecules[1].id);
  assert.equal(await page.getByRole('combobox',{name:'Source model for STR-002',exact:true}).inputValue(),'unknown');
  assert.equal(await page.evaluate((id)=>StructureUI.contextFor(id).model,molecules[1].id),null);
  assert.equal(await page.locator(`[data-edit-correspondence="${molecules[1].id}"]`).isDisabled(),true);
  await page.getByRole('combobox',{name:'Structure for STR-002',exact:true}).selectOption(structures[1].id);await viewer(page,molecules[1].id);
 });
 await check('project switching keeps structural IDs and camera context in their own project',async()=>{
  await page.getByRole('button',{name:'Import data',exact:true}).click();await page.getByRole('button',{name:'Preview synthetic example',exact:true}).click();await page.getByRole('button',{name:/Save \d+ valid rows/}).click();await page.locator('#candidate-count').filter({hasText:'8'}).waitFor();
  const stored=await page.evaluate(()=>{const id=localStorage.getItem('awx-project');return JSON.parse(localStorage.getItem('awx-state-'+id));});
  assert.deepEqual(stored.structureViews,{});assert.deepEqual(stored.structureResidues,{});
  await page.getByRole('combobox',{name:'Project',exact:true}).selectOption(bundle.project.id);await viewer(page,molecules[0].id);
  assert.equal(await page.locator('#selection-count').textContent(),'2 selected');
 });
 await check('restart and JSON roundtrip preserve original coordinates maps evidence and camera context',async()=>{
  const before=await page.evaluate(async(id)=>await(await fetch('/api/bundle?project_id='+id)).json(),bundle.project.id);const port=Number(new URL(origin).port);
  await stop();await start(database,port);await page.reload();await viewer(page,molecules[0].id);assert.equal(await page.locator('#selection-count').textContent(),'2 selected');
  const current=await page.evaluate(async(id)=>await(await fetch('/api/bundle?project_id='+id)).json(),bundle.project.id);assert.deepEqual(current,before);
  assert.deepEqual(await page.evaluate((id)=>StructureUI.viewerFor(id).getView(),molecules[0].id),savedView);
  const storage=await page.evaluate(()=>Object.fromEntries(Object.keys(localStorage).map((k)=>[k,localStorage.getItem(k)])));
  for(const s of structures) assert.equal(JSON.stringify(storage).includes(s.content.slice(0,100)),false);
  await stop();await start(path.join(temp,'fresh.sqlite3'));await page.goto(origin);await page.getByRole('button',{name:'Import data',exact:true}).click();await page.locator('#import-format').selectOption('json');await page.locator('#import-text').fill(JSON.stringify(before));
  await page.getByRole('button',{name:'Validate & preview',exact:true}).click();await page.getByRole('button',{name:/Save \d+ valid rows/}).click();await page.locator('#candidate-count').filter({hasText:'2'}).waitFor();
  const copied=await page.evaluate(async(id)=>await(await fetch('/api/bundle?project_id='+id)).json(),bundle.project.id);assert.deepEqual(copied,before);
  const bad=structuredClone(before);bad.entities.find((e)=>e.type==='structure').sha256='0'.repeat(64);assert.equal((await api(page,'/api/import',bad)).status,422);
  assert.deepEqual(await page.evaluate(async(id)=>await(await fetch('/api/bundle?project_id='+id)).json(),bundle.project.id),before);
 });
 assert.deepEqual(errors,[]);assert.deepEqual(outbound,[]);record('M2-structure-browser-results.json',{scope:'F08 structural observation; full J03/J04/J08 still require later steps',status:'PASS',timestamp:new Date().toISOString(),browser:await browser.version(),results,no_outbound:true,no_javascript_errors:true});console.log('PASS F08 browser checks',results.length);
})().catch((error)=>{console.error(error);record('M2-structure-browser-failure.json',{error:String(error),results});process.exitCode=1;}).finally(async()=>{if(browser)await browser.close();await stop();});
