// P05/J05/AC-J05 public-source browser replay. The alternative is a comparison declaration.
const assert = require('node:assert/strict');
const {spawn, spawnSync} = require('node:child_process');
const {createHash} = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {chromium} = require('playwright');

const root = path.resolve(__dirname, '..');
const input = path.join(root, 'validation', 'public');
const output = path.resolve(process.argv[2] || fs.mkdtempSync(path.join(os.tmpdir(), 'awx-m13-report-')));
const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'awx-m13-store-'));
const python = process.env.PYTHON || path.join(root, '.venv', 'Scripts', 'python.exe');
const database = path.join(temp, 'source.sqlite3');
const expectations = JSON.parse(fs.readFileSync(path.join(root, 'validation', 'emicizumab-reference-expectations.json'), 'utf8'));
const expectVisibleConnections = process.argv.includes('--visible-connections');
const chainOrder = ['Q', 'J', 'L1', 'L2'];
const errors = [], outbound = [], checks = [];
let child, browser, context, page, origin;

function digest(file) {
  return createHash('sha256').update(fs.readFileSync(file)).digest('hex');
}

async function start(file, port = 0) {
  child = spawn(python, ['-m', 'workspace_app.server', '--database', file, '--port', String(port)], {cwd:root, windowsHide:true});
  origin = await new Promise((resolve, reject) => {
    const timeout = setTimeout(() => reject(Error('Server startup timed out')), 20000);
    child.once('error', reject);
    child.once('exit', (code) => { clearTimeout(timeout); reject(Error(`Server exited ${code}`)); });
    child.stdout.on('data', (data) => {
      const match = String(data).match(/http:\/\/127\.0\.0\.1:\d+/);
      if (match) { clearTimeout(timeout); resolve(match[0]); }
    });
  });
}

async function stop() {
  if (child?.exitCode === null && child.signalCode === null) {
    await new Promise((resolve) => { child.once('exit', resolve); child.kill(); });
  }
}

async function openPage() {
  context = await browser.newContext({viewport:{width:1440,height:1000}, acceptDownloads:true});
  await context.route('**/*', (route) => {
    const url = route.request().url();
    if (url.startsWith(`${origin}/`)) return route.continue();
    outbound.push(url);
    return route.abort();
  });
  page = await context.newPage();
  page.on('pageerror', (error) => errors.push(error.message));
  await page.goto(origin);
  await page.waitForFunction(() => !document.querySelector('#import-button').disabled);
}

const button = (name) => page.getByRole('button', {name, exact:true});
const fill = (id, value) => page.locator(`#${id}`).fill(value);
const nav = (screen) => page.locator(`nav [data-screen="${screen}"]`).click();
const read = (id) => page.evaluate(async (project) => (await fetch(`/api/bundle?project_id=${project}`)).json(), id);
const preview = () => button('Validate & preview').click();

async function saveImport() {
  await page.locator('#commit-import').click();
  await page.locator('#import-dialog').waitFor({state:'hidden'});
  await page.waitForFunction(() => !document.querySelector('#import-button').disabled && document.querySelector('#project-select').value);
}

function unitBundle(bundle) {
  const code = [
    'import json,runpy,sys',
    "source=runpy.run_path('TEST_EVIDENCE/M11-emicizumab-composition-probe.py')",
    'bundle=json.load(sys.stdin)',
    'molecule,=bundle["entities"]',
    'print(json.dumps({**bundle,"entities":list(source["source_units"](molecule))}))',
  ].join('\n');
  const result = spawnSync(python, ['-c',code], {cwd:root, input:JSON.stringify(bundle), encoding:'utf8', windowsHide:true});
  assert.equal(result.status, 0, result.stderr);
  return JSON.parse(result.stdout);
}

async function compositionPreview() {
  await button('Review new composition before saving').click();
  await page.locator('#composition-preview-dialog').waitFor({state:'visible'});
  return JSON.parse(await page.locator('#composition-preview-content > pre').textContent());
}

async function saveComposition() {
  await button('Save reviewed composition records').click();
  await page.locator('#composition-preview-dialog').waitFor({state:'hidden'});
  await button('Inspect saved composition in W').waitFor();
}

(async () => {
  fs.mkdirSync(output, {recursive:true});
  assert.equal(digest(path.join(input, 'emicizumab-gsrs.json')), expectations.input_sha256);
  const fasta = path.join(input, 'emicizumab.fasta');
  assert.equal(digest(fasta), expectations.derived_fasta_sha256);
  await start(database);
  browser = await chromium.launch({headless:true, channel:process.env.PLAYWRIGHT_CHANNEL || 'chrome'});
  await openPage();
  await button('Import data').click();
  await page.locator('#import-format').selectOption('fasta_grouped');
  await page.locator('#import-file').setInputFiles(fasta);
  await fill('project-title', 'Emicizumab public composition review');
  await preview();
  const rows = page.locator('[data-sequence-record]');
  await rows.last().waitFor();
  assert.equal(await rows.count(), 4);
  for (const [index, chain] of chainOrder.entries()) {
    const row = rows.nth(index);
    await row.locator('[data-group-candidate]').fill('EMI-GSRS');
    await row.locator('[data-group-chain]').fill(chain);
    await row.locator('[data-group-role]').fill(index < 2 ? 'heavy' : 'light');
  }
  await fill('group-molecular-format', 'Asymmetric bispecific IgG4');
  await page.locator('#apply-sequence-grouping').click();
  await saveImport();
  const project = await page.locator('#project-select').inputValue();
  const original = await read(project);
  const source = original.entities[0];
  const [q, j, l1, l2] = source.chains;
  assert.deepEqual(source.chains.map((chain) => [chain.id,chain.sequence.length]), [['Q',448],['J',444],['L1',214],['L2',214]]);
  assert.notEqual(q.sequence, j.sequence);
  assert.equal(l1.sequence, l2.sequence);

  // The registry supplies the two source pairs. Import their explicit bindings via the existing file route.
  const seed = unitBundle(original);
  const unitsFile = path.join(temp,'public-binding-units.json');
  fs.writeFileSync(unitsFile, JSON.stringify(seed));
  await button('Import data').click();
  await page.locator('#import-file').setInputFiles(unitsFile);
  await preview();
  await saveImport();
  for (const unit of seed.entities) await page.locator(`[data-unit-select="${unit.id}"]`).check();
  await button('Design an explicit composition').click();
  await fill('composition-name', 'Emicizumab registry declaration');
  await fill('composition-external', 'EMI-DECLARED');
  await fill('composition-format', 'Asymmetric bispecific IgG4');
  await fill('composition-note', 'GSRS v37 identifies four interchain disulfides. This declaration records the three linked component pairs.');
  assert.equal(await button('Review new composition before saving').isDisabled(), true);
  checks.push('empty_recipe_cannot_be_previewed');

  const endpoints = {};
  for (const [index, name] of chainOrder.entries()) {
    const unit = seed.entities.find((entry) => entry.chains.some((chain) => chain.id === name));
    await button('Add an explicit chain').click();
    const chain = page.locator(`fieldset[data-recipe-chain="${index}"]`);
    await chain.locator('[data-chain-field="id"]').fill(name);
    await chain.locator('[data-chain-field="role"]').fill(index < 2 ? 'heavy' : 'light');
    await chain.locator('[data-chain-field="copies"]').fill('1');
    await chain.locator(`[data-part-add="${index}"]`).click();
    const part = chain.locator('.composition-part');
    await part.locator('[data-part-field="role"]').fill('Complete source chain');
    await part.locator('[data-part-unit]').selectOption(unit.id);
    await part.locator('[data-part-source-chain]').selectOption(name);
    await part.getByRole('button',{name:'Use full declared source chain',exact:true}).click();
    endpoints[name] = JSON.stringify({chain_id:name, component_id:await part.locator('[data-part-field="id"]').inputValue()});
  }
  const expectedPairs = [['Q','L1'],['J','L2'],['Q','J']];
  for (const [index, [left,right]] of expectedPairs.entries()) {
    await button('Add an explicit connection').click();
    const row = page.locator(`[data-recipe-connection="${index}"]`);
    await row.locator('[data-connection-side="left"]').selectOption(endpoints[left]);
    await row.locator('[data-connection-side="right"]').selectOption(endpoints[right]);
    await row.locator('[data-connection-kind]').selectOption('disulfide');
  }
  const base = await compositionPreview();
  const parent = base.entities[0];
  const graph = parent.component_graph;
  assert.deepEqual(graph.connections.map(({left,right}) => [left.chain_id,right.chain_id]),expectedPairs);
  assert.deepEqual(parent.chains,source.chains);
  assert.deepEqual(graph.chains.map((chain) => [chain.chain_id,chain.copies,chain.components[0].origin.chain_id]),chainOrder.map((name) => [name,1,name]));
  await saveComposition();
  await button('Inspect saved composition in W').click();
  const selector = page.getByRole('combobox',{name:'Chain for EMI-DECLARED',exact:true});
  for (const name of ['L1','L2']) {
    await selector.selectOption(name);
    assert.match(await selector.locator('option:checked').textContent(),/214 aa/);
    const jump = page.locator(`[data-jump="${parent.id}"]`);
    await jump.fill('214');
    await jump.press('Tab');
    await page.locator(`[data-position-molecule="${parent.id}"][data-position-chain="${name}"][data-position="214"].active`).waitFor();
    const component = page.locator('.component-item').filter({hasText:JSON.parse(endpoints[name]).component_id});
    await component.locator('summary').click();
    const unit = seed.entities.find((entry) => entry.chains.some((chain) => chain.id === name));
    assert.match(await component.textContent(),new RegExp(unit.id));
  }
  checks.push('four_public_chains_and_two_distinct_light_chain_sources');

  await nav('D');
  await button('Use saved composition as parent recipe').click();
  await fill('composition-name','Comparison declaration with Q–J connection omitted');
  await fill('composition-external','EMI-REVIEW-ALT');
  await fill('composition-reason','Check whether the declared Q–J component link can be distinguished from the two retained light-chain links. The original registry remains the source for disulfide residues.');
  await page.locator('[data-recipe-connection="2"] [data-connection-remove]').click();
  const alternative = await compositionPreview();
  const childDesign = alternative.entities[0];
  const lineage = alternative.entities.find((entry) => entry.type === 'lineage');
  assert.equal(lineage.parent_id,parent.id);
  assert.deepEqual(childDesign.chains,parent.chains);
  assert.deepEqual(childDesign.component_graph.chains,graph.chains);
  assert.deepEqual(childDesign.component_graph.connections,graph.connections.slice(0,2));
  await saveComposition();
  const comparison = page.locator('#composition-contexts');
  await comparison.getByRole('heading',{name:/EMI-REVIEW-ALT/}).waitFor();
  assert.equal(await comparison.getByText(/Whole-molecule structure prediction: unsupported/).count(),2);
  assert.equal(await page.getByRole('button',{name:/Run.*prediction|Predict.*structure/}).count(),0);
  if (expectVisibleConnections) {
    const tables = await comparison.getByRole('table',{name:'Declared component connections'}).all();
    assert.equal(tables.length,2);
    const expected = graph.connections.map(({left,right,kind}) => [`${left.chain_id} / ${left.component_id}`,kind,`${right.chain_id} / ${right.component_id}`]);
    for (const [index, table] of tables.entries()) {
      const body = await table.locator('tbody tr').all();
      const actual = await Promise.all(body.map((row) => row.locator('td').allTextContents()));
      assert.deepEqual(actual,index === 0 ? expected : expected.slice(0,2));
      assert.ok((await table.boundingBox()).y >= 0);
      assert.ok(await table.evaluate((element) => element.getBoundingClientRect().bottom <= innerHeight));
    }
    assert.equal(await comparison.locator('article details[open] > pre').count(),0);
    await page.screenshot({path:path.join(output,'composition-first-view.png')});
    checks.push('declared_endpoints_and_kinds_visible_without_json_disclosure');
  }
  for (const column of await comparison.locator('article').all()) {
    await column.getByText('Exact graph, declared connections and source usage',{exact:true}).click();
  }
  const visibleGraphs = await comparison.locator('article details > pre').allTextContents();
  const compared = visibleGraphs.map((text) => JSON.parse(text).molecule.component_graph.connections.length);
  assert.deepEqual(compared,[3,2]);
  await page.screenshot({path:path.join(output,'composition-comparison.png'),fullPage:true});
  checks.push('alternative_preserves_sequences_and_differs_only_in_declared_graph', 'unsupported_prediction_has_no_action');

  await nav('E');
  const selected = page.locator('[data-select]:checked');
  for (const item of await selected.all()) {
    if (![parent.id,childDesign.id].includes(await item.getAttribute('data-select'))) await item.uncheck();
  }
  for (const id of [parent.id,childDesign.id]) await page.locator(`[data-select="${id}"]`).check();
  await nav('R');
  await button('Record research hypothesis').click();
  await fill('hypothesis-text','The reference declaration retains the public Q–J component link. The comparison declaration omits that link and leaves all four chain sequences identical.');
  await fill('hypothesis-question','Reconcile the declared component links against the registry residue-level disulfide record before treating either graph as a structural model.');
  await fill('hypothesis-limitations','The alternate declaration has no assembly or functional evidence. The application graph does not retain two separate Q–J residue-level bonds.');
  const annotation = (await read(project)).entities.find((entry) => entry.type === 'evidence' && entry.subject_id === parent.id);
  await page.locator(`[data-hypothesis-evidence="${annotation.id}"]`).check();
  await page.locator(`[data-hypothesis-lineage="${lineage.id}"]`).check();
  await button('Review hypothesis before saving').click();
  await page.locator('#design-preview-dialog').waitFor({state:'visible'});
  await button('Save reviewed records').click();
  await page.locator('.saved-hypothesis').waitFor();
  const saved = await read(project);
  assert.ok(saved.entities.filter((entry) => entry.type === 'evidence').every((entry) => entry.kind === 'annotation'));
  assert.ok(saved.entities.find((entry) => entry.type === 'hypothesis').lineage_ids.includes(lineage.id));

  const port = Number(new URL(origin).port);
  await stop();
  await start(database,port);
  await page.reload();
  await page.locator('.saved-hypothesis').waitFor();
  assert.deepEqual(await read(project),saved);
  const download = page.waitForEvent('download');
  await page.locator('#export-button').click();
  const archive = path.join(temp,'emicizumab-transfer.json');
  await (await download).saveAs(archive);
  assert.deepEqual(JSON.parse(fs.readFileSync(archive,'utf8')),saved);
  await context.close();
  await stop();
  await start(path.join(temp,'restored.sqlite3'));
  await openPage();
  await button('Import data').click();
  await page.locator('#import-file').setInputFiles(archive);
  await preview();
  await saveImport();
  assert.deepEqual(await read(project),saved);
  checks.push('original_annotations_and_proposed_reasoning_survive_restart_and_transfer');

  assert.deepEqual(errors,[]);
  assert.deepEqual(outbound,[]);
  const result = {status:'PASS',timestamp:new Date().toISOString(),browser:browser.version(),sourceSha256:expectations.input_sha256,scope:'Public source composition with a hypothetical comparison declaration',checks,errors,outbound};
  fs.writeFileSync(path.join(output,'results.json'),JSON.stringify(result,null,2)+'\n');
  console.log(JSON.stringify(result));
})().catch(async (error) => {
  console.error(error);
  if (page) await page.screenshot({path:path.join(output,'failure.png'),fullPage:true}).catch(() => {});
  process.exitCode = 1;
}).finally(async () => {
  await browser?.close();
  await stop();
});
