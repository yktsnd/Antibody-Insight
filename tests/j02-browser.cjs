/* Complete J02 engineering path, with actual source-coordinate design and restart. */
const {chromium}=require('playwright');
const {spawn,spawnSync}=require('node:child_process');
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),out=path.join(root,'TEST_EVIDENCE'),temp=fs.mkdtempSync(path.join(os.tmpdir(),'antibody-j02-'));
const python=process.env.PYTHON||'python',database=path.join(temp,'design.sqlite3'),results=[],steps=[];let child,origin,browser;
function record(name,data){const target=path.join(out,name),pending=target+'.pending-'+crypto.randomUUID();fs.writeFileSync(pending,JSON.stringify(data,null,2));fs.renameSync(pending,target);}
async function start(db=database,port=0){child=spawn(python,['-m','workspace_app.server','--database',db,'--port',String(port)],{cwd:root,windowsHide:true,stdio:['ignore','pipe','pipe']});origin=await new Promise((resolve,reject)=>{let log='';const timer=setTimeout(()=>reject(Error('Server timeout '+log)),15000);child.stdout.on('data',(data)=>{log+=data;const m=log.match(/http:\/\/127\.0\.0\.1:\d+/);if(m){clearTimeout(timer);resolve(m[0]);}});child.stderr.on('data',(data)=>log+=data);child.on('exit',(code)=>{clearTimeout(timer);reject(Error('Server exited '+code+' '+log));});});}
async function stop(){if(child&&child.exitCode===null)await new Promise((resolve)=>{child.once('exit',resolve);child.kill();});}
async function check(name,fn){const time=Date.now();await fn();results.push({name,status:'PASS',duration_ms:Date.now()-time});console.log('PASS',name);}
async function post(page,route,data){return page.evaluate(async({route,data})=>{const boot=await(await fetch('/api/bootstrap')).json();const r=await fetch(route,{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':boot.csrf},body:JSON.stringify(data)});return{status:r.status,data:await r.json()};},{route,data});}
async function nav(page,screen){await page.locator(`nav [data-screen="${screen}"]`).click();}
async function bundle(page,id){return page.evaluate(async(id)=>await(await fetch('/api/bundle?project_id='+id)).json(),id);}
async function download(page,name){const wait=page.waitForEvent('download');await page.getByRole('button',{name:'Export JSON',exact:true}).click();const d=await wait,p=path.join(temp,name);await d.saveAs(p);return{path:p,bundle:JSON.parse(fs.readFileSync(p,'utf8'))};}

(async()=>{
  const file=path.join(temp,'synthetic-parent-reference.json');
  const generated=spawnSync(python,['-c',"from pathlib import Path; import sys,json; from workspace_app.design_fixtures import design_bundle; Path(sys.argv[1]).write_text(json.dumps(design_bundle()),encoding='utf-8')",file],{cwd:root,windowsHide:true,encoding:'utf8'});assert.equal(generated.status,0,generated.stderr);
  const fixture=JSON.parse(fs.readFileSync(file,'utf8')),parent=fixture.entities.find((e)=>e.external_id==='DES-001'),reference=fixture.entities.find((e)=>e.external_id==='REF-001');
  const map=(molecule,chain)=>fixture.entities.find((e)=>e.type==='residue_map'&&e.molecule_id===molecule.id&&e.chain_id===chain);
  const h=map(parent,'H'),l=map(parent,'L'),rh=map(reference,'H'),rl=map(reference,'L');
  await start();browser=await chromium.launch({headless:true,channel:process.env.PLAYWRIGHT_CHANNEL||'chrome'});const context=await browser.newContext({viewport:{width:1500,height:1050},acceptDownloads:true}),page=await context.newPage();
  const outbound=[],errors=[];page.on('pageerror',(e)=>errors.push(e.message));await context.route('**/*',async(route)=>{if(!route.request().url().startsWith(origin+'/')){outbound.push(route.request().url());await route.abort();}else await route.continue();});
  await page.goto(origin);let saved,designed,lineage,hypothesis;
  await check('e2e_j02_humanize_variant',async()=>{
    await page.getByRole('button',{name:'Import data',exact:true}).click();await page.locator('#import-file').setInputFiles(file);await page.getByRole('button',{name:'Validate & preview',exact:true}).click();await page.getByRole('button',{name:/Save \d+ valid rows/}).click();
    await page.locator('#candidate-count').filter({hasText:'8'}).waitFor();
    await page.getByRole('checkbox',{name:'Select DES-001',exact:true}).check();await page.getByRole('checkbox',{name:'Select REF-001',exact:true}).check();
    await page.getByRole('button',{name:parent.name,exact:true}).click();
    const headers=await page.locator('.numbered-comparison thead th').allTextContents();
    const center=headers.indexOf('111');
    assert.ok(center>0);
    assert.deepEqual(headers.slice(center,center+4),['111','111.1','112.1','112']);
    assert.equal(await page.getByRole('button',{name:'DES-001 H IMGT 111.1 N, raw index 112',exact:true}).count(),1);
    await page.getByRole('button',{name:/DES-001 H sequence index 112 /}).click();
    assert.match(await page.locator('.sequence-details').first().textContent(),/IMGT 111\.1 \/ CDR3/);
    await page.getByRole('button',{name:'Design a substitution at the selected residue',exact:false}).click();
    await page.getByRole('heading',{name:'Substitution design',exact:true}).waitFor();
    assert.equal(await page.locator('#design-map').inputValue(),h.id);assert.equal(await page.locator('#design-parent').inputValue(),parent.id);
    await page.locator('#design-reference').selectOption(rh.id);await page.getByRole('combobox',{name:'Target AA at H IMGT 111.1',exact:true}).waitFor();
    const position=page.locator('[data-design-coordinate="111.1"]');assert.match(await position.textContent(),/112 \/ N/);assert.match(await position.textContent(),/112 \/ P/);
    await page.getByRole('combobox',{name:'Target AA at H IMGT 111.1',exact:true}).selectOption('P');
    await page.locator('#design-map').selectOption(l.id);await page.locator('#design-reference').selectOption(rl.id);
    await page.locator('#design-position-filter').fill('10');
    await page.getByRole('combobox',{name:'Target AA at L IMGT 10',exact:true}).selectOption('V');
    assert.equal(await page.locator('#design-staged tbody tr').count(),2);
    assert.match(await page.locator('#design-staged').textContent(),/CDR3/);assert.match(await page.locator('#design-staged').textContent(),/FR1/);
    await page.locator('#design-name').fill('Synthetic reference-guided child');await page.locator('#design-external').fill('DES-CHILD-001');
    const reason='Synthetic engineering design: explicit reference-coordinate H111.1 and L10 substitutions; no claim of human species, preserved function or successful humanization.';
    await page.locator('#design-reason').fill(reason);await page.evaluate(()=>window.scrollTo(0,0));await page.screenshot({path:path.join(out,'J02-coordinate-design.png'),fullPage:true});await page.getByRole('button',{name:'Review child and lineage before saving',exact:true}).click();
    await page.locator('#design-preview-dialog').waitFor();assert.deepEqual(await bundle(page,fixture.project.id),fixture);
    const preview=JSON.parse(await page.locator('#design-preview-content pre').textContent());assert.equal(preview.entities.length,2);
    [designed,lineage]=preview.entities;assert.equal(lineage.change_set.reason,reason);
    assert.deepEqual(lineage.change_set.mutations.map((m)=>[m.chain_id,m.scheme,m.number,m.ins_code,m.sequence_index,m.to_aa]),[['H','IMGT',111,'.1',112,'P'],['L','IMGT',10,'',10,'V']]);
    await page.getByRole('button',{name:'Save reviewed records',exact:true}).click();await page.locator('#saved-design').waitFor();
    const after=await bundle(page,fixture.project.id);assert.deepEqual(after.entities.slice(0,fixture.entities.length),fixture.entities);assert.equal(after.entities.length,fixture.entities.length+2);
    assert.equal(after.entities.find((e)=>e.id===designed.id).chains[0].sequence[111],'P');assert.equal(after.entities.find((e)=>e.id===designed.id).chains[1].sequence[9],'V');
    assert.equal(after.entities.find((e)=>e.id===parent.id).chains[0].sequence[111],'N');assert.equal(after.entities.find((e)=>e.id===parent.id).chains[1].sequence[9],'M');
    assert.match(await page.locator('#saved-design').textContent(),/Child numbering, structure, measurements and function are not validated/);
    steps.push('E/W/D: explicit VH/VL parent and reference; source IMGT 111.1/CDR3 and L10/FR1 observed; source-coordinate comparison and two reviewed substitutions saved with full lineage; original records unchanged');
    await page.getByRole('button',{name:'Inspect parent and child in W',exact:true}).click();
    assert.match(await page.locator('.panel-head h2').first().textContent(),/Synthetic reference-guided child/);
    await page.getByRole('combobox',{name:'Chain for DES-CHILD-001',exact:true}).selectOption('L');await page.getByRole('combobox',{name:'Chain for DES-001',exact:true}).selectOption('L');
    await page.getByRole('button',{name:/DES-CHILD-001 L sequence index 10 V/}).click();
    assert.equal(await page.locator('.residue.active').count(),2);assert.ok(await page.locator('.residue.diff').count()>0);
    await page.getByText('Numbering: mapping unavailable (no imported map).',{exact:true}).first().waitFor();
    await nav(page,'R');await page.getByRole('button',{name:'Record research hypothesis',exact:true}).click();
    await page.locator('#hypothesis-text').fill('Synthetic proposed hypothesis: reference-guided substitutions may alter properties; evaluate the child rather than inheriting parent observations.');
    await page.locator('#hypothesis-question').fill('Compare purified parent and child under matched assay conditions; measure binding and stability independently.');
    await page.locator('#hypothesis-limitations').fill('Engineering fixture only. Human sequence identity, numbering of the child and biological activity are unvalidated.');
    const parentMaterial=fixture.entities.find((e)=>e.type==='material'&&fixture.entities.some((c)=>c.type==='construct'&&c.id===e.construct_id&&c.molecule_id===parent.id));
    const evidence=fixture.entities.find((e)=>e.type==='evidence'&&e.subject_id===parentMaterial.id);
    await page.locator(`[data-hypothesis-evidence="${evidence.id}"]`).check();
    await page.getByRole('button',{name:'Review hypothesis before saving',exact:true}).click();
    await page.locator('#design-preview-dialog').waitFor({state:'visible'});
    hypothesis=JSON.parse(await page.locator('#design-preview-content pre').textContent());
    assert.equal(hypothesis.type,'hypothesis');assert.equal(hypothesis.status,'proposed');assert.deepEqual(hypothesis.related_evidence_ids,[evidence.id]);assert.deepEqual(hypothesis.lineage_ids,[lineage.id]);
    assert.deepEqual(hypothesis.residue_refs,[{molecule_id:designed.id,chain_id:'L',sequence_index:10}]);
    assert.equal((await bundle(page,fixture.project.id)).entities.length,fixture.entities.length+2);
    await page.getByRole('button',{name:'Save reviewed records',exact:true}).click();await page.locator('.saved-hypothesis').waitFor();
    await page.evaluate(()=>window.scrollTo(0,document.body.scrollHeight));await page.screenshot({path:path.join(out,'J02-saved-hypothesis.png'),fullPage:true});
    const output=await download(page,'saved.json');saved=output.bundle;assert.deepEqual(saved.entities.slice(0,fixture.entities.length),fixture.entities);assert.equal(saved.entities.length,fixture.entities.length+3);
    assert.deepEqual(saved.entities.find((e)=>e.id===hypothesis.id),hypothesis);assert.deepEqual(saved.entities.find((e)=>e.id===lineage.id),lineage);
    assert.equal(saved.entities.filter((e)=>['evidence','construct','material','structure','residue_map'].includes(e.type)&&e.molecule_id===designed.id).length,0);
    steps.push('D/W/R: parent/child differences observed with child numbering explicitly unavailable; proposed hypothesis, next test, limitations, actual parent Evidence ID, child raw residue and lineage retained separately from measurements');
    const selection=await page.locator('#selection-count').textContent(),port=Number(new URL(origin).port);await stop();await start(database,port);await page.reload();await page.locator('.saved-hypothesis').waitFor();
    assert.equal(await page.locator('#selection-count').textContent(),selection);assert.deepEqual((await download(page,'restart.json')).bundle,saved);
    steps.push('Actual process restart: exact parent, child, mutation identifiers, original evidence, hypothesis text/question/limitations/source contexts and selection restored');
    await stop();await start(path.join(temp,'fresh.sqlite3'));await page.goto(origin);await page.getByRole('button',{name:'Import data',exact:true}).click();await page.locator('#import-file').setInputFiles(output.path);await page.getByRole('button',{name:'Validate & preview',exact:true}).click();await page.getByRole('button',{name:/Save \d+ valid rows/}).click();await page.locator('#candidate-count').filter({hasText:'9'}).waitFor();
    assert.deepEqual(await bundle(page,fixture.project.id),saved);steps.push('Fresh database JSON reimport: all entity IDs/types, exact source data, full lineage and proposed hypothesis equal the saved bundle');
  });
  await check('e2e_j02_numbering_unavailable',async()=>{
    await nav(page,'D');const unavailable=fixture.entities.find((e)=>e.external_id==='DES-UNAVAILABLE'),badMap=map(unavailable,'H');
    await page.locator('#design-parent').selectOption(unavailable.id);
    await page.waitForFunction(({parentId,mapId})=>document.querySelector('#design-parent')?.value===parentId&&document.querySelector(`#design-map option[value="${mapId}"]`)?.disabled,{parentId:unavailable.id,mapId:badMap.id});
    const disabledOption=page.locator(`#design-map option[value="${badMap.id}"]`);
    assert.deepEqual(await disabledOption.evaluate((el)=>({disabled:el.disabled,matchesDisabled:el.matches(':disabled')})),{disabled:true,matchesDisabled:true});
    await page.locator('#design-map').focus();await page.keyboard.press('ArrowDown');
    assert.equal(await page.locator('#design-map').inputValue(),'');
    await page.getByText('Numbering unavailable for design until an eligible map is chosen.',{exact:false}).waitFor();
    const rejected=await post(page,'/api/variant-preview',{project_id:fixture.project.id,parent_id:unavailable.id,name:'Must not exist',external_id:'REJECT',reason:'Synthetic invalid map test',substitutions:[{parent_map_id:badMap.id,number:111,ins_code:'.1',to_aa:'A',reference_map_id:null}]});
    assert.equal(rejected.status,422);assert.match(rejected.data.error,/Numbering unavailable/);assert.deepEqual(await bundle(page,fixture.project.id),saved);
  });
  await check('e2e_j02_insertion_mapping',async()=>{
    await page.locator('#design-parent').selectOption(parent.id);await page.locator('#design-map').selectOption(h.id);
    await page.locator('#design-position-filter').fill('111');await page.getByRole('combobox',{name:'Target AA at H IMGT 111',exact:true}).selectOption('A');
    await page.locator('#design-position-filter').fill('111.1');await page.getByRole('combobox',{name:'Target AA at H IMGT 111.1',exact:true}).selectOption('C');
    assert.match(await page.locator('#design-staged').textContent(),/111\.1/);assert.equal(await page.locator('#design-staged tbody tr').count(),2);
    await page.locator('#design-position-filter').fill('111.2');await page.getByText('No recorded coordinate matches. No neighbour or raw-index fallback.',{exact:true}).waitFor();assert.equal(await page.locator('[data-design-coordinate]:visible').count(),0);
    const rejected=await post(page,'/api/variant-preview',{project_id:fixture.project.id,parent_id:parent.id,name:'Must not exist',external_id:'REJECT',reason:'Synthetic unmapped insertion test',substitutions:[{parent_map_id:h.id,number:111,ins_code:'.2',to_aa:'A',reference_map_id:null}]});assert.equal(rejected.status,422);assert.match(rejected.data.error,/mapping unavailable/);
    await page.locator('#design-name').fill('Insertion preview only');await page.locator('#design-external').fill('NOT-SAVED');await page.locator('#design-reason').fill('Show integer and insertion as distinct source residues.');
    await page.getByRole('button',{name:'Review child and lineage before saving',exact:true}).click();await page.locator('#design-preview-dialog').waitFor();
    const incoming=JSON.parse(await page.locator('#design-preview-content pre').textContent());assert.deepEqual(incoming.entities[1].change_set.mutations.map((m)=>[m.number,m.ins_code,m.sequence_index]),[[111,'',111],[111,'.1',112]]);
    await page.getByRole('button',{name:'Close design preview',exact:true}).click();assert.deepEqual(await bundle(page,fixture.project.id),saved);
  });
  assert.deepEqual(outbound,[]);assert.deepEqual(errors,[]);results.push({name:'No outbound browser requests or JavaScript errors',status:'PASS'});
  record('J02-browser-results.json',{status:'PASS',scope:'Full J02 and two prescribed negatives, labelled synthetic engineering fixture; human scientific/reference validation remains pending',timestamp:new Date().toISOString(),browser:await browser.version(),dataset_sha256:crypto.createHash('sha256').update(JSON.stringify(saved)).digest('hex'),steps,results});
  console.log('PASS J02 browser checks',results.length);
})().catch((error)=>{console.error(error);record('J02-browser-failure.json',{status:'FAIL',timestamp:new Date().toISOString(),error:String(error),steps,results});process.exitCode=1;}).finally(async()=>{if(browser)await browser.close();await stop();});
