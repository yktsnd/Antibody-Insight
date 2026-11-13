const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {spawn} = require('node:child_process');
const {chromium} = require('playwright');

const evidence = __dirname;
const localSnapshot = path.join(evidence, 'snapshot');
const root = process.env.AWX_REVIEW_SNAPSHOT || (fs.existsSync(localSnapshot) ? localSnapshot : path.join(evidence, '..', 'snapshot'));
const output = path.join(evidence, 'independent-j08-edge-results.json');
const database = path.join(evidence, 'j08-edge.sqlite3');
const results = [];
const outbound = [];
const pageErrors = [];
const previewRequests = [];
const oldPayload = '>CLOSED-OLD\r\nACDEFG\r\n';
const groupedPayload = '>A-RECORD\r\nACDEFG\r\n>B-RECORD\r\nGHIKLM\r\n';
const recoveredPayload = '>RECOVERED\nACDEFG\n';
let browser;

const server = spawn(process.env.PYTHON, ['-m','workspace_app.server','--database',database,'--port','0'], {
  cwd: root, windowsHide:true, stdio:['ignore','pipe','pipe']
});

async function start() {
  return new Promise((resolve,reject) => {
    let log = '';
    const timer = setTimeout(() => reject(new Error('Server timeout ' + log)), 15000);
    server.stdout.on('data', chunk => {
      log += chunk;
      const url = log.match(/http:\/\/127\.0\.0\.1:\d+/);
      if (url) { clearTimeout(timer); resolve(url[0]); }
    });
    server.stderr.on('data', chunk => {log += chunk;});
    server.once('exit', code => {clearTimeout(timer); reject(new Error('Server exit ' + code + ' ' + log));});
  });
}

async function check(name, operation) {
  const before = Date.now();
  try {
    const evidence = await operation();
    results.push({name, status:'PASS', duration_ms:Date.now() - before, evidence});
  } catch (error) {
    results.push({name, status:'FAIL', duration_ms:Date.now() - before, error:String(error)});
    throw error;
  }
}

async function run() {
  const origin = await start();
  browser = await chromium.launch({headless:true, channel:'chrome'});
  const context = await browser.newContext();
  await context.route('**/*', async route => {
    const req = route.request();
    if (!req.url().startsWith(origin + '/')) {
      outbound.push(req.url());
      await route.abort();
      return;
    }
    if (req.method() === 'POST' && req.url() === origin + '/api/preview') {
      previewRequests.push(req.postDataJSON());
    }
    await route.continue();
  });
  await context.addInitScript(() => {
    const original = File.prototype.arrayBuffer;
    window.readGates = new Map();
    File.prototype.arrayBuffer = function () {
      if (!this.name.startsWith('gated-')) return original.call(this);
      return new Promise(resolve => {
        window.readGates.set(this.name, () => {
          window.readGates.delete(this.name);
          resolve(original.call(this));
        });
      });
    };
  });
  const page = await context.newPage();
  page.on('pageerror', error => pageErrors.push(error.message));
  await page.goto(origin);
  await page.waitForFunction(() => !document.querySelector('#project-select').disabled);
  const dialog = page.locator('#import-dialog');
  const input = page.locator('#import-file');
  const text = page.locator('#import-text');
  const format = page.locator('#import-format');
  const preview = page.locator('#import-preview');
  const projects = () => page.evaluate(async () => await (await fetch('/api/bootstrap')).json());
  const baseline = await projects();
  const open = () => page.getByRole('button', {name:'Import data', exact:true}).click();
  const submit = () => page.getByRole('button', {name:'Validate & preview', exact:true}).click();
  async function close() {
    await page.keyboard.press('Escape');
    await dialog.waitFor({state:'hidden'});
  }
  async function choose(name, payload, gated = true) {
    await input.setInputFiles({name, mimeType:'text/plain', buffer:Buffer.from(payload)});
    if (gated) await page.waitForFunction(filename => window.readGates.has(filename), name);
  }
  async function release(name) {
    await page.evaluate(async filename => {
      window.readGates.get(filename)();
      await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
    }, name);
  }
  async function expectNoNewPreview(count) {
    assert.equal(await preview.isHidden(), true);
    assert.equal(previewRequests.length, count);
  }

  await check('independent_j08_close_reopen_blocks_old_read_and_submit', async () => {
    await open();
    await choose('gated-closed.fasta', oldPayload);
    await submit();
    await expectNoNewPreview(0);
    await close();
    await open();
    assert.equal(await input.evaluate(el => el.files.length), 0);
    await choose('gated-reopened.fasta', '>REOPENED\r\nIKLMNP\r\n');
    await submit();
    await release('gated-closed.fasta');
    await expectNoNewPreview(0);
    assert.equal(await text.inputValue(), '');
    await release('gated-reopened.fasta');
    await preview.waitFor({state:'visible'});
    assert.equal(previewRequests.length, 1);
    assert.equal(previewRequests[0].filename, 'gated-reopened.fasta');
    assert.match(await preview.textContent(), /REOPENED/);
    assert.doesNotMatch(await preview.textContent(), /CLOSED-OLD/);
    await close();
    assert.deepEqual(await projects(), baseline);
    return 'A queued preview from a closed import produced no request. The reopened dialog previewed only the new filename and record. Cancel preserved the store.';
  });

  await check('independent_j08_explicit_format_while_read_pending', async () => {
    await open();
    await format.selectOption('fasta');
    await choose('gated-format.fasta', groupedPayload);
    assert.equal(await format.inputValue(), 'fasta');
    await format.selectOption('fasta_grouped');
    await page.locator('#project-title').fill('Independent grouped preview');
    await submit();
    await expectNoNewPreview(1);
    await release('gated-format.fasta');
    await preview.waitFor({state:'visible'});
    assert.equal(previewRequests.length, 2);
    assert.equal(previewRequests[1].format, 'fasta_grouped');
    assert.equal(previewRequests[1].filename, 'gated-format.fasta');
    assert.equal(previewRequests[1].text, groupedPayload);
    assert.equal(previewRequests[1].title, 'Independent grouped preview');
    assert.match(await preview.textContent(), /Declare which chains belong to each candidate/);
    assert.match(await preview.textContent(), /A-RECORD/);
    assert.match(await preview.textContent(), /B-RECORD/);
    await close();
    assert.deepEqual(await projects(), baseline);
    return 'User-selected grouped FASTA took precedence over automatic extension selection. Both source records and the original CRLF bytes reached the grouped preview; cancellation preserved the store.';
  });

  await check('independent_j08_replaced_invalid_utf8_cannot_report_stale_error', async () => {
    await open();
    await format.selectOption('fasta');
    await choose('gated-invalid.fasta', Buffer.from([0xff, 0xfe, 0xfe]));
    await choose('recovery.fasta', recoveredPayload, false);
    await page.waitForFunction(value => document.querySelector('#import-text').value === value, recoveredPayload);
    await submit();
    await preview.waitFor({state:'visible'});
    await release('gated-invalid.fasta');
    assert.equal(previewRequests.length, 3);
    assert.equal(previewRequests[2].filename, 'recovery.fasta');
    assert.match(await preview.textContent(), /RECOVERED/);
    assert.equal(await page.locator('#notification.error').count(), 0);
    assert.equal(await page.locator('#import-dialog > .dialog-error').count(), 0);
    await close();
    assert.deepEqual(await projects(), baseline);
    return 'Late decode failure from the replaced file left the newer preview and status untouched and produced no writes.';
  });

  assert.deepEqual(outbound, []);
  assert.deepEqual(pageErrors, []);
}

run().then(() => 'PASS').catch(error => {
  console.error(error);
  process.exitCode = 1;
  return 'FAIL';
}).then(async status => {
  fs.writeFileSync(output, JSON.stringify({status, reviewer:'/root/import_review', timestamp:new Date().toISOString(),
    commit:'cd3a6d70ca7a999e8279187edfcae9fe3bfdd108', results, outbound, pageErrors}, null, 2));
  console.log(status, JSON.stringify(results), output);
  if (browser) await browser.close();
  server.kill();
});
