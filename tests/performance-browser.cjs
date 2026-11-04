/* P01/P08 J01/J08 AC-J01/AC-J08 and Release1.0 latency gate.
 * Ten actual local browser runs with1000 labelled synthetic candidates.
 * This host has less than16GB RAM; record observations without standard-host PASS.
 */
const {chromium}=require('playwright'),{spawn,spawnSync}=require('node:child_process');
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),temp=fs.mkdtempSync(path.join(os.tmpdir(),'antibody-performance-'));
const python=process.env.PYTHON||path.join(root,'.venv','Scripts','python.exe'),db=path.join(temp,'performance.sqlite3');
let browser,server,origin;const trials=[],errors=[],outbound=[];
const diagnostic=process.argv.includes('--diagnostic'),runCount=diagnostic?3:10;
const hardware={logical_cpus:os.cpus().length,ram_bytes:os.totalmem(),os:os.release(),cpu_model:os.cpus()[0]?.model,
  disk_media:'not independently verified',standard_hardware_gate:'NOT_QUALIFIED:16GB RAM and SSD verification required'};
const seed=spawnSync(python,['-c',"import json,sys;from workspace_app.fixtures import example_bundle;from workspace_app.storage import Store;b=example_bundle(1000);Store(sys.argv[1]).import_bundle(b);print(json.dumps({'project_id':b['project']['id'],'first':b['entities'][0]['id']}))",db],{cwd:root,windowsHide:true,encoding:'utf8'});
assert.equal(seed.status,0,seed.stderr);const fixture=JSON.parse(seed.stdout);
const clock=()=>Number(process.hrtime.bigint())/1e6;
const painted=(p)=>p.evaluate(()=>new Promise((r)=>requestAnimationFrame(()=>requestAnimationFrame(r))));
(async()=>{
 server=spawn(python,['-m','workspace_app.server','--database',db,'--port','0'],{cwd:root,windowsHide:true,stdio:['ignore','pipe','pipe']});
 origin=await new Promise((resolve,reject)=>{let log='';const timer=setTimeout(()=>reject(Error('Server timeout '+log)),15000);server.stdout.on('data',(d)=>{log+=d;const match=log.match(/http:\/\/127\.0\.0\.1:\d+/);if(match){clearTimeout(timer);resolve(match[0]);}});server.stderr.on('data',(d)=>log+=d);});
 browser=await chromium.launch({headless:true,channel:process.env.PLAYWRIGHT_CHANNEL||'chrome'});hardware.browser_version=browser.version();
 for(let run=1;run<=runCount;run++){
  const context=await browser.newContext({viewport:{width:1600,height:1050}}),page=await context.newPage();page.on('pageerror',(e)=>errors.push(e.message));
  await context.route('**/*',async(route)=>{if(!route.request().url().startsWith(origin+'/')){outbound.push(route.request().url());await route.abort();}else await route.continue();});
  const start=clock();await page.goto(origin);await page.waitForFunction(()=>!document.querySelector('#project-select').disabled&&document.querySelectorAll('tr[data-candidate-id]').length===1000);await painted(page);
  const trial={run,initial_1000_ms:clock()-start,operations:[]};
  async function measure(name,selector,eventName,action,assertion){
   // Diagnostic only: measure the actual native input event through the next
   // painted frames, alongside (never replacing) original automation timings.
   await page.locator(selector).evaluate((el,eventName)=>{window.__awxPerfMark=null;el.addEventListener(eventName,()=>{const start=performance.now();requestAnimationFrame(()=>requestAnimationFrame(()=>{window.__awxPerfMark=performance.now()-start;}));},{capture:true,once:true});},eventName);
   const begin=clock();await action();await assertion();await painted(page);const duration_ms=clock()-begin;
   trial.operations.push({name,duration_ms,event_to_two_frames_ms:await page.evaluate(()=>window.__awxPerfMark)});
  }
  await measure('search_one',`#candidate-search`,'input',()=>page.locator('#candidate-search').fill('FIX-001'),()=>assert.doesNotReject(async()=>assert.equal(await page.locator('tr[data-candidate-id]').count(),1)));
  await measure('clear_search',`#candidate-search`,'input',()=>page.locator('#candidate-search').fill(''),()=>assert.doesNotReject(async()=>assert.equal(await page.locator('tr[data-candidate-id]').count(),1000)));
  await measure('select_candidate',`[data-select="${fixture.first}"]`,'change',()=>page.locator(`[data-select="${fixture.first}"]`).check(),()=>assert.doesNotReject(async()=>assert.equal(await page.locator('#selection-count').textContent(),'1 selected')));
  await measure('open_workspace',`nav [data-screen="W"]`,'click',()=>page.locator('nav [data-screen="W"]').click(),()=>assert.doesNotReject(async()=>assert.equal(await page.locator(`[data-chain="${fixture.first}"]`).count(),1)));
  await measure('return_explorer',`nav [data-screen="E"]`,'click',()=>page.locator('nav [data-screen="E"]').click(),()=>assert.doesNotReject(async()=>assert.equal(await page.locator('tr[data-candidate-id]').count(),1000)));
  await measure('clear_selection',`[data-select="${fixture.first}"]`,'change',()=>page.locator(`[data-select="${fixture.first}"]`).uncheck(),()=>assert.doesNotReject(async()=>assert.equal(await page.locator('#selection-count').textContent(),'0 selected')));
  const times=trial.operations.map((o)=>o.duration_ms).sort((a,b)=>a-b);trial.simple_operation_p95_ms=times[Math.ceil(times.length*.95)-1];trials.push(trial);console.log('RUN',run,'initial_ms',Math.round(trial.initial_1000_ms),'p95_ms',Math.round(trial.simple_operation_p95_ms));await context.close();
 }
 const ops=trials.flatMap((t)=>t.operations.map((o)=>o.duration_ms)).sort((a,b)=>a-b),p95=ops[Math.ceil(ops.length*.95)-1];assert.deepEqual(errors,[]);assert.deepEqual(outbound,[]);
 fs.writeFileSync(path.join(root,'TEST_EVIDENCE',diagnostic?'M5-host-performance-diagnostic.json':'M5-host-performance.json'),JSON.stringify({status:'MEASURED_NONSTANDARD_HOST',diagnostic,hardware,trials,overall_simple_operation_p95_ms:p95,
  observed_initial_le_5000ms:trials.every((t)=>t.initial_1000_ms<=5000),observed_operation_p95_le_300ms:p95<=300,
  standard_release_gate:'PENDING:repeat ten runs on verified8logicalCPU/16GB/SSD',event_diagnostic:'Native input/click capture to two animation frames; recorded separately, does not replace full operation latency or qualify standard hardware.',method:'Fresh browser context per run, warm local server/browser; end-to-end Playwright action/assertion plus two animation frames. Includes automation/actionability overhead; six explicit simple operations per run. All1000 rows must exist before initial timer stops. Synthetic data only; no biological performance claim.',errors,outbound,timestamp:new Date().toISOString()},null,2));
})().catch((e)=>{console.error(e);process.exitCode=1;}).finally(async()=>{await browser?.close();if(server&&server.exitCode===null)await new Promise((r)=>{server.once('exit',r);server.kill();});});
