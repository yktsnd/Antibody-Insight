// F29 / AC-J01, AC-J04, AC-J06, AC-J07. All input values are synthetic.
const assert = require('node:assert/strict');
const {spawn, spawnSync} = require('node:child_process');
const {createHash} = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {chromium} = require('playwright');

const root = path.resolve(__dirname, '..');
const python = process.env.PYTHON || path.join(root, '.venv', 'Scripts', 'python.exe');
const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'awx-observation-comparison-'));
const output = process.env.AWX_COMPARISON_EVIDENCE || path.join(temp, 'comparison.json');
const baseline = process.argv.includes('--baseline');
const fixture = spawnSync(python, ['-c', [
  'import copy, json',
  'from workspace_app.fixtures import research_example_bundle, fixture_id',
  'bundle = research_example_bundle()',
  'records = bundle["entities"]',
  'original = next(e for e in records if e["type"] == "evidence" and e["value"] == 120)',
  'original["value"] = 0',
  'alternate = next(e for e in records if e["type"] == "material" and e["name"] == "Fixture alternate lot")',
  'records.append(dict(copy.deepcopy(original), id=fixture_id("evidence", "comparison-repeat"), subject_id=alternate["id"], value=12))',
  'records.append(dict(copy.deepcopy(original), id=fixture_id("evidence", "comparison-unit"), unit="mRU", value=12000))',
  'floating = dict(copy.deepcopy(original), id=fixture_id("evidence", "comparison-float"), value=30)',
  'floating["conditions"]["temperature_C"] = 25.0',
  'records.append(floating)',
  'print(json.dumps(bundle))',
].join('\n')], {cwd: root, encoding: 'utf8', windowsHide: true});
assert.equal(fixture.status, 0, fixture.stderr);
const bundle = JSON.parse(fixture.stdout);
const original = bundle.entities.find((e) => e.type === 'evidence' && e.value === 90);
const server = spawn(python, ['-m', 'workspace_app.server', '--database', path.join(temp, 'test.sqlite3'), '--port', '0'],
  {cwd: root, windowsHide: true});
let browser;

async function run() {
  const origin = await new Promise((resolve, reject) => {
    const timeout = setTimeout(() => reject(Error('Workspace server did not start')), 15000);
    server.once('error', reject);
    server.once('exit', (code) => { clearTimeout(timeout); reject(Error('Workspace exited: ' + code)); });
    server.stdout.on('data', (buffer) => {
      const match = buffer.toString().match(/http:\/\/127\.0\.0\.1:\d+/);
      if (match) { clearTimeout(timeout); resolve(match[0]); }
    });
  });
  browser = await chromium.launch({headless: true, channel: process.env.PLAYWRIGHT_CHANNEL || 'chrome'});
  const page = await browser.newPage({viewport: {width: 1440, height: 1000}});
  const outside = [];
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.route('**/*', (route) => {
    if (route.request().url().startsWith(origin + '/')) return route.continue();
    outside.push(route.request().url());
    return route.abort();
  });
  await page.goto(origin);
  await page.locator('#import-button').click();
  await page.locator('#import-format').selectOption('json');
  await page.locator('#import-text').fill(fixture.stdout);
  await page.getByRole('button', {name: 'Validate & preview', exact: true}).click();
  await page.locator('#commit-import').click();
  await page.locator('.sequence').first().waitFor();
  await page.locator('nav [data-screen="R"]').click();
  await page.locator('#shortlist-reason').waitFor();
  await page.locator('#expression-material').waitFor();
  await page.evaluate(() => scrollTo(0, 0));
  const source = page.locator('#evidence-' + original.id);
  const table = page.locator('#candidate-observations');
  const link = table.locator(`[data-source-evidence="${original.id}"]`);
  const entry = await page.evaluate((id) => ({
    documentHeight: document.documentElement.scrollHeight,
    originalRecordTop: Math.round(document.getElementById('evidence-' + id).getBoundingClientRect().top + scrollY),
    viewportHeight: innerHeight,
  }), original.id);
  const targetBox = await (baseline ? source : link).boundingBox();
  entry.valueVisibleInitially = targetBox.y >= 0 && targetBox.y + targetBox.height <= entry.viewportHeight;
  entry.scrollBeforeFirstPixel = Math.max(0, Math.ceil(targetBox.y - entry.viewportHeight));
  await page.screenshot({path: output.replace(/\.json$/, '.png')});

  const checks = [];
  if (!baseline) {
    assert.equal(entry.valueVisibleInitially, true);
    const matched = table.getByRole('row').filter({hasText: '"temperature_C":25}'}).filter({hasText: /\bRU\b/});
    assert.equal(await matched.count(), 1);
    assert.match(await matched.textContent(), /2 original observations/);
    await matched.getByText('2 original observations', {exact: true}).click();
    assert.ok(await matched.getByRole('button', {name: /^0 RU/}).isVisible());
    assert.ok(await matched.getByRole('button', {name: /^12 RU/}).isVisible());
    assert.ok(await matched.getByRole('button', {name: /^90 RU/}).isVisible());
    assert.ok(await matched.getByText('fixture-lot-B', {exact: false}).isVisible());
    const differentCondition = table.getByRole('row').filter({hasText: '"temperature_C":37'});
    assert.equal(await differentCondition.getByRole('button', {name: /^90 RU/}).count(), 0);
    assert.ok(await differentCondition.getByText('No record in this context', {exact: true}).isVisible());
    const picker = table.getByRole('combobox', {name: 'Observation context'});
    const unitOption = await picker.getByRole('option').filter({hasText: ' / mRU / '}).getAttribute('value');
    await picker.selectOption(unitOption);
    const differentUnit = table.getByRole('row').filter({hasText: 'mRU'});
    assert.ok(await differentUnit.getByRole('button', {name: /^12000 mRU/}).isVisible());
    assert.equal(await differentUnit.getByRole('button', {name: /^90 RU/}).count(), 0);
    const floatOption = await picker.getByRole('option').filter({hasText: '"temperature_C":25.0}'}).getAttribute('value');
    await picker.selectOption(floatOption);
    assert.ok(await table.getByRole('button', {name: /^30 RU/}).isVisible());
    assert.equal(await link.count(), 0);
    await table.getByRole('button', {name: /^30 RU/}).click();
    assert.match(await page.locator(':focus').textContent(), /"temperature_C":25\.0\}/);
    const thermalOption = await picker.getByRole('option').filter({hasText: 'illustrative_transition_temperature'}).getAttribute('value');
    await picker.selectOption(thermalOption);
    const thermal = table.getByRole('row').filter({hasText: 'illustrative_transition_temperature'});
    assert.ok(await thermal.getByRole('button', {name: /^Value missing/}).isVisible());
    await picker.selectOption('');
    checks.push('condition and unit boundaries; original records for two lots; exact integer and float labels; null, absent and zero');

    await page.locator('#shortlist-reason').fill('Synthetic draft retained during source inspection.');
    await page.evaluate(() => scrollTo(0, 0));
    await link.click();
    assert.equal(await page.evaluate(() => document.activeElement.id), 'evidence-' + original.id);
    assert.match(await source.textContent(), /90\s+RU/);
    assert.equal(await page.locator('#shortlist-reason').inputValue(), 'Synthetic draft retained during source inspection.');
    await page.locator('nav [data-screen="W"]').click();
    await page.locator('nav [data-screen="R"]').click();
    assert.equal(await page.locator('#selection-count').textContent(), '2 selected');
    assert.equal(await page.locator('#shortlist-reason').inputValue(), 'Synthetic draft retained during source inspection.');
    checks.push('one source action focuses the exact Evidence; W/R round trip preserves candidate and draft state');
  }
  assert.deepEqual(errors, []);
  assert.deepEqual(outside, []);
  const sha256 = (bytes) => createHash('sha256').update(bytes).digest('hex');
  const files = ['web/app.js', 'web/decisions.js', 'web/style.css', 'workspace_app/observation.py', 'workspace_app/decisions.py'];
  const sourceSha256 = Object.fromEntries(files.map((file) => [file, sha256(fs.readFileSync(path.join(root, file)))]));
  const report = {status: 'PASS', baseline, scope: 'Synthetic engineering fixture at 1440 × 1000',
    fixtureSha256: sha256(fixture.stdout), sourceSha256, entry, checks, errors, outside};
  fs.writeFileSync(output, JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify(report));
}

run().catch((error) => {
  console.error(error);
  process.exitCode = 1;
}).finally(async () => {
  try { await browser?.close(); } finally { server.kill(); }
});
