/* Full prescribed J01 journey and its two negatives, using labelled synthetic data. */
const {chromium}=require('playwright');
const {spawn,spawnSync}=require('node:child_process');
const fs=require('node:fs'),path=require('node:path'),os=require('node:os');
const assert=require('node:assert/strict'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),evidence=path.join(root,'TEST_EVIDENCE');
const temp=fs.mkdtempSync(path.join(os.tmpdir(),'antibody-j01-')),database=path.join(temp,'j01.sqlite3');
const results=[],steps=[];let server,origin,browser;
const python=process.env.PYTHON||'python';
function py(code,...args){const r=spawnSync(python,['-c',code,...args],{cwd:root,windowsHide:true,encoding:'utf8',env:{...process.env,PYTHONUTF8:'1'}});assert.equal(r.status,0,r.stderr);}
function report(name,data){const target=path.join(evidence,name),pending=target+'.pending-'+crypto.randomUUID();fs.writeFileSync(pending,JSON.stringify(data,null,2));fs.renameSync(pending,target);}
async function start(port=0){server=spawn(python,['-m','workspace_app.server','--database',database,'--port',String(port)],{cwd:root,windowsHide:true,stdio:['ignore','pipe','pipe']});
  origin=await new Promise((resolve,reject)=>{let log='';const timer=setTimeout(()=>reject(Error('Server timeout '+log)),15000);server.stdout.on('data',(data)=>{log+=data;const m=log.match(/http:\/\/127\.0\.0\.1:\d+/);if(m){clearTimeout(timer);resolve(m[0]);}});server.stderr.on('data',(data)=>log+=data);server.on('exit',(code)=>{clearTimeout(timer);reject(Error('Server exited '+code+' '+log));});});}
async function stop(){if(server&&server.exitCode===null)await new Promise((resolve)=>{server.once('exit',resolve);server.kill();});}
async function check(name,action){const then=Date.now();await action();results.push({name,status:'PASS',duration_ms:Date.now()-then});console.log('PASS',name);}
async function nav(page,screen){await page.locator(`nav [data-screen="${screen}"]`).click();}
async function exported(page,name){const wait=page.waitForEvent('download');await page.getByRole('button',{name:'Export JSON',exact:true}).click();const download=await wait;const target=path.join(temp,name);await download.saveAs(target);return {target,bundle:JSON.parse(fs.readFileSync(target,'utf8'))};}
async function select(page,n){await page.getByRole('checkbox',{name:`Select DISC-${String(n).padStart(3,'0')}`,exact:true}).check();}
const row=(page,n)=>page.locator('tr').filter({has:page.getByRole('checkbox',{name:`Select DISC-${String(n).padStart(3,'0')}`,exact:true})});

(async()=>{
  const input=path.join(temp,'synthetic-discovery.csv');
  py("from pathlib import Path; import sys; from workspace_app.discovery_fixtures import sequence_input; Path(sys.argv[1]).write_text(sequence_input(),encoding='utf-8')",input);
  await start();browser=await chromium.launch({headless:true,channel:process.env.PLAYWRIGHT_CHANNEL||'chrome'});
  const context=await browser.newContext({viewport:{width:1500,height:1050},acceptDownloads:true});const page=await context.newPage();
  const outbound=[],errors=[];page.on('pageerror',(e)=>errors.push(e.message));
  await context.route('**/*',async(route)=>{if(!route.request().url().startsWith(origin+'/')){outbound.push(route.request().url());await route.abort();}else await route.continue();});
  await page.goto(origin);
  let saved,selectedIds,cohort,choice,projectId;
  await check('e2e_j01_candidate_shortlist',async()=>{
    await page.getByRole('button',{name:'Import data',exact:true}).click();
    assert.equal(await page.locator('#project-data-class').inputValue(),'research');
    await page.locator('#project-data-class').selectOption('synthetic_fixture');
    await page.locator('#project-title').fill('[SYNTHETIC FIXTURE] J01 discovery');
    await page.locator('#project-goal').fill('Engineering acceptance only; no real antibody or experiment claims.');
    await page.locator('#import-file').setInputFiles(input);await page.getByRole('button',{name:'Validate & preview',exact:true}).click();
    await check('e2e_j01_invalid_sequence',async()=>{
      await page.getByText(/802 input rows · 800 valid · 2 excluded/).waitFor();
      const excluded=await page.locator('.preview-list').first().textContent();
      assert.match(excluded,/DISC-MISSING/);assert.match(excluded,/Missing sequence/);assert.match(excluded,/DISC-INVALID/);
      assert.match(await page.locator('.preview-summary').textContent(),/sequence-repeat warnings/);
      assert.equal(await page.evaluate(async()=>(await(await fetch('/api/bootstrap')).json()).projects.length),0);
      await page.getByRole('button',{name:'Save 800 valid rows (excluded rows omitted)',exact:true}).click();
      await page.locator('#candidate-count').filter({hasText:'800'}).waitFor({timeout:30000});
      assert.equal(await page.locator('tbody tr').count(),800);
      assert.equal(await page.getByRole('checkbox',{name:/Select DISC-(MISSING|INVALID)/}).count(),0);
      assert.equal(await page.locator('td .tag.warning').count(),800);
    });
    steps.push('E: 802 CSV rows previewed; 800 accepted, missing/invalid rows excluded explicitly, sequence repeats retained as distinct IDs');
    const base=await exported(page,'imported.json');projectId=base.bundle.project.id;
    assert.equal(base.bundle.project.data_class,'synthetic_fixture');assert.equal(new Set(base.bundle.entities.map((e)=>e.id)).size,800);
    const support=path.join(temp,'synthetic-numbering-and-measurements.json');
    py("from pathlib import Path; import sys,json; from workspace_app.discovery_fixtures import support_bundle; source=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8')); Path(sys.argv[2]).write_text(json.dumps(support_bundle(source)),encoding='utf-8')",base.target,support);
    await page.getByRole('button',{name:'Import data',exact:true}).click();await page.locator('#import-file').setInputFiles(support);
    await page.getByRole('button',{name:'Validate & preview',exact:true}).click();await page.getByRole('button',{name:/Save \d+ valid rows/}).click();
    await page.getByText('3 complete groups.',{exact:false}).waitFor({timeout:30000});
    assert.equal(await page.locator('#candidate-count').textContent(),'800');
    const options=await page.locator('#observation-context option').evaluateAll((els)=>els.map((el)=>({value:el.value,text:el.textContent})));
    cohort=options.find((o)=>o.text.includes('/ nM /')).value;assert.ok(cohort.startsWith('evd_'));
    await page.locator('#observation-context').selectOption(cohort);
    await page.locator('#observation-context-details summary').click();
    assert.match(await page.locator('#observation-context-details').textContent(),/temperature_C/);
    await check('e2e_j01_missing_measurement',async()=>{
      await row(page,2).locator('[data-observation-status="value missing"]').waitFor();
      assert.doesNotMatch(await row(page,2).locator('.ordering-observation').textContent(),/^0\s/);
      assert.match(await row(page,1).locator('.ordering-observation').textContent(),/^0 nM/);
      assert.equal(await row(page,3).locator('.ordering-observation').getAttribute('data-observation-status'),'context incomplete');
      assert.equal(await row(page,4).locator('.ordering-observation').getAttribute('data-observation-status'),'different context');
      assert.equal(await row(page,800).locator('.ordering-observation').getAttribute('data-observation-status'),'not measured / not predicted');
      await select(page,1);await select(page,2);await nav(page,'R');
      assert.equal(await page.locator('.evidence-row .value').filter({hasText:'Value missing'}).count(),1);
      assert.equal(await page.locator('.evidence-row .value').filter({hasText:'0 nM'}).count(),1);
      await nav(page,'E');
    });
    assert.equal(await row(page,5).locator('.ordering-observation').getAttribute('data-observation-status'),'choose observation');
    const choices=await page.getByRole('combobox',{name:'Observation for DISC-005',exact:true}).locator('option').evaluateAll((els)=>els.map((el)=>({value:el.value,text:el.textContent})));
    choice=choices.find((o)=>o.text.startsWith('4.5 nM')).value;
    await page.getByRole('combobox',{name:'Observation for DISC-005',exact:true}).selectOption(choice);
    await row(page,5).locator('[data-observation-status="observed"]').waitFor();
    await page.locator('#observation-direction').selectOption('descending');
    await page.waitForFunction(()=>document.querySelector('tbody tr').textContent.includes('DISC-799'));
    assert.match(await page.locator('tbody tr').last().textContent(),/DISC-800/);
    await page.locator('#observation-direction').selectOption('ascending');
    await page.waitForFunction(()=>document.querySelector('tbody tr').textContent.includes('DISC-001'));
    await page.locator('#group-by').selectOption('cdr3');
    const group=await page.locator('#cdr3-filter option').nth(1).getAttribute('value');await page.locator('#cdr3-filter').selectOption(group);
    const groupText=await page.locator('#cdr3-filter option:checked').textContent();assert.match(groupText,/\(26[67]\)/);
    const groupRows=await page.locator('tbody tr').count();assert.ok(groupRows>=266&&groupRows<=267);
    assert.equal(await page.locator('#selection-count').textContent(),'2 selected');
    await page.locator('#cdr3-filter').selectOption('');await page.locator('#group-by').selectOption('none');
    steps.push('E: exact CDR-H3 groups and binding-context numeric ordering, two directions; explicit multiple-material Evidence choice; no unit/condition pooling');
    await page.getByRole('button',{name:'Discovery fixture candidate 001',exact:true}).click();
    assert.equal(await page.locator('.sequence').count(),2);assert.ok(await page.locator('.residue.diff').count()>0);
    await page.getByRole('button',{name:/DISC-001 chain-1 sequence index 105 /}).click();
    assert.equal(await page.locator('.residue.active').count(),2);
    assert.match(await page.locator('.sequence-details').first().textContent(),/IMGT 105 \/ CDR3/);
    assert.notEqual((await page.locator('.residue.active').allTextContents())[0],(await page.locator('.residue.active').allTextContents())[1]);
    await page.evaluate(()=>window.scrollTo(0,0));await page.screenshot({path:path.join(evidence,'J01-two-candidate-observation.png'),fullPage:true});
    steps.push('W: two distinct candidates physically opened and differing CDR3 residues clicked; raw indexes and imported IMGT coordinates inspected');
    await nav(page,'E');for(const n of [5,6,7])await select(page,n);
    assert.equal(await page.locator('#selection-count').textContent(),'5 selected');
    selectedIds=await page.locator('[data-select]:checked').evaluateAll((els)=>els.map((el)=>el.dataset.select));
    await nav(page,'R');assert.equal(await page.locator('#selection-count').textContent(),'5 selected');
    const reason='Synthetic J01 acceptance: retain five distinct candidates after CDR-H3 and source-specific binding observation; DISC-002 is missing, not zero. Compare the alternate lot explicitly; validate experimentally before a scientific decision.';
    await page.locator('#shortlist-reason').fill(reason);await page.getByRole('button',{name:'Review before saving',exact:true}).click();
    const preview=JSON.parse(await page.locator('#shortlist-preview pre').textContent());
    assert.deepEqual(new Set(preview.candidate_ids),new Set(selectedIds));assert.ok(preview.evidence_ids.includes(choice));
    await page.getByRole('button',{name:'Save draft',exact:true}).click();await page.locator('.saved-draft').waitFor();
    saved=(await exported(page,'saved-shortlist.json')).bundle;
    const draft=saved.entities.find((e)=>e.type==='decision');assert.equal(draft.reason,reason);assert.deepEqual(new Set(draft.candidate_ids),new Set(selectedIds));
    assert.equal(draft.status,'draft');assert.ok(draft.evidence_snapshot.length>=5);
    for(const snapshot of draft.evidence_snapshot)assert.deepEqual(snapshot,saved.entities.find((e)=>e.id===snapshot.id));
    steps.push('E → R: five IDs retained; exact reason, actual Material Evidence IDs, type/source/timestamp/conditions frozen in an immutable shortlist draft');
    await page.evaluate(()=>window.scrollTo(0,0));await page.screenshot({path:path.join(evidence,'J01-saved-shortlist.png'),fullPage:true});
    const port=Number(new URL(origin).port);await stop();await start(port);await page.reload();await page.locator('.saved-draft').waitFor();
    assert.equal(await page.locator('#selection-count').textContent(),'5 selected');assert.equal(await page.locator('.saved-draft > p').first().textContent(),reason);
    const restarted=(await exported(page,'restarted.json')).bundle;assert.deepEqual(restarted,saved);
    await nav(page,'E');assert.equal(await page.locator('#observation-context').inputValue(),cohort);
    assert.equal(await page.getByRole('combobox',{name:'Observation for DISC-005',exact:true}).inputValue(),choice);
    assert.deepEqual(new Set(await page.locator('[data-select]:checked').evaluateAll((els)=>els.map((el)=>el.dataset.select))),new Set(selectedIds));
    const stored=await page.evaluate((id)=>JSON.parse(localStorage.getItem('awx-state-'+id)),projectId);
    assert.equal(stored.observationCohort,cohort);assert.equal(Object.values(stored.observationChoices)[0],choice);
    assert.doesNotMatch(JSON.stringify(stored),/synthetic binding observation|temperature_C|4\.5|"unit"\s*:|"value"\s*:/);
    assert.match(stored.observationCohort,/^evd_[0-9a-f-]+$/);
    for(const value of Object.values(stored.observationChoices))assert.match(value,/^evd_[0-9a-f-]+$/);
    steps.push('Actual server process stopped/restarted at the same origin: exact bundle, five candidate IDs, reason, evidence snapshots and ID-only context choices restored');
  });
  await check('English and Japanese explanations preserve research data and context',async()=>{
    const before=await page.evaluate((id)=>localStorage.getItem('awx-state-'+id),projectId);
    await page.getByRole('button',{name:'Researcher guide / 利用ガイド',exact:true}).click();
    assert.equal(await page.locator('#help-language').inputValue(),'en');
    await page.locator('#help-language').selectOption('ja');
    assert.equal(await page.locator('#help-content').getAttribute('lang'),'ja');
    const japanese=await page.locator('#help-content').textContent();
    assert.match(japanese,/humanizationは「ヒト化」です/);assert.match(japanese,/humanness（ヒト抗体らしさ）/);assert.doesNotMatch(japanese,/人源化/);
    assert.match(japanese,/平均、単位換算、欠測値の補完は行いません/);
    await page.locator('#help-language').selectOption('en');assert.equal(await page.locator('#help-content').getAttribute('lang'),'en');
    assert.match(await page.locator('#help-content').textContent(),/No averaging, unit conversion or missing-value replacement/);
    await page.getByRole('button',{name:'Close guide',exact:true}).click();
    assert.equal(await page.evaluate((id)=>localStorage.getItem('awx-state-'+id),projectId),before);
    assert.deepEqual((await exported(page,'after-language-switch.json')).bundle,saved);
  });
  assert.deepEqual(outbound,[]);assert.deepEqual(errors,[]);
  results.push({name:'no outbound browser requests or JavaScript errors',status:'PASS'});
  report('J01-browser-results.json',{scope:'Full J01 and two prescribed negatives; synthetic engineering fixtures, not scientific golden validation or full product acceptance',status:'PASS',timestamp:new Date().toISOString(),browser:await browser.version(),dataset_sha256:crypto.createHash('sha256').update(JSON.stringify(saved)).digest('hex'),selected_ids:selectedIds,steps,results});
  console.log(JSON.stringify({status:'PASS',checks:results.length,steps:steps.length}));
})().catch((error)=>{console.error(error);report('J01-browser-failure.json',{status:'FAIL',timestamp:new Date().toISOString(),error:String(error),steps,results});process.exitCode=1;}).finally(async()=>{if(browser)await browser.close();await stop();});
