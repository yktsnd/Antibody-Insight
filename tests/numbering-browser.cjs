/* F07 import/observation evidence. Not the complete J01/J02/J08 acceptance. */
const {chromium} = require('playwright');
const {spawn} = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const assert = require('node:assert/strict');

const root = path.resolve(__dirname,'..'), evidence = path.join(root,'TEST_EVIDENCE');
const temp = fs.mkdtempSync(path.join(os.tmpdir(),'antibody-numbering-'));
const database = path.join(temp,'numbering.sqlite3');
let server, origin, browser;
const results=[];
async function start(port=0) {
  server=spawn(process.env.PYTHON || 'python',['-m','workspace_app.server','--database',database,'--port',String(port)],{cwd:root,windowsHide:true,stdio:['ignore','pipe','pipe']});
  origin=await new Promise((resolve,reject)=>{let log='';const timer=setTimeout(()=>reject(new Error('Server timeout '+log)),15000);
    server.stdout.on('data',(data)=>{log+=data;const found=log.match(/http:\/\/127\.0\.0\.1:\d+/);if(found){clearTimeout(timer);resolve(found[0]);}});
    server.stderr.on('data',(data)=>{log+=data;});server.on('exit',(code)=>{clearTimeout(timer);reject(new Error('Server exited '+code+' '+log));});});
}
async function stop(){if(server&&server.exitCode===null)await new Promise((resolve)=>{server.once('exit',resolve);server.kill();});}
async function check(name,action){const then=Date.now();await action();results.push({name,status:'PASS',duration_ms:Date.now()-then});console.log('PASS',name);}
async function post(page,route,data){return page.evaluate(async({route,data})=>{const boot=await(await fetch('/api/bootstrap')).json();const response=await fetch(route,{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':boot.csrf},body:JSON.stringify(data)});return{status:response.status,data:await response.json()};},{route,data});}
async function nav(page,screen){await page.locator(`nav [data-screen="${screen}"]`).click();}
async function text(page,value){await page.getByText(value,{exact:false}).first().waitFor();}

(async()=>{
  await start();browser=await chromium.launch({headless:true,channel:process.env.PLAYWRIGHT_CHANNEL || 'chrome'});
  const context=await browser.newContext({viewport:{width:1440,height:1080},acceptDownloads:true});const page=await context.newPage();
  const outbound=[],errors=[];page.on('pageerror',(e)=>errors.push(e.message));
  await context.route('**/*',async(route)=>{if(!route.request().url().startsWith(origin+'/')){outbound.push(route.request().url());await route.abort();}else await route.continue();});
  await page.goto(origin);let fixture;
  await check('800 candidates imported with explicit synthetic numbering metadata',async()=>{
    fixture=await page.evaluate(async()=>await(await fetch('/api/example-numbering?count=800')).json());
    assert.equal(fixture.project.data_class,'synthetic_fixture');
    await page.getByRole('button',{name:'Import data',exact:true}).click();await page.locator('#import-format').selectOption('json');
    await page.locator('#import-text').fill(JSON.stringify(fixture));await page.getByRole('button',{name:'Validate & preview'}).click();
    await page.getByRole('button',{name:/Save \d+ valid rows/}).click();await page.locator('#candidate-count').filter({hasText:'800'}).waitFor({timeout:30000});
    await text(page,'3 complete groups');assert.equal(await page.locator('[data-map-choice]').count(),0);
  });
  await check('CDR-H3 grouping retains five selected IDs across raw chain and exact insertion observations',async()=>{
    for(let i=1;i<=5;i++)await page.getByRole('checkbox',{name:`Select NUM-${String(i).padStart(3,'0')}`,exact:true}).check();
    await page.locator('#group-by').selectOption('cdr3');const options=await page.locator('#cdr3-filter option').allTextContents();assert.equal(options.length,4);
    const group=await page.locator('#cdr3-filter option').nth(1).getAttribute('value');await page.locator('#cdr3-filter').selectOption(group);
    assert.match(group,/^rmp_/);
    const displayedSequence=(await page.locator('#cdr3-filter option:checked').textContent()).split(' ')[0];
    assert.equal(await page.evaluate((seq)=>Object.keys(localStorage).some((key)=>localStorage.getItem(key).includes(seq)),displayedSequence),false);
    assert.equal(await page.locator('#selection-count').textContent(),'5 selected');
    await page.locator('#cdr3-filter').selectOption('');await page.getByRole('button',{name:'Numbered fixture candidate 001',exact:true}).click();
    await text(page,'Synthetic engineering annotation; human scientific validation pending.');
    await page.getByRole('button',{name:/NUM-001 H sequence index 112 /}).click();await text(page,'IMGT 111.1 / CDR3 / fixture-V');
    await page.getByRole('button',{name:/NUM-001 H sequence index 113 /}).click();await text(page,'IMGT 112.1 / CDR3 / fixture-V');
    await page.getByRole('combobox',{name:'Chain for NUM-001',exact:true}).selectOption('L');
    assert.match(await page.locator('.sequence-details').first().textContent(),/IMGT 113 \/ CDR3/);
    assert.equal(await page.locator('#selection-count').textContent(),'5 selected');
    await page.getByRole('combobox',{name:'Chain for NUM-001',exact:true}).selectOption('H');
    await page.evaluate(()=>window.scrollTo(0,0));await page.screenshot({path:path.join(evidence,'M2-numbering-screen.png'),fullPage:true});
  });
  await check('unavailable partial unverified and ambiguous mappings remain explicit',async()=>{
    const source=fixture.entities.find((e)=>e.type==='residue_map'&&e.chain_type==='heavy');
    const extra=structuredClone(source);extra.id='rmp_39d5ca2e-1c93-4052-b7d8-f8aba82accf5';extra.source.version='second engineering annotation';
    assert.equal((await post(page,'/api/import',{schema_version:fixture.schema_version,project:fixture.project,entities:[extra]})).status,200);
    await page.reload();await nav(page,'E');const choice=page.getByRole('combobox',{name:'CDR-H3 map for NUM-001',exact:true});await choice.waitFor();
    const row=page.locator('tr').filter({has:page.getByRole('checkbox',{name:'Select NUM-001',exact:true})});assert.match(await row.textContent(),/choose map\/domain/);
    await choice.selectOption(extra.id);await page.waitForFunction((id)=>document.querySelector(`[data-map-choice="${id}"]`).value!=='',source.molecule_id);
    assert.equal(await page.getByRole('combobox',{name:'CDR-H3 map for NUM-001',exact:true}).inputValue(),extra.id);
    for(const kind of ['unavailable','unverified','partial']){
      const map=structuredClone(source);map.id='rmp_'+({unavailable:'7f91c67c-0885-4a6b-81bb-df238e7cbf91',unverified:'7a84399c-60e8-4c59-b6df-4082117bdf7b',partial:'d941070b-1ef3-45a5-9206-50bc79e907b9'}[kind]);
      map.domain_id=kind+'-test';
      if(kind==='unavailable'){map.status='unavailable';map.reason='Source failed to number';map.entries=[];map.sequence_start=null;map.sequence_end=null;}
      if(kind==='unverified')map.verification.status='unverified';
      if(kind==='partial'){map.entries=map.entries.slice(0,110);map.sequence_end=110;}
      assert.equal((await post(page,'/api/import',{schema_version:fixture.schema_version,project:fixture.project,entities:[map]})).status,200);
    }
    await page.reload();await nav(page,'W');const select=page.getByRole('combobox',{name:'Numbering map for NUM-001 H',exact:true});
    await select.selectOption('rmp_7f91c67c-0885-4a6b-81bb-df238e7cbf91');await text(page,'Source failed to number');
    assert.equal(await page.locator('.panel').first().locator('.residue[title*="IMGT"]').count(),0);
    await select.selectOption('rmp_7a84399c-60e8-4c59-b6df-4082117bdf7b');await text(page,'Not eligible for source-verified numbering actions.');
    await page.getByRole('combobox',{name:'Numbering map for NUM-001 H',exact:true}).selectOption('rmp_d941070b-1ef3-45a5-9206-50bc79e907b9');await text(page,'CDR3: partial / unavailable');
  });
  await check('bad sequence annotation and malformed map choices reject without overwrite',async()=>{
    const bad=structuredClone(fixture);const map=bad.entities.find((e)=>e.type==='residue_map');map.entries[0].aa='X';
    assert.equal((await post(page,'/api/import',bad)).status,422);
    for(const map_choices of [[],false,null,0,'',{'unknown-molecule':'unknown-map'}])assert.equal((await post(page,'/api/cdr3-groups',{project_id:fixture.project.id,map_choices})).status,422);
  });
  await check('server restart preserves map choice chain context and exact map provenance',async()=>{
    const before=await page.evaluate(async(id)=>await(await fetch('/api/bundle?project_id='+id)).json(),fixture.project.id);
    const port=Number(new URL(origin).port);await stop();await start(port);await page.reload();await text(page,'CDR3: partial / unavailable');
    assert.equal(await page.locator('#selection-count').textContent(),'5 selected');
    await nav(page,'E');assert.equal(await page.getByRole('combobox',{name:'CDR-H3 map for NUM-001',exact:true}).inputValue(),'rmp_39d5ca2e-1c93-4052-b7d8-f8aba82accf5');
    const after=await page.evaluate(async(id)=>await(await fetch('/api/bundle?project_id='+id)).json(),fixture.project.id);assert.deepEqual(after,before);
    await page.evaluate(()=>window.scrollTo(0,0));await page.screenshot({path:path.join(evidence,'M2-numbering-explorer.png')});
  });
  assert.deepEqual(outbound,[]);assert.deepEqual(errors,[]);
  const report={scope:'F07 source-bearing imported numbering and partial J01/J02/J08; full journeys remain pending',status:'PASS',timestamp:new Date().toISOString(),browser:await browser.version(),results,no_outbound_requests:true,no_javascript_errors:true};
  fs.writeFileSync(path.join(evidence,'M2-numbering-browser-results.json'),JSON.stringify(report,null,2));console.log('PASS F07 browser checks',results.length);
})().catch((error)=>{console.error(error);fs.writeFileSync(path.join(evidence,'M2-numbering-browser-failure.json'),JSON.stringify({error:String(error),results},null,2));process.exitCode=1;}).finally(async()=>{if(browser)await browser.close();await stop();});
