/* Initial F01-F05 real-browser evidence. This is not the final eight-journey suite. */
const {chromium} = require('playwright');
const {spawn} = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');

const root = path.resolve(__dirname, '..');
const evidenceDir = path.join(root, 'TEST_EVIDENCE');
const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'antibody-insight-e2e-'));
const database = path.join(temp, 'test.sqlite3');
const results = [];
let browser, server;

async function start(databasePath, port = 0) {
  const child = spawn(process.env.PYTHON || 'python', ['-m', 'workspace_app.server', '--database', databasePath, '--port', String(port)], {cwd:root, windowsHide:true, stdio:['ignore','pipe','pipe']});
  let log = '';
  const origin = await new Promise((resolve, reject) => {
    const timeout = setTimeout(() => reject(new Error('Server did not start')), 15000);
    child.stdout.on('data', (data) => {log += data; const match = log.match(/http:\/\/127\.0\.0\.1:\d+/); if (match) {clearTimeout(timeout);resolve(match[0]);}});
    child.stderr.on('data', (data) => {log += data;});
    child.on('exit', (code) => {clearTimeout(timeout);reject(new Error(`Server exited ${code}: ${log}`));});
  });
  return {child, origin};
}
async function stop(s) {
  if (!s || s.child.exitCode !== null) return;
  await new Promise((resolve) => {s.child.once('exit', resolve);s.child.kill();});
}
async function check(name, action) {const start = Date.now(); await action();results.push({name,status:'PASS',duration_ms:Date.now()-start});console.log('PASS',name);}
async function navigate(page, screen) {await page.locator(`nav [data-screen="${screen}"]`).click();await page.waitForFunction((s) => document.querySelector(`nav [data-screen="${s}"]`).classList.contains('active'),screen);}
async function bodyContains(page, text) {await page.getByText(text,{exact:false}).first().waitFor();}
async function fromPage(page, route, data) {
  return page.evaluate(async ({route,data}) => {
    const boot = await (await fetch('/api/bootstrap')).json();
    const r = await fetch(route, {method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':boot.csrf},body:JSON.stringify(data)});
    return {status:r.status,data:await r.json()};
  },{route,data});
}

(async () => {
  server = await start(database);
  browser = await chromium.launch({headless:true,channel:process.env.PLAYWRIGHT_CHANNEL || 'chrome'});
  const context = await browser.newContext({viewport:{width:1440,height:1000},acceptDownloads:true});
  const page = await context.newPage();
  const outbound = [], consoleErrors = [];
  page.on('pageerror',(e) => consoleErrors.push(e.message));
  await context.route('**/*', async (route) => {
    if (!route.request().url().startsWith(server.origin + '/')) {outbound.push(route.request().url());await route.abort();} else await route.continue();
  });
  await check('empty workspace and explicit fixture preview', async () => {
    await page.goto(server.origin);await page.getByRole('heading',{name:'Candidate Explorer',exact:true}).waitFor();
    await page.getByRole('button',{name:'Import data',exact:true}).click();
    await page.getByRole('button',{name:'Preview synthetic example'}).click();
    await bodyContains(page,'Synthetic fixture. These are invented engineering values');
    assert.equal(await page.evaluate(async () => (await (await fetch('/api/bootstrap')).json()).projects.length),0);
    await page.getByRole('button',{name:/Save \d+ valid rows/}).click();
    await page.locator('#candidate-count').filter({hasText:'8'}).waitFor();
  });
  await check('five IDs persist across E W D R and residue selection',async () => {
    for(let i=1;i<=5;i++) await page.getByRole('checkbox',{name:`Select FIX-${String(i).padStart(3,'0')}`,exact:true}).check();
    assert.equal(await page.locator('#selection-count').textContent(),'5 selected');
    await navigate(page,'W');
    await page.getByRole('button',{name:'FIX-001 chain-1 sequence index 3 Q',exact:true}).click();
    assert.equal(await page.locator('.residue.active').count(),2);
    await navigate(page,'E');await page.getByRole('button',{name:'Fixture candidate 005',exact:true}).click();
    assert.equal(await page.locator('.panel-head h2').first().textContent(),'Fixture candidate 005');
    assert.match(await page.locator('#breadcrumb').textContent(),/FIX-005/);
    await navigate(page,'D');await page.getByRole('heading',{name:'Substitution design',exact:true}).waitFor();assert.equal(await page.locator('#selection-count').textContent(),'5 selected');
    await navigate(page,'R');assert.equal(await page.locator('#selection-count').textContent(),'5 selected');
  });
  let draft;
  await check('measured computed null zero conditions and immutable five-candidate draft',async () => {
    assert.equal(await page.locator('.evidence-row .tag.measured').count(),5);assert.equal(await page.locator('.evidence-row .tag.computed').count(),1);
    await bodyContains(page,'Value missing');await bodyContains(page,'Conditions unknown');
    assert.match(await page.locator('.value').first().textContent(),/^0 /);
    await page.locator('#shortlist-reason').fill('Retain five candidates; compare specificity in the next experiment. Synthetic engineering check.');
    await page.getByRole('button',{name:'Review before saving'}).click();
    await bodyContains(page,'5 candidate IDs · 6 evidence records');
    const response = page.waitForResponse((r) => r.url().endsWith('/api/shortlist') && r.request().method()==='POST');
    await page.getByRole('button',{name:'Save draft',exact:true}).click();draft = await (await response).json();
    assert.equal(draft.candidate_ids.length,5);assert.equal(draft.evidence_snapshot.length,6);assert.equal(draft.status,'draft');
    await page.locator('.saved-draft').waitFor();
    await page.evaluate(()=>window.scrollTo(0,0));
    await page.screenshot({path:path.join(evidenceDir,'M1-evidence-screen.png'),fullPage:true});
  });
  let exported;
  await check('fresh JSON export and restart preserve IDs snapshots selection and source versions',async () => {
    const downloadPromise = page.waitForEvent('download');await page.getByRole('button',{name:'Export JSON'}).click();
    const download = await downloadPromise;const target = path.join(temp,'roundtrip.json');await download.saveAs(target);exported = JSON.parse(fs.readFileSync(target,'utf8'));
    assert.deepEqual(exported.entities.find((e)=>e.id===draft.id),draft);
    const port = Number(new URL(server.origin).port);await stop(server);server = await start(database,port);
    await page.reload();await page.locator('.saved-draft').waitFor();
    assert.equal(await page.locator('#selection-count').textContent(),'5 selected');
    const stored = await page.evaluate(async (id)=>(await (await fetch('/api/bundle?project_id='+id)).json()), exported.project.id);
    assert.deepEqual(stored,exported);
  });
  await check('English and Japanese researcher explanations use curated terminology',async () => {
    await page.getByRole('button',{name:'Researcher guide / 利用ガイド'}).click();
    await page.locator('#help-language').selectOption('ja');await bodyContains(page,'humanizationは「ヒト化」です');
    assert.equal((await page.locator('#help-content').textContent()).includes('人源化'),false);
    await page.locator('#help-language').selectOption('en');await bodyContains(page,'Humanization means engineering');
    await page.getByRole('button',{name:'Close guide',exact:true}).click();
  });
  await check('duplicate ID rejected atomically; unknown fields and corrupt structures do not change state',async () => {
    const duplicate = await fromPage(page,'/api/import',exported);assert.equal(duplicate.status,422);
    const bad = structuredClone(exported);bad.unsupported_field='no';
    const unknown = await fromPage(page,'/api/import',bad);assert.equal(unknown.status,422);assert.ok(unknown.data.details.includes('bundle.unsupported_field'));
    const structure = await fromPage(page,'/api/preview',{text:'ATOM broken',format:'pdb',filename:'broken.pdb',project_id:exported.project.id,title:'',goal:''});assert.equal(structure.status,422);
    const current = await page.evaluate(async (id)=>(await (await fetch('/api/bundle?project_id='+id)).json()),exported.project.id);assert.deepEqual(current,exported);
  });
  await check('hostile imported text stays text with no script execution',async () => {
    const raw = '>hostile <img src=x onerror=window.INJECTED=1>\nEVQL';
    const preview = await fromPage(page,'/api/preview',{text:raw,format:'fasta',filename:'hostile.fa',project_id:exported.project.id,title:'',goal:''});assert.equal(preview.status,200);
    assert.equal((await fromPage(page,'/api/import',preview.data.bundle)).status,200);
    await page.reload();await navigate(page,'E');await page.getByRole('button',{name:'hostile <img src=x onerror=window.INJECTED=1>',exact:true}).waitFor();
    assert.equal(await page.evaluate(()=>window.INJECTED),undefined);assert.equal(await page.locator('td img').count(),0);
  });
  await check('800-candidate FASTA QC preview; valid subset explicitly saved; responsive UI',async () => {
    await page.getByRole('button',{name:'Import data',exact:true}).click();await page.locator('#import-target').selectOption('');
    await page.locator('#project-title').fill('[SYNTHETIC FIXTURE] 800 candidates');
    const raw = Array.from({length:800},(_,i)=>`>Batch-${i+1}\nEVQLVESGGGACD`).join('\n')+'\n>Missing\n>Invalid\nEVQ*';
    await page.locator('#import-text').fill(raw);await page.getByRole('button',{name:'Validate & preview'}).click();
    await bodyContains(page,'802 input rows · 800 valid · 2 excluded');await page.getByRole('button',{name:'Save 800 valid rows (excluded rows omitted)',exact:true}).click();
    await page.locator('#candidate-count').filter({hasText:'800'}).waitFor();
    await page.getByRole('checkbox',{name:'Select Batch-1',exact:true}).check();
    await page.evaluate(()=>window.scrollTo(0,0));
    await page.screenshot({path:path.join(evidenceDir,'M1-explorer-800.png')});
    await page.setViewportSize({width:390,height:844});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth),false);
    await page.screenshot({path:path.join(evidenceDir,'M1-mobile.png')});
    await page.setViewportSize({width:1440,height:1000});
  });
  await check('fresh environment JSON import roundtrip equals exported dataset',async () => {
    await stop(server);server = await start(path.join(temp,'fresh.sqlite3'));
    await page.goto(server.origin);await page.getByRole('button',{name:'Import data',exact:true}).click();
    await page.locator('#import-format').selectOption('json');await page.locator('#import-text').fill(JSON.stringify(exported));
    await page.getByRole('button',{name:'Validate & preview'}).click();await page.getByRole('button',{name:/Save \d+ valid rows/}).click();
    await page.locator('#candidate-count').filter({hasText:'8'}).waitFor();
    const current = await page.evaluate(async (id)=>(await (await fetch('/api/bundle?project_id='+id)).json()),exported.project.id);assert.deepEqual(current,exported);
  });
  await check('F06 declared units component order copy counts and lineage in the workspace',async () => {
    // Keep the existing fixture project to verify real same-workspace coexistence.
    await page.goto(server.origin);await page.getByRole('button',{name:'Import data',exact:true}).click();
    await page.getByRole('button',{name:'Preview composition fixture',exact:true}).click();
    await page.getByRole('button',{name:/Save \d+ valid rows/}).click();
    await page.locator('#candidate-count').filter({hasText:'9'}).waitFor();
    await page.getByRole('checkbox',{name:'Select COMP-001',exact:true}).check();
    await page.getByRole('button',{name:'Fixture tandem composition',exact:true}).click();
    await bodyContains(page,'tandem · 2 declared copies');await bodyContains(page,'partner · 1 declared copy');
    const firstChain = page.locator('.composition-chain').first();
    assert.deepEqual(await firstChain.locator('.component-item summary').allTextContents(),[
      'unit-A / declared binding segment / 32 aa','linker / linker / 3 aa','unit-B / declared binding segment / 32 aa'
    ]);
    await firstChain.locator('.component-item summary').first().click();
    await bodyContains(page,'Fixture binding unit 1');
    await page.getByRole('button',{name:/Inspect unit origin: Fixture candidate 001/}).click();
    assert.equal(await page.locator('.panel-head h2').first().textContent(),'Fixture candidate 001');
    assert.equal(await page.locator('#selection-count').textContent(),'1 selected');
    await page.getByText('Fixture candidate 001 → Fixture tandem composition',{exact:true}).first().click();
    await page.getByRole('button',{name:'Inspect child',exact:true}).first().click();
    assert.equal(await page.locator('.panel-head h2').first().textContent(),'Fixture tandem composition');
    await navigate(page,'R');await bodyContains(page,'Not measured / not predicted. No evidence records');
    assert.equal(await page.locator('.tag.measured').count(),0);
    await navigate(page,'W');await page.evaluate(()=>window.scrollTo(0,0));
    await page.screenshot({path:path.join(evidenceDir,'M1-composition-screen.png'),fullPage:true});
    const original = await page.evaluate(async () => {
      const projects = (await (await fetch('/api/bootstrap')).json()).projects;
      if (projects.length !== 2) throw new Error('Both fixture projects must coexist');
      const project = projects.find((p)=>p.title.includes('Explicit composition'));
      return await (await fetch('/api/bundle?project_id='+project.id)).json();
    });
    const port = Number(new URL(server.origin).port);await stop(server);server=await start(path.join(temp,'fresh.sqlite3'),port);
    await page.reload();await bodyContains(page,'tandem · 2 declared copies');
    const restart = await page.evaluate(async (id)=>(await (await fetch('/api/bundle?project_id='+id)).json()),original.project.id);
    assert.deepEqual(restart,original);
    await stop(server);server=await start(path.join(temp,'composition-fresh.sqlite3'));
    await page.goto(server.origin);await page.getByRole('button',{name:'Import data',exact:true}).click();
    await page.locator('#import-format').selectOption('json');await page.locator('#import-text').fill(JSON.stringify(original));
    await page.getByRole('button',{name:'Validate & preview'}).click();await page.getByRole('button',{name:/Save \d+ valid rows/}).click();
    await page.locator('#candidate-count').filter({hasText:'9'}).waitFor();
    const reimported = await page.evaluate(async (id)=>(await (await fetch('/api/bundle?project_id='+id)).json()),original.project.id);
    assert.deepEqual(reimported,original);
    const corrupted = structuredClone(original);const graphMolecule=corrupted.entities.find((e)=>e.component_graph);
    graphMolecule.component_graph.chains[0].copies=true;
    assert.equal((await fromPage(page,'/api/import',corrupted)).status,422);
    const unchanged=await page.evaluate(async(id)=>(await (await fetch('/api/bundle?project_id='+id)).json()),original.project.id);
    assert.deepEqual(unchanged,original);
  });
  assert.deepEqual(outbound,[]);assert.deepEqual(consoleErrors,[]);
  results.push({name:'no outbound browser requests or JavaScript errors',status:'PASS'});
  const report = {scope:'M1 foundation F01-F06; not final 8/8 or 16/16 acceptance',status:'PASS',timestamp:new Date().toISOString(),browser:await browser.version(),dataset_sha256:crypto.createHash('sha256').update(JSON.stringify(exported)).digest('hex'),results};
  fs.writeFileSync(path.join(evidenceDir,'M1-browser-results.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify({status:report.status,checks:results.length,browser:report.browser}));
})().catch((error)=>{console.error(error);fs.writeFileSync(path.join(evidenceDir,'M1-browser-failure.json'),JSON.stringify({timestamp:new Date().toISOString(),error:String(error),results},null,2));process.exitCode=1;}).finally(async()=>{if(browser)await browser.close();await stop(server);});
