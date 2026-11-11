/* Independent public 1MLC FASTA/mmCIF/ANARCI file replay. */
const { chromium } = require('playwright');
const { spawn, spawnSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');

const root = path.resolve(__dirname, '..');
const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'awx-numbering-review-'));
const snapshot = path.join(temp, 'snapshot');
const db = path.join(temp, 'research.sqlite3');
const python = process.env.PYTHON || path.join(root, '.venv', 'Scripts', 'python.exe');
const output = process.argv[2];
assert(output && !fs.existsSync(output), 'Supply a fresh evidence path');
const directories = ['workspace_app', 'web', 'fixtures/public'];
for (const directory of directories) {
  fs.cpSync(path.join(root, directory), path.join(snapshot, directory), {
    recursive: true, filter: (file) => !file.includes('__pycache__'),
  });
}
const digest = (bytes) => crypto.createHash('sha256').update(bytes).digest('hex');
function hashes() {
  const files = directories.flatMap((dir) =>
    fs.readdirSync(path.join(snapshot, dir), { recursive: true, withFileTypes: true })
      .filter((entry) => entry.isFile() && !entry.name.endsWith('.pyc'))
      .map((entry) => path.relative(snapshot, path.join(entry.parentPath || entry.path, entry.name)).replaceAll('\\', '/')));
  return Object.fromEntries(files.sort().map((file) => [file, digest(fs.readFileSync(path.join(snapshot, file)))]));
}
const source = hashes();
const cif = path.join(snapshot, 'fixtures', 'public', '1MLC.cif');
const anarciFile = path.join(snapshot, 'fixtures', 'public', '1MLC-AB.anarci.txt');
const fasta = path.join(temp, 'D44.1.fasta');
const sourceBytes = fs.readFileSync(anarciFile);
const sourceHash = digest(sourceBytes);
assert.equal(sourceHash, '26c2c44b388d7f62dd9efdf992a1c69f366f07cc0db1b43001e32c175c3e0747');
const sourceText = sourceBytes.toString('utf8');
const prep = spawnSync(python, ['-c', `
import json, sys
from pathlib import Path
import gemmi
cif, fasta = map(Path, sys.argv[1:])
block = gemmi.cif.read_file(str(cif)).sole_block()
sequences = {}
for row in block.find(['_entity_poly.pdbx_strand_id', '_entity_poly.pdbx_seq_one_letter_code_can']):
    for chain in row[0].split(','):
        sequences[chain] = ''.join(gemmi.cif.as_string(row[1]).split())
selected = {'L': sequences['A'], 'H': sequences['B']}
fasta.write_text(''.join(f'>1MLC-{chain}\\n{sequence}\\n' for chain, sequence in selected.items()), encoding='utf-8')
print(json.dumps(selected))
`, cif, fasta], { cwd: snapshot, encoding: 'utf8', windowsHide: true });
assert.equal(prep.status, 0, prep.stderr);
const sequences = JSON.parse(prep.stdout);
const expected = sourceText.trim().split('//').filter((record) => record.trim()).map((record) => {
  const positions = record.split(/\r?\n/).map((line) => line.trim().split(/\s+/)).filter((parts) => ['H', 'L'].includes(parts[0]));
  assert(positions.every((parts) => parts.length === 3));
  return positions.filter((parts) => parts[2] !== '-').map((parts, index) => ({
    sequence_index: index + 1, aa: parts[2], number: Number(parts[1]), ins_code: '',
  }));
});
assert.deepEqual(expected.map((rows) => rows.length), [107, 116]);
const results = [], errors = [], outbound = [];
let child, browser, context, page, origin, projectId, molecule, stored;

async function check(name, run) {
  await run();
  results.push({ name, status: 'PASS' });
  console.log('PASS', name);
}

async function start(database, port = 0) {
  child = spawn(python, ['-m', 'workspace_app.server', '--database', database, '--port', String(port)],
    { cwd: snapshot, windowsHide: true, stdio: ['ignore', 'pipe', 'pipe'] });
  origin = await new Promise((resolve, reject) => {
    let log = '';
    const timer = setTimeout(() => reject(Error('Server startup ' + log)), 15000);
    child.stdout.on('data', (chunk) => {
      log += chunk;
      const match = log.match(/http:\/\/127\.0\.0\.1:\d+/);
      if (match) { clearTimeout(timer); resolve(match[0]); }
    });
    child.stderr.on('data', (chunk) => { log += chunk; });
    child.on('exit', (code) => { clearTimeout(timer); reject(Error('Server exit ' + code + ' ' + log)); });
  });
}

async function stop() {
  if (child && child.exitCode === null) {
    await new Promise((resolve) => { child.once('exit', resolve); child.kill(); });
  }
}

async function openPage() {
  context = await browser.newContext({ viewport: { width: 1500, height: 1050 } });
  await context.route('**/*', async (route) => {
    if (!route.request().url().startsWith(origin + '/')) {
      outbound.push(route.request().url());
      await route.abort();
    } else await route.continue();
  });
  page = await context.newPage();
  page.on('pageerror', (error) => errors.push(error.message));
  await page.goto(origin);
  await page.waitForFunction(() => !document.querySelector('#import-button').disabled);
}

async function api(route, data) {
  return page.evaluate(async ({ route, data }) => {
    const boot = await (await fetch('/api/bootstrap')).json();
    const response = await fetch(route, data === undefined ? {} : {
      method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': boot.csrf }, body: JSON.stringify(data),
    });
    return { status: response.status, data: await response.json() };
  }, { route, data });
}

async function bundle() {
  const response = await api('/api/bundle?project_id=' + projectId);
  assert.equal(response.status, 200, JSON.stringify(response.data));
  return response.data;
}

async function importFile(format, file) {
  await page.locator('#import-button').click();
  await page.locator('#import-format').selectOption(format);
  await page.locator('#import-file').setInputFiles(file);
  await page.waitForFunction(() => document.querySelector('#import-text').value.length > 0);
}

async function review() {
  await page.getByRole('button', { name: 'Validate & preview', exact: true }).click();
  await page.locator('#import-preview').waitFor({ state: 'visible' });
}

async function save(count) {
  const response = page.waitForResponse((res) => res.url().endsWith('/api/import') && res.request().method() === 'POST');
  await page.locator('#commit-import').click();
  assert.equal((await response).status(), 200);
  await page.locator('#import-dialog').waitFor({ state: 'hidden' });
  await page.locator('#notification').filter({ hasText: `Saved ${count} entities` }).waitFor();
}

async function nav(screen) {
  await page.locator(`nav [data-screen="${screen}"]`).click();
}

function write(status, error) {
  fs.writeFileSync(output, JSON.stringify({
    status, reviewer: '/root/deposited_mapping_review', timestamp: new Date().toISOString(),
    scope: 'Ordinary files from public 1MLC through actual browser correspondence and native numbering. No original assay or human numbering review is supplied.',
    source_sha256: source, results, page_errors: errors, external_requests: outbound, error: error?.stack || null,
  }, null, 2));
}

(async () => {
  await start(db);
  browser = await chromium.launch({ headless: true, channel: process.env.PLAYWRIGHT_CHANNEL || 'chrome',
    args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  await openPage();
  await check('Register actual public FASTA and coordinates through ordinary file inputs', async () => {
    await importFile('fasta_grouped', fasta);
    await page.locator('#project-title').fill('Independent 1MLC numbered domains');
    await review();
    await page.locator('#group-molecular-format').fill('Fab');
    for (const [i, chain, role] of [[1, 'L', 'light'], [2, 'H', 'heavy']]) {
      await page.getByRole('textbox', { name: 'Candidate for record ' + i, exact: true }).fill('D44.1');
      await page.getByRole('textbox', { name: 'Chain ID for record ' + i, exact: true }).fill(chain);
      await page.getByRole('textbox', { name: 'Role for record ' + i, exact: true }).fill(role);
    }
    await page.locator('#apply-sequence-grouping').click();
    await save(1);
    projectId = await page.locator('#project-select').inputValue();
    molecule = (await bundle()).entities.find((entity) => entity.type === 'molecule');
    assert.deepEqual(Object.fromEntries(molecule.chains.map((chain) => [chain.id, chain.sequence])), sequences);
    await importFile('mmcif', cif);
    await page.locator('#structure-molecule').selectOption(molecule.id);
    await page.locator('#structure-origin').selectOption('experimental');
    await review();
    await save(1);
    await page.locator(`[data-select="${molecule.id}"]`).check();
    await nav('W');
    await page.locator('[data-edit-correspondence]').click();
    for (const [label, chain] of [['A', 'L'], ['B', 'H']]) {
      const row = page.locator('.map-chain-row').filter({ hasText: new RegExp(' / label ' + label + ' / segment ') });
      await row.locator('[data-map-role]').selectOption('antibody');
      await row.locator('[data-map-chain]').selectOption(chain);
    }
    await page.locator('[data-map-from-polymer]').click();
    await page.locator('#map-review').filter({ hasText: '432 mapped residues' }).waitFor();
    await page.locator('[data-map-save]').click();
    await page.locator('#notification').filter({ hasText: 'Saved correspondence' }).waitFor();
    assert.equal((await bundle()).entities.filter((entity) => entity.type === 'structure_map').length, 1);
  });
  await check('Preview explicit ANARCI target bindings and reject wrong chains and incomplete attestation', async () => {
    const before = await bundle();
    await importFile('anarci_text', anarciFile);
    await page.locator('#numbering-tool-version').fill('2026.2.13.2');
    await review();
    const rows = page.locator('#numbering-binding-panel tbody tr');
    assert.equal(await rows.count(), 2);
    assert.match(await rows.nth(0).textContent(), /1MLC-A.*K.*1–107/s);
    assert.match(await rows.nth(1).textContent(), /1MLC-B.*H.*1–116/s);
    assert.equal(await page.locator('#commit-import').isDisabled(), true);
    const light = page.getByRole('combobox', { name: 'Target for record 1 domain 1', exact: true });
    const heavy = page.getByRole('combobox', { name: 'Target for record 2 domain 1', exact: true });
    const list = await page.locator('#numbering-target-chains option').evaluateAll((options) => options.map((option) => option.value));
    const lightTarget = list.find((value) => value.includes(' / L '));
    const heavyTarget = list.find((value) => value.includes(' / H '));
    assert(lightTarget && heavyTarget);
    await light.fill(heavyTarget);
    await page.locator('#apply-numbering-bindings').click();
    await page.locator('#import-dialog .dialog-error').filter({ hasText: 'Numbered amino acid differs' }).waitFor();
    assert.deepEqual(await bundle(), before);
    await light.fill(lightTarget);
    await heavy.fill(heavyTarget);
    await page.getByText('Record an existing scientific review', { exact: true }).click();
    await page.locator('#numbering-reviewed').check();
    await page.locator('#apply-numbering-bindings').click();
    await page.locator('#import-dialog .dialog-error').filter({ hasText: 'verification.reference' }).waitFor();
    assert.deepEqual(await bundle(), before);
    await page.locator('#numbering-reviewed').uncheck();
    await page.locator('#apply-numbering-bindings').click();
    await page.getByRole('heading', { name: 'Review numbering assignments', exact: true }).waitFor();
    assert.equal((await page.locator('#import-preview tbody tr').allTextContents()).filter((row) => row.includes('unverified')).length, 2);
    assert.deepEqual(await bundle(), before);
    await save(3);
    stored = await bundle();
  });
  await check('Retain exact ANARCI maps and file bytes, show independent raw, IMGT and deposited positions in W', async () => {
    const native = stored.entities.find((entity) => entity.type === 'numbering_file');
    assert.equal(native.sha256, sourceHash);
    assert.equal(native.content, sourceText);
    const maps = stored.entities.filter((entity) => entity.type === 'residue_map');
    assert.equal(maps.length, 2);
    for (const [i, chain, type] of [[0, 'L', 'light'], [1, 'H', 'heavy']]) {
      const record = maps.find((map) => map.chain_id === chain);
      assert.equal(record.chain_type, type);
      assert.deepEqual(record.entries, expected[i]);
      assert.deepEqual(record.numbering_origin, { file_id: native.id, record_index: i, domain_index: 1 });
      assert.deepEqual(record.verification, { status: 'unverified', reviewer: null, reference: null, reviewed_at: null });
      assert.deepEqual(native.allocations.find((allocation) => allocation.map_id === record.id).binding, {
        record_index: i, domain_index: 1, molecule_id: molecule.id, chain_id: chain, verification: record.verification,
      });
    }
    await nav('W');
    await page.getByRole('combobox', { name: 'Chain for D44.1', exact: true }).selectOption('L');
    const map = maps.find((record) => record.chain_id === 'L');
    await page.getByRole('combobox', { name: 'Numbering map for D44.1 L', exact: true }).selectOption(map.id);
    const selected = expected[0].find((entry) => entry.sequence_index !== entry.number);
    assert(selected);
    await page.getByRole('button', { name: `D44.1 L sequence index ${selected.sequence_index} ${selected.aa}`, exact: true }).click();
    await page.locator('.sequence-details').filter({ hasText: new RegExp('Selected raw index ' + selected.sequence_index + '.*IMGT ' + selected.number) }).waitFor();
    await page.locator('.structure-selection').filter({ hasText: new RegExp('Mapped L raw index ' + selected.sequence_index + '.*label A:' + selected.sequence_index) }).waitFor();
    await page.getByText('Numbering source, definition and verification', { exact: true }).click();
    const download = page.waitForEvent('download');
    await page.getByRole('button', { name: 'Download original ANARCI output', exact: true }).click();
    const downloaded = path.join(temp, 'original-ANARCI.txt');
    await (await download).saveAs(downloaded);
    assert.deepEqual(fs.readFileSync(downloaded), sourceBytes);
    await page.screenshot({ path: output.replace(/\.json$/, '-numbering-observation.png') });
  });
  await check('Unverified numbering stays unavailable for source-numbered design in W and D', async () => {
    await page.getByRole('button', { name: 'Design a substitution at the selected residue', exact: true }).click();
    await page.locator('#notification').filter({ hasText: 'Choose an eligible source map covering this residue' }).waitFor();
    assert.equal(await page.locator('nav [data-screen="W"]').getAttribute('aria-current'), 'page');
    await nav('D');
    await page.locator('#design-map').waitFor();
    for (const map of stored.entities.filter((entity) => entity.type === 'residue_map')) {
      const option = page.locator(`#design-map option[value="${map.id}"]`);
      assert.equal(await option.evaluate((element) => element.disabled), true);
      const response = await api('/api/design-context', {
        project_id: projectId, parent_id: molecule.id, map_id: map.id, reference_map_id: null,
      });
      assert.equal(response.status, 422);
      assert.match(response.data.error, /unverified/);
    }
    assert.match(await page.locator('#design-coordinate-context').textContent(), /unverified maps cannot authorize substitutions/);
    assert.equal((await bundle()).entities.some((entity) => entity.type === 'lineage'), false);
  });
  await check('Preserve duplicate source record labels with distinct ordinal bindings and expose a failed record', async () => {
    const text = sourceText.replace('# 1MLC-B', '# 1MLC-A') + '# no HMM hit\n//\n';
    assert.notEqual(text, sourceText);
    const read = await api('/api/numbering-file-preview', { project_id: projectId, text, filename: 'adversarial-names.anarci.txt',
      version: null, bindings: [], bindings_text_sha256: null });
    assert.equal(read.status, 200, JSON.stringify(read.data));
    assert.deepEqual(read.data.report.numbering_domains.map(({ record_name, record_index }) => [record_name, record_index]), [['1MLC-A', 0], ['1MLC-A', 1]]);
    assert.equal(read.data.report.excluded[0].reason, 'No numbering returned');
    const original = stored.entities.find((entity) => entity.type === 'numbering_file');
    const bindings = original.allocations.map((allocation) => allocation.binding);
    const mapped = await api('/api/numbering-file-preview', { project_id: projectId, text, filename: 'adversarial-names.anarci.txt',
      version: null, bindings, bindings_text_sha256: read.data.report.text_sha256 });
    assert.equal(mapped.status, 200, JSON.stringify(mapped.data));
    assert.deepEqual(mapped.data.bundle.entities.filter((entity) => entity.type === 'residue_map').map((map) => [map.chain_id, map.numbering_origin.record_index]),
      [['L', 0], ['H', 1]]);
    assert.deepEqual(await bundle(), stored);
  });
  await check('Verify exact source, target maps and coordinates across restart and fresh project reimport', async () => {
    const port = Number(new URL(origin).port);
    await stop();
    await start(db, port);
    await page.reload();
    await page.waitForFunction(() => !document.querySelector('#export-button').disabled);
    assert.deepEqual(await bundle(), stored);
    const download = page.waitForEvent('download');
    await page.locator('#export-button').click();
    const file = path.join(temp, 'whole-public-project.json');
    await (await download).saveAs(file);
    await stop();
    await context.close();
    await start(path.join(temp, 'fresh.sqlite3'), port);
    await openPage();
    await importFile('json', file);
    await review();
    await save(stored.entities.length);
    assert.deepEqual(await bundle(), stored);
  });
  assert.deepEqual(outbound, []);
  assert.deepEqual(errors, []);
  assert.deepEqual(hashes(), source);
  write('PASS');
})().catch((error) => {
  console.error(error);
  write('FAIL', error);
  process.exitCode = 1;
}).finally(async () => {
  await browser?.close();
  await stop();
});
