/* Independent F09 stale-fallback/project race: P01/J01/AC-J01. */
const {chromium}=require('playwright');
const {spawn,spawnSync}=require('node:child_process');
const fs=require('node:fs'),path=require('node:path'),os=require('node:os');
const assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),temp=fs.mkdtempSync(path.join(os.tmpdir(),'antibody-observation-review-'));
const database=path.join(temp,'review.sqlite3'),python=process.env.PYTHON||'python';
const seeded=spawnSync(python,['-c',"import sys,json; from workspace_app.fixtures import example_bundle; from workspace_app.storage import Store; s=Store(sys.argv[1]); bundles=[example_bundle(n) for n in (8,9)]; [s.import_bundle(b) for b in bundles]; print(json.dumps([b['project']['id'] for b in bundles]))",database],{cwd:root,windowsHide:true,encoding:'utf8'});
assert.equal(seeded.status,0,seeded.stderr);const [first,second]=JSON.parse(seeded.stdout);
let browser,server,releaseOld;const results=[];
(async()=>{
  server=spawn(python,['-m','workspace_app.server','--database',database,'--port','0'],{cwd:root,windowsHide:true,stdio:['ignore','pipe','pipe']});
  const origin=await new Promise((resolve,reject)=>{let log='';const timer=setTimeout(()=>reject(Error('Server timeout '+log)),15000);server.stdout.on('data',(d)=>{log+=d;const m=log.match(/http:\/\/127\.0\.0\.1:\d+/);if(m){clearTimeout(timer);resolve(m[0]);}});server.stderr.on('data',(d)=>log+=d);});
  browser=await chromium.launch({headless:true,channel:process.env.PLAYWRIGHT_CHANNEL||'chrome'});
  const context=await browser.newContext(),page=await context.newPage(),outbound=[],errors=[];
  page.on('pageerror',(e)=>errors.push(e.message));
  await context.route('**/*',async(route)=>{if(!route.request().url().startsWith(origin+'/')){outbound.push(route.request().url());await route.abort();}else await route.continue();});
  await page.goto(origin);
  await page.waitForFunction(()=>!document.querySelector('#project-select').disabled);
  if(await page.locator('#project-select').inputValue()!==first)await page.locator('#project-select').selectOption(first);
  await page.waitForFunction(()=>!document.querySelector('#project-select').disabled&&document.querySelector('#candidate-count')?.textContent==='8'&&!document.querySelector('#observation-context')?.disabled);
  const firstContext=await page.locator('#observation-context option').nth(1).getAttribute('value');
  let rejectOnce=true,held=false,markHeld;const oldHeld=new Promise((r)=>markHeld=r),oldGate=new Promise((r)=>releaseOld=r);
  await context.route('**/api/observation-order',async(route)=>{
    const data=route.request().postDataJSON();
    if(data.project_id===first&&data.cohort_id!==null&&rejectOnce){rejectOnce=false;await route.fulfill({status:400,contentType:'application/json',body:JSON.stringify({error:'Independent simulated stale context'})});return;}
    if(data.project_id===first&&data.cohort_id===null&&!rejectOnce&&!held){held=true;markHeld();await oldGate;}
    await route.continue();
  });
  await page.locator('#observation-context').selectOption(firstContext);await oldHeld;
  assert.equal(await page.locator('#observation-context').isDisabled(),true);
  assert.equal(await page.locator('#observation-direction').isDisabled(),true);
  assert.equal(await page.locator('[data-observation-status="updating"]').count(),8);
  assert.equal(await page.locator('[data-observation-status="observed"]').count(),0);
  results.push({name:'pending failed request exposes no stale scalar and disables ordering controls',status:'PASS'});
  await page.locator('#project-select').selectOption(second);
  await page.waitForFunction(()=>document.querySelector('#candidate-count')?.textContent==='9'&&!document.querySelector('#observation-context')?.disabled);
  const secondOptions=await page.locator('#observation-context option').evaluateAll((els)=>els.map((e)=>e.value));
  assert.ok(!secondOptions.includes(firstContext));const secondContext=secondOptions[1];
  await page.locator('#observation-context').selectOption(secondContext);
  await page.waitForFunction(()=>document.querySelector('[data-observation-status="observed"]'));
  const expected=await page.locator('tbody').textContent();
  const oldResponse=page.waitForResponse((response)=>response.url().endsWith('/api/observation-order')&&response.request().postDataJSON().project_id===first);
  releaseOld();await oldResponse;await page.evaluate(()=>new Promise((resolve)=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
  assert.equal(await page.locator('#project-select').inputValue(),second);
  assert.equal(await page.locator('#observation-context').inputValue(),secondContext);
  assert.deepEqual(await page.locator('#observation-context option').evaluateAll((els)=>els.map((e)=>e.value)),secondOptions);
  assert.equal(await page.locator('tbody').textContent(),expected);
  const stored=await page.evaluate((id)=>JSON.parse(localStorage.getItem('awx-state-'+id)),second);
  assert.equal(stored.observationCohort,secondContext);
  results.push({name:'late previous-project fallback cannot overwrite new project context or values',status:'PASS'});
  assert.deepEqual(outbound,[]);assert.deepEqual(errors,[]);
  results.push({name:'independent race replay has no outbound requests or JavaScript errors',status:'PASS'});
  fs.writeFileSync(path.join(root,'TEST_EVIDENCE/M2-observation-independent-browser-results.json'),JSON.stringify({status:'PASS',reviewer:'/root/j01_replay_review',timestamp:new Date().toISOString(),browser:await browser.version(),results},null,2));
  console.log(JSON.stringify({status:'PASS',results},null,2));
})().catch((error)=>{console.error(error);process.exitCode=1;}).finally(async()=>{releaseOld?.();if(browser)await browser.close();if(server&&server.exitCode===null)await new Promise((resolve)=>{server.once('exit',resolve);server.kill();});});
