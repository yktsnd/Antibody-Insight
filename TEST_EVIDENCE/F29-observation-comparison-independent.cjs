const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {spawn, spawnSync} = require('node:child_process');
const {chromium} = require('playwright');
const artifactDirectory = fs.mkdtempSync(path.join(os.tmpdir(), 'awx-f29-review-'));
const artifact = (name) => path.join(artifactDirectory, name);
const fixture = spawnSync(process.env.PYTHON, ['-c', [
  'import copy, json',
  'from workspace_app.fixtures import example_bundle, fixture_id',
  'bundle = example_bundle(3)',
  'records = bundle["entities"]',
  'a, b, c = [r for r in records if r["type"] == "molecule"]',
  'observations = [r for r in records if r["type"] == "evidence" and r["kind"] == "measured"]',
  'first, second, outside = observations',
  'first.update(value=10, metric="typed temperatures")',
  'second.update(value=20, metric="typed temperatures", conditions=dict(first["conditions"], temperature_C=25.0))',
  'outside.update(value=30, metric="outside scope", conditions=dict(first["conditions"]))',
  'def add(label, base, **updates):',
  '    record = dict(copy.deepcopy(base), id=fixture_id("evidence", label))',
  '    record.update(updates)',
  '    records.append(record)',
  '    return record["id"]',
  'source_other = add("edge-source-version", first, value=11, source=dict(first["source"], version="2"))',
  'computed = add("edge-computed-construct", first, kind="computed", value=12, subject_id=next(r["id"] for r in records if r["type"] == "construct" and r["molecule_id"] == a["id"]))',
  'repeat_subject = add("edge-repeat-subject", first, value=10, timestamp="2026-11-03T00:00:00+00:00")',
  'signed_zero_condition = add("edge-negative-zero", first, value=-0.0, metric="signed-zero conditions", conditions=dict(first["conditions"], temperature_C=-0.0))',
  'positive_zero_condition = add("edge-positive-zero", first, value=15, metric="signed-zero conditions", conditions=dict(first["conditions"], temperature_C=0.0))',
  'metadata = dict(a=a["id"], b=b["id"], c=c["id"], first=first["id"], second=second["id"], outside=outside["id"], source_other=source_other, computed=computed, repeat_subject=repeat_subject, signed_zero_condition=signed_zero_condition, positive_zero_condition=positive_zero_condition)',
  'print(json.dumps(metadata))',
  'print(json.dumps(bundle))',
].join('\n')], {encoding: 'utf8', windowsHide: true});
assert.equal(fixture.status, 0, fixture.stderr);
const newline = fixture.stdout.indexOf('\n');
const ids = JSON.parse(fixture.stdout.slice(0, newline));
const input = fixture.stdout.slice(newline + 1);
const bundle = JSON.parse(input);
const report = {scope: 'Independent replay, isolated store and synthetic fixtures', checks: [], errors: [], external: [], network: []};
const server = spawn(process.env.PYTHON, ['-m', 'workspace_app.server', '--database', artifact('independent.sqlite3'), '--port', '0'], {windowsHide: true});
let browser;

async function run() {
  const origin = await new Promise((resolve, reject) => {
    const timeout = setTimeout(() => reject(Error('Workspace server did not start')), 15000);
    server.once('error', reject);
    server.once('exit', (code) => {clearTimeout(timeout); reject(Error('Workspace exited: ' + code));});
    server.stdout.on('data', (chunk) => {
      const address = chunk.toString().match(/http:\/\/127\.0\.0\.1:\d+/);
      if (address) {clearTimeout(timeout); resolve(address[0]);}
    });
  });
  browser = await chromium.launch({headless: true, channel: 'chrome'});
  const page = await browser.newPage({viewport: {width: 1440, height: 1000}});
  page.on('pageerror', (error) => report.errors.push(error.message));
  page.on('request', (request) => report.network.push([request.method(), request.url().replace(origin, '')]));
  await page.route('**/*', (route) => {
    const url = route.request().url();
    if (url.startsWith(origin + '/')) return route.continue();
    report.external.push(url);
    return route.abort();
  });
  await page.goto(origin);
  await page.locator('#import-button').click();
  await page.locator('#import-format').selectOption('json');
  await page.locator('#import-text').fill(input);
  await page.getByRole('button', {name: 'Validate & preview', exact: true}).click();
  await page.locator('#commit-import').click();
  await page.locator('[data-select]').first().waitFor();
  for (const id of [ids.a, ids.b]) await page.locator('[data-select="' + id + '"]').check();
  assert.equal(await page.locator('#selection-count').textContent(), '2 selected');
  const bundleUrl = origin + '/api/bundle?project_id=' + bundle.project.id;
  const originalBundle = await (await page.request.get(bundleUrl)).text();
  assert.match(originalBundle, /"temperature_C"\s*:\s*25\.0/);
  assert.match(originalBundle, /"temperature_C"\s*:\s*-0\.0/);

  await page.locator('nav [data-screen="R"]').click();
  const table = page.locator('#candidate-observations');
  const dropdown = table.locator('select');
  await dropdown.waitFor();
  const repeated = [ids.first, ids.repeat_subject];
  const integer = await dropdown.locator('option').evaluateAll((options, targets) => options.find((option) => targets.includes(option.value)).value, repeated);
  const options = {};
  for (const id of [integer, ids.second, ids.source_other, ids.computed, ids.signed_zero_condition, ids.positive_zero_condition]) {
    options[id] = await dropdown.locator('option[value="' + id + '"]').textContent();
  }
  assert.equal(await dropdown.locator('option[value="' + ids.outside + '"]').count(), 0);
  assert.equal(await page.locator('#evidence-' + ids.outside).count(), 0);
  assert.equal(await table.getByRole('columnheader').filter({hasText: 'FIX-003'}).count(), 0);
  await dropdown.selectOption(integer);
  const integerLabel = await table.getByRole('rowheader').textContent();
  assert.equal(await table.locator('[data-source-evidence="' + ids.second + '"]').count(), 0);
  await dropdown.selectOption(ids.second);
  const floatLabel = await table.getByRole('rowheader').textContent();
  assert.equal(await table.locator('[data-source-evidence="' + ids.first + '"]').count(), 0);
  assert.ok(await table.locator('[data-source-evidence="' + ids.second + '"]').isVisible());
  const distinctNumbers = /"temperature_C":25}/.test(options[integer]) &&
    /"temperature_C":25\.0}/.test(options[ids.second]) &&
    /"temperature_C":25}/.test(integerLabel) && /"temperature_C":25\.0}/.test(floatLabel);
  const signedZero = /"temperature_C":-0\.0}/.test(options[ids.signed_zero_condition]) &&
    /"temperature_C":0\.0}/.test(options[ids.positive_zero_condition]);
  report.checks.push({name:'numeric context types stay distinguishable', status:distinctNumbers && signedZero ? 'PASS' : 'FAIL',
    integer:{id:integer, option:options[integer], row:integerLabel}, float:{id:ids.second, option:options[ids.second], row:floatLabel},
    signedZero:{negative:options[ids.signed_zero_condition], positive:options[ids.positive_zero_condition]}});
  await page.screenshot({path:artifact('independent-typed-conditions.png')});

  await page.locator('[data-research-task="decision"]').click();
  const criterionContext = page.locator('#decision-add-context');
  await criterionContext.waitFor();
  await criterionContext.selectOption(integer);
  await page.locator('#decision-add-criterion').click();
  const weight = page.locator('[data-criterion-field="weight"]');
  await weight.fill('2.5');
  const reason = page.locator('#decision-reason');
  await reason.fill('Independently retained synthetic trade-off.');
  const evidencePanel = page.locator('#decision-original-evidence');
  assert.equal(await evidencePanel.evaluate((element) => element.open), false);
  const networkStart = report.network.length;

  await dropdown.selectOption(ids.source_other);
  assert.match(await table.getByRole('rowheader').textContent(), /experiment\) 2/);
  const link = table.locator('[data-source-evidence="' + ids.source_other + '"]');
  await link.click();
  assert.equal(await evidencePanel.evaluate((element) => element.open), true);
  assert.equal(await page.evaluate(() => document.activeElement.id), 'evidence-' + ids.source_other);
  const sourceCard = page.locator('#evidence-' + ids.source_other);
  await sourceCard.getByText('Original record, subject IDs & provenance').click();
  const shownRecord = JSON.parse(await sourceCard.locator('pre').textContent());
  const inputRecord = bundle.entities.find((record) => record.id === ids.source_other);
  assert.deepEqual(shownRecord, inputRecord);
  assert.match(await sourceCard.textContent(), new RegExp(inputRecord.timestamp.replace(/[+]/g, '\\+')));
  assert.equal(await reason.inputValue(), 'Independently retained synthetic trade-off.');
  assert.equal(await weight.inputValue(), '2.5');

  await dropdown.selectOption(ids.computed);
  assert.ok(await table.getByRole('rowheader').getByText('computed', {exact: true}).isVisible());
  assert.equal(await table.locator('[data-source-evidence="' + ids.first + '"]').count(), 0);
  await table.locator('[data-source-evidence="' + ids.computed + '"]').click();
  const computedCard = page.locator('#evidence-' + ids.computed);
  assert.equal(await page.evaluate(() => document.activeElement.id), 'evidence-' + ids.computed);
  assert.match(await computedCard.textContent(), /construct: Fixture construct 1/);
  assert.equal(await reason.inputValue(), 'Independently retained synthetic trade-off.');
  assert.equal(await weight.inputValue(), '2.5');

  await dropdown.selectOption(integer);
  await table.getByText('2 original observations', {exact:true}).click();
  await table.locator('[data-source-evidence="' + ids.repeat_subject + '"]').click();
  assert.equal(await page.evaluate(() => document.activeElement.id), 'evidence-' + ids.repeat_subject);
  assert.match(await page.locator('#evidence-' + ids.repeat_subject).textContent(), /2026-11-03/);
  assert.equal(await reason.inputValue(), 'Independently retained synthetic trade-off.');
  assert.equal(await weight.inputValue(), '2.5');
  assert.deepEqual(report.network.slice(networkStart), []);
  assert.equal(await (await page.request.get(bundleUrl)).text(), originalBundle);
  report.checks.push({name:'candidate scope, source version, original construct/material identities, and no save on browse', status:'PASS',
    ids, selection:await page.locator('#selection-count').textContent(),
    decisionDraft:{weight:await weight.inputValue(), reason:await reason.inputValue()}, requestsDuringComparison:report.network.slice(networkStart), bundleByteIdentical:true});
  await page.screenshot({path:artifact('independent-source-focus.png')});
  await dropdown.selectOption(ids.signed_zero_condition);
  assert.match(await table.getByRole('rowheader').textContent(), /"temperature_C":-0\.0}/);
  const signedZeroSource = table.locator('[data-source-evidence="' + ids.signed_zero_condition + '"]');
  assert.match(await signedZeroSource.textContent(), /^-0 nM/);
  await signedZeroSource.click();
  const signedZeroCard = page.locator('#evidence-' + ids.signed_zero_condition);
  assert.equal(await page.evaluate(() => document.activeElement.id), 'evidence-' + ids.signed_zero_condition);
  assert.match(await signedZeroCard.textContent(), /"temperature_C":-0\.0}/);
  assert.match(await signedZeroCard.locator('.value').textContent(), /^-0\s+nM$/);
  report.checks.push({name:'negative-zero scalar agrees in comparison and original Evidence', status:'PASS',
    comparison:await signedZeroSource.textContent(), original:await signedZeroCard.locator('.value').textContent()});
  await page.screenshot({path:artifact('independent-signed-zero-original.png')});

  await dropdown.selectOption(integer);
  await table.getByText('2 original observations', {exact:true}).click();
  const repeat = await table.locator('[data-source-evidence="' + ids.repeat_subject + '"]').textContent();
  const first = await table.locator('[data-source-evidence="' + ids.first + '"]').textContent();
  report.checks.push({name:'same material, same value, different times', status:repeat !== first ? 'PASS' : 'OBSERVATION', first, repeat});

  const addedId = 'evd_00000000-0000-4000-8000-000000000001';
  const appended = {...bundle, entities:[{...bundle.entities.find((record) => record.id === ids.first), id:addedId, value:31}]};
  await page.locator('#import-button').click();
  await page.locator('#import-format').selectOption('json');
  await page.locator('#import-text').fill(JSON.stringify(appended));
  await page.getByRole('button', {name: 'Validate & preview', exact: true}).click();
  await page.locator('#commit-import').click();
  await table.getByText('3 original observations', {exact:true}).waitFor();
  const selectedOption = await dropdown.inputValue();
  const currentRows = await table.getByRole('rowheader').count();
  report.checks.push({name:'comparison context persists after a same-context append changes representative', status:selectedOption === addedId && currentRows === 1 ? 'PASS' : 'FAIL',
    previous:integer, representative:addedId, selectedOption, currentRows});
  assert.deepEqual(report.errors, []);
  assert.deepEqual(report.external, []);
  report.status = report.checks.every((check) => check.status !== 'FAIL') ? 'PASS' : 'FAIL';
}

run().catch((error) => {report.status = 'FAIL'; report.exception = error.stack; console.error(error);}).finally(async () => {
  try { await browser?.close(); } finally {server.kill();}
  fs.writeFileSync(artifact('independent-edges.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({status:report.status, checks:report.checks, exception:report.exception}, null, 2));
  process.exitCode = report.status === 'PASS' ? 0 : 1;
});
