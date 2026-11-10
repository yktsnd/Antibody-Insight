/* Independent P0 API and actual local WebGL replay. Temporary synthetic DB only. */
const {chromium}=require('playwright');
const {spawn,spawnSync}=require('node:child_process');
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),temp=fs.mkdtempSync(path.join(os.tmpdir(),'antibody-map-independent-'));
const python=process.env.PYTHON||path.join(root,'.venv','Scripts','python.exe'),db=path.join(temp,'legacy.sqlite3');
const output=process.argv[2];assert(output,'Supply a fresh output JSON path');assert(!fs.existsSync(output),'Never overwrite independent evidence');
const prep=spawnSync(python,['-c',`
import copy,json,runpy,sys
from contextlib import closing
from workspace_app.storage import Store
n=runpy.run_path('TEST_EVIDENCE/M6-mapping-independent-probe.py')
b=n['bundle'](n['pdb']([(1,''),(2,'')]),indexes=[2,1])
s=Store(sys.argv[1])
with closing(s.connect()) as conn,conn:
 conn.execute('INSERT INTO projects VALUES (?,?)',(b['project']['id'],json.dumps(b['project'])))
 for e in b['entities']:s._insert(conn,e)
good=n['bundle'](n['pdb']([(10,''),(10,'A'),(15,'')]),indexes=[1,3,4])
print(json.dumps({'legacy':b,'good':good}))
`,db],{cwd:root,encoding:'utf8',windowsHide:true});assert.equal(prep.status,0,prep.stderr);
const {legacy,good}=JSON.parse(prep.stdout),molecule=legacy.entities.find(e=>e.type==='molecule'),structure=legacy.entities.find(e=>e.type==='structure'),badMap=legacy.entities.find(e=>e.type==='structure_map');
let child,origin,browser;const results=[],errors=[],outbound=[];
async function api(page,route,data){return page.evaluate(async({route,data})=>{const boot=await(await fetch('/api/bootstrap')).json();const r=await fetch(route,data===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':boot.csrf},body:JSON.stringify(data)});return{status:r.status,data:await r.json()};},{route,data});}
async function check(name,fn){await fn();results.push({name,status:'PASS'});console.log('PASS',name);}
async function start(){child=spawn(python,['-m','workspace_app.server','--database',db,'--port','0'],{cwd:root,windowsHide:true,stdio:['ignore','pipe','pipe']});origin=await new Promise((resolve,reject)=>{let text='';const timer=setTimeout(()=>reject(Error('Server timeout '+text)),15000);child.stdout.on('data',d=>{text+=d;const match=text.match(/http:\/\/127\.0\.0\.1:\d+/);if(match){clearTimeout(timer);resolve(match[0]);}});child.stderr.on('data',d=>text+=d);child.on('exit',c=>{clearTimeout(timer);reject(Error('Server exited '+c+' '+text));});});}
async function viewer(page){await page.waitForFunction(id=>!!StructureUI.contextFor(id)?.viewer,molecule.id);}
async function sourceClick(page,author,insertion=''){
 const host=page.locator(`[data-structure-host="${molecule.id}"] .coordinate-canvas`);await host.scrollIntoViewIfNeeded();
 const point=await page.evaluate(({id,author,insertion})=>{const c=StructureUI.contextFor(id),a=c.data.parsed.atoms.find(a=>a.auth_number===author&&a.insertion_code===insertion);assertSource(a);function assertSource(a){if(!a)throw Error('Source unavailable');}const rendered=c.viewer.selectedAtoms({serial:a.index+1})[0],p=c.viewer.modelToScreen(rendered);return{x:p.x-window.scrollX,y:p.y-window.scrollY};},{id:molecule.id,author,insertion});
 await page.mouse.click(point.x,point.y);
}
function definition(mapping){const {structure_id,molecule_id,source,chain_assignments,residues}=mapping;return{structure_id,molecule_id,source,chain_assignments,residues};}
(async()=>{
 await start();browser=await chromium.launch({headless:true,channel:process.env.PLAYWRIGHT_CHANNEL||'chrome',args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const context=await browser.newContext({viewport:{width:1500,height:1100}}),page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
 await context.route('**/*',async route=>{if(!route.request().url().startsWith(origin+'/')){outbound.push(route.request().url());await route.abort();}else await route.continue();});
 await page.goto(origin);await page.locator('#candidate-count').filter({hasText:'1'}).waitFor();
 await check('API map preview refuses reversed identical amino acids in a legacy project',async()=>{
   const response=await api(page,'/api/structure-map-preview',{project_id:legacy.project.id,definition:definition(badMap)});
   assert.equal(response.status,422);assert.match(response.data.error,/order/);
 });
 await check('Native awx file preview refuses both complete and append-file reversed maps',async()=>{
   const complete=await api(page,'/api/preview',{text:JSON.stringify(legacy),format:'json',filename:'inverse-complete.awx.json',project_id:null,title:'',goal:''});
   assert.equal(complete.status,422);assert.match(complete.data.error,/order/);
   const incoming=structuredClone(badMap);incoming.id='smp_'+crypto.randomUUID();
   const append={schema_version:legacy.schema_version,project:legacy.project,entities:[incoming]};
   const response=await api(page,'/api/preview',{text:JSON.stringify(append),format:'json',filename:'inverse-append.awx.json',project_id:legacy.project.id,title:'',goal:''});
   assert.equal(response.status,422);assert.match(response.data.error,/order/);
   const after=await api(page,'/api/bundle?project_id='+legacy.project.id);assert.deepEqual(after.data.entities,legacy.entities);
 });
 await check('Direct import refuses a new reversed map and leaves all prior entities exact',async()=>{
   const before=await api(page,'/api/bundle?project_id='+legacy.project.id),incoming=structuredClone(badMap);incoming.id='smp_'+crypto.randomUUID();
   const response=await api(page,'/api/import',{schema_version:legacy.schema_version,project:legacy.project,entities:[incoming]});assert.equal(response.status,422);assert.match(response.data.error,/order/);
   const after=await api(page,'/api/bundle?project_id='+legacy.project.id);assert.deepEqual(after,before);
 });
 await check('Legacy contradictory map renders an explicit warning and never highlights sequence-linked atoms',async()=>{
   await page.getByRole('checkbox',{name:'Select STR-001',exact:true}).check();await page.locator('nav [data-screen="W"]').click();await viewer(page);
   assert.match(await page.locator('.declared-struct-chains').textContent(),/Sequence order contradicts/);
   await page.getByRole('button',{name:'STR-001 H sequence index 1 A',exact:true}).click();await viewer(page);
   const observed=await page.evaluate(id=>{const c=StructureUI.contextFor(id);return{map:c.data.map,status:c.data.mapping_status,atoms:c.selectionAtoms.length,focus:c.host.querySelector('[data-focus-structure]').disabled};},molecule.id);
   assert.deepEqual(observed,{map:null,status:'contradictory',atoms:0,focus:true});assert.match(await page.locator('.structure-selection').textContent(),/Mapping unavailable/);
 });
 await check('Actual coordinate click on quarantined source stays source-only and cannot select a sequence residue',async()=>{
   await sourceClick(page,2);await viewer(page);await page.getByText('Structure selection is unmapped:',{exact:false}).waitFor();
   assert.equal(await page.locator('.residue.active').count(),0);assert.match(await page.locator('.structure-selection').textContent(),/Source-only selection.*author H:2/);
   const refs=await page.evaluate(id=>StructureUI.hypothesisContexts([id]),molecule.id);assert.equal(refs[0].structure_map_id,null);assert.equal(refs[0].residue.source_key.auth_number,2);
 });
 await check('Ordinary correspondence editor rejects reverse identical residues before offering Save',async()=>{
   await page.locator(`[data-edit-correspondence="${molecule.id}"]`).click();
   await page.locator('[data-map-role="0"]').selectOption('antibody');await page.locator('[data-map-chain="0"]').selectOption('H');
   const pairs=await page.evaluate(id=>StructureUI.contextFor(id).data.parsed.residues.map(r=>({uid:r.uid,author:r.auth_number})),molecule.id);
   for(const [index,author] of [[1,2],[2,1]]){await page.locator('#map-pair-index').fill(String(index));await page.locator('#map-pair-residue').selectOption(pairs.find(r=>r.author===author).uid);await page.locator('[data-map-add-pair]').click();}
   await page.locator('[data-map-preview]').click();await page.locator('#structure-map-dialog .dialog-error').filter({hasText:'Sequence order contradicts'}).waitFor();
   assert.equal(await page.locator('[data-map-save]').count(),0);await page.getByRole('button',{name:'Close correspondence editor',exact:true}).click();
   const after=await api(page,'/api/bundle?project_id='+legacy.project.id);assert.deepEqual(after.data.entities,legacy.entities);
 });
 let goodMapId;
 await check('Explicit valid map retains molecule identity and a distinct gap-bearing molecule saves',async()=>{
   const nextStructure=structuredClone(good.entities.find(e=>e.type==='structure'));nextStructure.id='stc_'+crypto.randomUUID();
   const source=await api(page,'/api/import',{schema_version:legacy.schema_version,project:legacy.project,entities:[nextStructure]});assert.equal(source.status,200);
   const map=structuredClone(good.entities.find(e=>e.type==='structure_map'));map.structure_id=nextStructure.id;
   const preview=await api(page,'/api/structure-map-preview',{project_id:legacy.project.id,definition:definition(map)});
   // The stored molecule has two positions; add a distinct molecule with the gap-bearing four-residue sequence instead of changing its identity.
   assert.equal(preview.status,422);assert.match(preview.data.error,/position|amino acid|chain/i);
   const fresh=structuredClone(good);fresh.project.id='prj_'+crypto.randomUUID();fresh.project.title='[SYNTHETIC FIXTURE] Independent insertion and gap';
   const ids=new Map(fresh.entities.map(e=>[e.id,e.type==='molecule'?'mol_'+crypto.randomUUID():e.type==='structure'?'stc_'+crypto.randomUUID():'smp_'+crypto.randomUUID()]));
   for(const e of fresh.entities){e.project_id=fresh.project.id;e.id=ids.get(e.id);if(e.molecule_id)e.molecule_id=ids.get(e.molecule_id);if(e.structure_id)e.structure_id=ids.get(e.structure_id);}
   const validMap=fresh.entities.find(e=>e.type==='structure_map');fresh.entities=fresh.entities.filter(e=>e.type!=='structure_map');
   const created=await api(page,'/api/import',fresh);assert.equal(created.status,200);
   const validPreview=await api(page,'/api/structure-map-preview',{project_id:fresh.project.id,definition:definition(validMap)});assert.equal(validPreview.status,200);
   const saved=await api(page,'/api/import',validPreview.data);assert.equal(saved.status,200);goodMapId=validPreview.data.entities[0].id;
   const newSource=fresh.entities.find(e=>e.type==='structure'),view=await api(page,`/api/structure-view?project_id=${fresh.project.id}&structure_id=${newSource.id}&map_id=${goodMapId}`);assert.equal(view.status,200);assert.equal(view.data.mapping_status,'verified');assert.equal(view.data.map.id,goodMapId);
   // Use that second project through the actual UI for bidirectional selection.
   await page.reload();await page.locator('#project-select').selectOption(fresh.project.id);await page.getByRole('checkbox',{name:'Select STR-001',exact:true}).check();await page.locator('nav [data-screen="W"]').click();
   // Retain this new molecule's actual identity for the next check.
   globalThis.validMolecule=fresh.entities.find(e=>e.type==='molecule');
 });
 await check('Actual valid gap/insertion selection works from sequence and from WebGL atom',async()=>{
   const id=globalThis.validMolecule.id;await page.waitForFunction(id=>!!StructureUI.contextFor(id)?.viewer,id);
   await page.getByRole('button',{name:'STR-001 H sequence index 3 A',exact:true}).click();await page.waitForFunction(id=>StructureUI.contextFor(id)?.selectionAtoms?.length===1,id);
   const selected=await page.evaluate(id=>{const c=StructureUI.contextFor(id);return c.selectionAtoms.map(a=>[a.auth_number,a.insertion_code]);},id);assert.deepEqual(selected,[[10,'A']]);
   const host=page.locator(`[data-structure-host="${id}"] .coordinate-canvas`);await host.scrollIntoViewIfNeeded();
   const point=await page.evaluate(id=>{const c=StructureUI.contextFor(id),a=c.data.parsed.atoms.find(a=>a.auth_number===15),p=c.viewer.modelToScreen(c.viewer.selectedAtoms({serial:a.index+1})[0]);return{x:p.x-window.scrollX,y:p.y-window.scrollY};},id);await page.mouse.click(point.x,point.y);
   await page.waitForFunction(id=>StructureUI.contextFor(id)?.host.querySelector('.structure-selection').textContent.includes('Mapped H raw index 4'),id);
   assert.equal(await page.getByRole('button',{name:'STR-001 H sequence index 4 A',exact:true}).evaluate(e=>e.classList.contains('active')),true);
 });
 assert.deepEqual(errors,[]);assert.deepEqual(outbound,[]);
 results.push({name:'No browser errors or external requests',status:'PASS'});
})().catch(error=>{results.push({name:'Independent replay interrupted',status:'FAIL',error:error.stack});console.error(error);process.exitCode=1;}).finally(async()=>{
 if(browser)await browser.close();if(child&&child.exitCode===null)await new Promise(resolve=>{child.once('exit',resolve);child.kill();});
 const sources={};for(const name of ['workspace_app/structures.py','workspace_app/domain.py','workspace_app/storage.py','workspace_app/hypotheses.py','workspace_app/server.py','web/structures.js'])sources[name]=crypto.createHash('sha256').update(fs.readFileSync(path.join(root,name))).digest('hex');
 fs.writeFileSync(output,JSON.stringify({reviewer:'/root/mapping_review',status:results.every(r=>r.status==='PASS')?'PASS':'FAIL',scope:'P0 API and actual WebGL only; synthetic engineering evidence, not real scientific validation',database:db,results,source_hashes_at_completion:sources},null,2));
});
