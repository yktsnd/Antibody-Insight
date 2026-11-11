/* Independent F27 / AC-J03, AC-J04, AC-J08 ordinary-input structural replay. */
const { chromium } = require('playwright');
const { spawn, spawnSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');

const root = path.resolve(__dirname, '..');
const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'awx-deposited-independent-'));
const snapshot = path.join(temp, 'snapshot');
const db = path.join(temp, 'public.sqlite3');
const python = process.env.PYTHON || path.join(root, '.venv', 'Scripts', 'python.exe');
const output = process.argv[2];
assert(output && !fs.existsSync(output), 'Supply a fresh evidence path');
for (const directory of ['workspace_app', 'web', 'fixtures/public']) {
  fs.cpSync(path.join(root, directory), path.join(snapshot, directory), {
    recursive: true, filter: (file) => !file.includes('__pycache__'),
  });
}
const digest = (bytes) => crypto.createHash('sha256').update(bytes).digest('hex');
function hashes(directory) {
  const files = ['workspace_app', 'web', 'fixtures/public'].flatMap((dir) =>
    fs.readdirSync(path.join(directory, dir), { recursive: true, withFileTypes: true })
      .filter((entry) => entry.isFile() && !entry.name.endsWith('.pyc'))
      .map((entry) => path.relative(directory, path.join(entry.parentPath || entry.path, entry.name)).replaceAll('\\', '/')));
  return Object.fromEntries(files.sort().map((file) => [file, digest(fs.readFileSync(path.join(directory, file)))]));
}
const source = hashes(snapshot);
const cif = path.join(snapshot, 'fixtures', 'public', '1MLC.cif');
const fasta = path.join(temp, 'D44.1.fasta');
const negativeCif = path.join(temp, 'adversarial-entity.cif');
const incompleteCif = path.join(temp, 'adversarial-alternate-and-gap.cif');
const prep = spawnSync(python, ['-c', `
import hashlib, json, sys
from pathlib import Path
import gemmi
cif, fasta, bad, incomplete = map(Path, sys.argv[1:])
raw = cif.read_bytes()
assert hashlib.sha256(raw).hexdigest() == '5536c79a3d73e09503f6a4d252bbca2dac5fa0e59b5424309f49cd0c34e8606e'
document = gemmi.cif.read_string(raw.decode('utf-8'))
block = document.sole_block()
sequences = {}
for row in block.find(['_entity_poly.pdbx_strand_id', '_entity_poly.pdbx_seq_one_letter_code_can']):
    for chain in row[0].split(','):
        sequences[chain] = ''.join(gemmi.cif.as_string(row[1]).split())
fasta.write_text('>1MLC author B D44.1 heavy\\n' + sequences['B'] + '\\n>1MLC author A D44.1 light\\n' + sequences['A'] + '\\n', encoding='utf-8')
scheme = [list(row) for row in block.find(['_pdbx_poly_seq_scheme.asym_id', '_pdbx_poly_seq_scheme.seq_id', '_pdbx_poly_seq_scheme.auth_seq_num', '_pdbx_poly_seq_scheme.mon_id']) if row[0] in ('A', 'B')]
atoms = block.find_mmcif_category('_atom_site.')
keys = {tag.split('.', 1)[1]: i for i, tag in enumerate(atoms.tags)}
def at(row, name): return row[keys[name]]
assert at(atoms[0], 'label_asym_id') == 'A' and at(atoms[0], 'label_seq_id') == '1'
original = at(atoms[0], 'label_entity_id')
atoms[0][keys['label_entity_id']] = '2'
document.write_file(str(bad))
atoms[0][keys['label_entity_id']] = original
atoms[0][keys['label_alt_id']] = 'A'
removed = [i for i, row in enumerate(atoms) if at(row, 'label_asym_id') == 'A' and at(row, 'label_seq_id') == '2']
assert removed
for i in reversed(removed):
    atoms.remove_row(i)
document.write_file(str(incomplete))
print(json.dumps({'sequences': {'H': sequences['B'], 'L': sequences['A']}, 'scheme': scheme}))
`, cif, fasta, negativeCif, incompleteCif], { cwd: snapshot, encoding: 'utf8', windowsHide: true });
assert.equal(prep.status, 0, prep.stderr);
const expected = JSON.parse(prep.stdout);
const results = [], errors = [], outbound = [];
let child, browser, context, page, origin, projectId, molecule, structure, stored, forgedOffset;

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

async function openBrowserPage() {
  context = await browser.newContext({ viewport: { width: 1540, height: 1050 } });
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
  assert.equal(response.status, 200);
  return response.data;
}

async function importFile(format, file) {
  await page.locator('#import-button').click();
  await page.locator('#import-format').selectOption(format);
  await page.locator('#import-file').setInputFiles(file);
  await page.waitForFunction(() => document.querySelector('#import-text').value.length > 0);
}

async function reviewFile() {
  await page.getByRole('button', { name: 'Validate & preview', exact: true }).click();
  await page.locator('#import-preview').waitFor({ state: 'visible' });
}

async function saveFile() {
  await page.locator('#commit-import').click();
  await page.locator('#import-dialog').waitFor({ state: 'hidden' });
  await page.locator('#candidate-count').filter({ hasText: '1' }).waitFor();
  await page.waitForFunction(() => !document.querySelector('#import-button').disabled && document.querySelector('#project-select').value);
}

async function viewer() {
  await page.waitForFunction((id) => !!StructureUI.contextFor(id)?.viewer, molecule.id);
}

async function assignEditor(asym, role, chain = '') {
  const row = page.locator('.map-chain-row').filter({ hasText: new RegExp(' / label ' + asym + ' / segment ') });
  await row.locator('[data-map-role]').selectOption(role);
  if (role === 'antibody') await row.locator('[data-map-chain]').selectOption(chain);
  if (role === 'antigen') {
    await row.locator('[data-target-namespace]').fill('PDB-entity');
    await row.locator('[data-target-identifier]').fill('1MLC:3');
  }
}

async function chooseCoordinates() {
  await page.locator('[data-edit-correspondence]').click();
  await assignEditor('A', 'antibody', 'L');
  await assignEditor('B', 'antibody', 'H');
  await assignEditor('E', 'antigen');
}

async function mappingDefinition(structureId) {
  const response = await api('/api/structure-view?project_id=' + projectId + '&structure_id=' + structureId);
  assert.equal(response.status, 200);
  const assignments = response.data.parsed.chains.filter((chain) => chain.model === 1).map((chain) => ({
    ...chain, role: ['A', 'B'].includes(chain.label_asym) ? 'antibody' : 'other',
    molecule_chain_id: { A: 'L', B: 'H' }[chain.label_asym] || null,
    target_ref: null, label: 'Independent explicit source assignment',
  }));
  return { project_id: projectId, definition: {
    structure_id: structureId, molecule_id: molecule.id, chain_assignments: assignments,
  } };
}

async function addAdversarialStructure(filename) {
  const content = fs.readFileSync(filename, 'utf8');
  const entity = { ...structure, id: 'stc_' + crypto.randomUUID(), name: path.basename(filename),
    content, sha256: digest(content), origin_kind: 'unknown',
    source: { name: 'Adversarial test derivative of the public coordinate file', version: null } };
  const response = await api('/api/import', { schema_version: stored.schema_version, project: stored.project, entities: [entity] });
  assert.equal(response.status, 200, JSON.stringify(response.data));
  return entity.id;
}

function write(status, error) {
  fs.writeFileSync(output, JSON.stringify({
    status, reviewer: '/root/deposited_mapping_review', timestamp: new Date().toISOString(),
    scope: 'Ordinary public FASTA and 1MLC mmCIF through persisted structural correspondence, browser selection, restart and transfer. Adversarial derivatives are engineering inputs.',
    source_sha256: source, observed: results, page_errors: errors, external_requests: outbound, error: error?.stack || null,
  }, null, 2));
}

(async () => {
  await start(db);
  browser = await chromium.launch({ headless: true, channel: process.env.PLAYWRIGHT_CHANNEL || 'chrome',
    args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  await openBrowserPage();
  await check('Register both real D44.1 chains through grouped FASTA with explicit identities', async () => {
    await importFile('fasta_grouped', fasta);
    await page.locator('#project-title').fill('Independent public D44.1 correspondence');
    await reviewFile();
    await page.locator('#group-molecular-format').fill('Fab');
    for (const [i, chain, role] of [[1, 'H', 'heavy'], [2, 'L', 'light']]) {
      await page.getByRole('textbox', { name: 'Candidate for record ' + i, exact: true }).fill('D44.1');
      await page.getByRole('textbox', { name: 'Chain ID for record ' + i, exact: true }).fill(chain);
      await page.getByRole('textbox', { name: 'Role for record ' + i, exact: true }).fill(role);
    }
    await page.locator('#apply-sequence-grouping').click();
    await saveFile();
    projectId = await page.locator('#project-select').inputValue();
    const registered = await bundle();
    assert.equal(registered.entities.length, 1);
    molecule = registered.entities[0];
    assert.deepEqual(Object.fromEntries(molecule.chains.map((chain) => [chain.id, chain.sequence])), expected.sequences);
  });
  await check('Import the deposited file against the explicit molecule and save the reviewed A/B mapping', async () => {
    await importFile('mmcif', cif);
    await page.locator('#structure-molecule').selectOption(molecule.id);
    await page.locator('#structure-origin').selectOption('experimental');
    await page.locator('#structure-source').fill('RCSB PDB 1MLC');
    await reviewFile();
    await saveFile();
    structure = (await bundle()).entities.find((entity) => entity.type === 'structure');
    assert.equal(structure.content, fs.readFileSync(cif, 'utf8'));
    await page.locator(`[data-select="${molecule.id}"]`).check();
    await page.locator('nav [data-screen="W"]').click();
    await viewer();
    await chooseCoordinates();
    await page.getByRole('button', { name: 'Use deposited polymer positions', exact: true }).click();
    await page.locator('#map-review').filter({ hasText: '432 mapped residues / 0 unavailable' }).waitFor();
    assert.equal((await bundle()).entities.filter((entity) => entity.type === 'structure_map').length, 0);
    await page.locator('[data-map-save]').click();
    await page.locator('#structure-map-dialog').waitFor({ state: 'hidden' });
    await viewer();
    stored = await bundle();
    const map = stored.entities.find((entity) => entity.type === 'structure_map');
    assert.equal(map.derivation, 'mmcif_polymer_sequence');
    assert.equal(map.source.version, 'sha256:' + structure.sha256);
    assert.equal(map.residues.length, expected.scheme.length);
    const scheme = new Map(expected.scheme.map(([asym, number, auth, monomer]) => [asym + ':' + number, [Number(auth), monomer]]));
    for (const entry of map.residues) {
      const source = entry.structure_residue;
      assert.equal(source.label_asym, entry.chain_id === 'L' ? 'A' : 'B');
      assert.equal(source.label_number, entry.sequence_index);
      assert.deepEqual([source.auth_number, source.residue_name], scheme.get(source.label_asym + ':' + source.label_number));
    }
  });
  await check('Select a sequence residue and physically click its deposited CA atom in Chrome', async () => {
    await page.locator('[data-structure-mode]').selectOption('calpha');
    await page.getByRole('combobox', { name: 'Chain for D44.1', exact: true }).selectOption('L');
    const residue = page.getByRole('button', { name: /^D44\.1 L sequence index 1 / });
    await residue.click();
    await viewer();
    await page.locator('.structure-selection').filter({ hasText: /Mapped L raw index 1.*label A:1/ }).waitFor();
    await page.locator('[data-focus-structure]').click();
    const other = page.getByRole('button', { name: /^D44[.]1 L sequence index 3 / });
    await other.click();
    await viewer();
    await page.locator('.structure-selection').filter({ hasText: /Mapped L raw index 3.*label A:3/ }).waitFor();
    await page.locator('.coordinate-canvas').scrollIntoViewIfNeeded();
    const point = await page.evaluate((id) => {
      const context = StructureUI.contextFor(id);
      const atom = context.data.parsed.atoms.find((value) => value.label_asym === 'A' && value.label_number === 1 && value.atom_name === 'CA');
      const rendered = context.viewer.selectedAtoms({ serial: atom.index + 1 })[0];
      const screen = context.viewer.modelToScreen(rendered);
      return { x: screen.x - window.scrollX, y: screen.y - window.scrollY };
    }, molecule.id);
    await page.mouse.click(point.x, point.y);
    await viewer();
    await page.locator('.structure-selection').filter({ hasText: /Mapped L raw index 1.*label A:1/ }).waitFor();
    assert.match(await residue.getAttribute('class'), /\bactive\b/);
    await page.screenshot({ path: output.replace(/\.json$/, '-public-1MLC.png') });
  });
  await check('Save a proposed experiment with the actual public source residue and map', async () => {
    const map = stored.entities.find((entity) => entity.type === 'structure_map');
    await page.locator('nav [data-screen="R"]').click();
    await page.getByRole('button', { name: 'Record research hypothesis', exact: true }).click();
    await page.locator('#hypothesis-text').fill('A change at the observed D44.1 light-chain position could affect antigen recognition.');
    await page.locator('#hypothesis-question').fill('Compare an explicitly prepared substitution with the parent Fab under matched binding assay conditions.');
    await page.locator('#hypothesis-limitations').fill('The deposited structure establishes coordinate context. The effect of a substitution remains unmeasured.');
    await page.getByRole('button', { name: 'Review hypothesis before saving', exact: true }).click();
    await page.locator('#design-preview-dialog').waitFor();
    await page.getByRole('button', { name: 'Save reviewed records', exact: true }).click();
    await page.locator('.saved-hypothesis').waitFor();
    stored = await bundle();
    const hypothesis = stored.entities.find((entity) => entity.type === 'hypothesis');
    assert.equal(hypothesis.status, 'proposed');
    assert.deepEqual(hypothesis.residue_refs, [{ molecule_id: molecule.id, chain_id: 'L', sequence_index: 1 }]);
    assert.equal(hypothesis.structure_refs.length, 1);
    const observation = hypothesis.structure_refs[0];
    assert.equal(observation.structure_id, structure.id);
    assert.equal(observation.structure_map_id, map.id);
    assert.equal(observation.model, 1);
    assert.deepEqual(observation.residue.source_key, map.residues.find((entry) => entry.chain_id === 'L' && entry.sequence_index === 1).structure_residue);
    assert.equal(stored.entities.some((entity) => entity.type === 'evidence'), false);
    await page.locator('nav [data-screen="W"]').click();
    await viewer();
  });
  await check('Reject an order-consistent same-AA offset forged as a deposited mapping', async () => {
    const map = structuredClone(stored.entities.find((entity) => entity.type === 'structure_map'));
    const target = molecule.chains.find((chain) => chain.id === 'L').sequence;
    const i = [...target].findIndex((aa, index) => aa === target[index + 1]);
    assert(i >= 0);
    const first = map.residues.find((entry) => entry.chain_id === 'L' && entry.sequence_index === i + 1);
    const second = map.residues.find((entry) => entry.chain_id === 'L' && entry.sequence_index === i + 2);
    first.structure_residue = second.structure_residue;
    second.status = 'unavailable';
    second.structure_residue = null;
    second.reason = 'Adversarial omission';
    map.id = 'smp_' + crypto.randomUUID();
    const append = { schema_version: stored.schema_version, project: stored.project, entities: [map] };
    const forged = await api('/api/import', append);
    assert.equal(forged.status, 422);
    assert.match(forged.data.error, /differs from the retained coordinate source/);
    assert.deepEqual(await bundle(), stored);
    forgedOffset = map;
  });
  await check('Classify a map with the copied source name as declared when it lacks typed derivation', async () => {
    const manual = structuredClone(forgedOffset);
    delete manual.derivation;
    const derived = stored.entities.find((entity) => entity.type === 'structure_map');
    assert.equal(manual.source.name, derived.source.name);
    const imported = await api('/api/import', { schema_version: stored.schema_version, project: stored.project, entities: [manual] });
    assert.equal(imported.status, 200, JSON.stringify(imported.data));
    await page.reload();
    await viewer();
    const choices = page.locator('[data-coordinate-map]');
    assert.match(await choices.locator(`option[value="${derived.id}"]`).textContent(), /^Deposited polymer positions /);
    assert.match(await choices.locator(`option[value="${manual.id}"]`).textContent(), /^Declared correspondence /);
    assert.equal(await choices.inputValue(), derived.id);
    stored = await bundle();
  });
  await check('Discard a delayed deposited preview when its editor has closed', async () => {
    const routePattern = '**/api/deposited-correspondence-preview';
    let captured, release, delivered;
    const waiting = new Promise((resolve) => { captured = resolve; });
    const gate = new Promise((resolve) => { release = resolve; });
    const delivery = new Promise((resolve) => { delivered = resolve; });
    await page.route(routePattern, async (route) => {
      const response = await route.fetch();
      captured();
      await gate;
      await route.fulfill({ response });
      delivered();
    });
    await chooseCoordinates();
    await page.getByRole('button', { name: 'Use deposited polymer positions', exact: true }).click();
    await waiting;
    await page.keyboard.press('Escape');
    await page.locator('#structure-map-dialog').waitFor({ state: 'hidden' });
    await chooseCoordinates();
    release();
    await delivery;
    await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    await page.unroute(routePattern);
    assert.equal(await page.locator('#map-edit-fields').isVisible(), true);
    assert.equal(await page.locator('[data-map-save]').count(), 0);
    assert.deepEqual(await bundle(), stored);
    await page.keyboard.press('Escape');
  });
  await check('Reject a coordinate entity mismatch without changing the persisted project', async () => {
    const structureId = await addAdversarialStructure(negativeCif);
    const before = await bundle();
    const response = await api('/api/deposited-correspondence-preview', await mappingDefinition(structureId));
    assert.equal(response.status, 422);
    assert.match(response.data.error, /Coordinate label entity differs/);
    assert.deepEqual(await bundle(), before);
  });
  await check('Expose an explicit alternate and missing coordinate as unavailable', async () => {
    const structureId = await addAdversarialStructure(incompleteCif);
    const response = await api('/api/deposited-correspondence-preview', await mappingDefinition(structureId));
    assert.equal(response.status, 200, JSON.stringify(response.data));
    const residues = response.data.entities[0].residues;
    const first = residues.find((entry) => entry.chain_id === 'L' && entry.sequence_index === 1);
    const second = residues.find((entry) => entry.chain_id === 'L' && entry.sequence_index === 2);
    assert.equal(first.status, 'unavailable');
    assert.match(first.reason, /explicit alternate conformer/);
    assert.equal(first.structure_residue, null);
    assert.equal(second.status, 'unavailable');
    assert.match(second.reason, /No coordinates/);
    assert.equal(second.structure_residue, null);
    assert.equal(residues.filter((entry) => entry.status === 'mapped').length, 430);
  });
  await check('Reopen the saved map after server restart and reproduce the project in a fresh store', async () => {
    const persisted = await bundle();
    const port = Number(new URL(origin).port);
    await stop();
    await start(db, port);
    await page.reload();
    await page.locator('[data-coordinate-choice]').waitFor();
    assert.equal(await page.locator('[data-coordinate-choice]').inputValue(), '');
    await page.locator('[data-coordinate-choice]').selectOption(structure.id);
    await viewer();
    assert.match(await page.locator('.structure-selection').textContent(), /Mapped L raw index 1.*label A:1/);
    assert.deepEqual(await bundle(), persisted);
    const download = page.waitForEvent('download');
    await page.locator('#export-button').click();
    const file = path.join(temp, 'exported-public-project.json');
    await (await download).saveAs(file);
    await stop();
    await context.close();
    await start(path.join(temp, 'fresh.sqlite3'), port);
    await openBrowserPage();
    await importFile('json', file);
    await reviewFile();
    await saveFile();
    assert.deepEqual(await bundle(), persisted);
  });
  assert.deepEqual(outbound, []);
  assert.deepEqual(errors, []);
  assert.deepEqual(hashes(snapshot), source);
  write('PASS');
})().catch((error) => {
  console.error(error);
  write('FAIL', error);
  process.exitCode = 1;
}).finally(async () => {
  await browser?.close();
  await stop();
});
