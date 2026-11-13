const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { spawn } = require('node:child_process');
const { createHash } = require('node:crypto');
const { chromium } = require('playwright');

const review = __dirname;
const snapshot = path.join(review, 'snapshot');
const file = path.join(review, 'browser', 'retained-export.json');
const source = fs.readFileSync(path.join(snapshot, 'validation', 'public', 'emicizumab-gsrs.json'));
const exported = JSON.parse(fs.readFileSync(file));
const records = exported.entities;
const get = (external) => records.find((record) => record.external_id === external);
const reference = get('EMI-DECLARED');
const alternative = get('EMI-REVIEW-ALT');
const publicMolecule = get('EMI-GSRS');
const units = records.filter((record) => record.type === 'binding_unit');
const lineage = records.find((record) => record.type === 'lineage');
const hypothesis = records.find((record) => record.type === 'hypothesis');
const sha = createHash('sha256').update(source).digest('hex');
const registry = JSON.parse(source);
const names = { 1: 'Q', 2: 'J', 3: 'L1', 4: 'L2' };
const subunits = Object.fromEntries(registry.protein.subunits.map((row) => [row.subunitIndex, row]));
const originalLinks = registry.protein._disulfideLinks.shorthand.split(';').map((bond) => bond.split('->').map((site) => site.split('_').map(Number)));
const bondPairs = originalLinks.filter(([a, b]) => a[0] !== b[0]).map((bond) => bond.map(([n, residue]) => {
  assert.equal(subunits[n].sequence[residue - 1], 'C');
  return { chain: names[n], residue };
}));
const unordered = (pair) => pair.slice().sort().join('/');
const projected = [...new Set(bondPairs.map((bond) => unordered(bond.map((site) => site.chain))))].sort();
const chains = Object.keys(names).map((n) => {
  const sourceChain = subunits[n];
  const name = names[n];
  const publicChain = publicMolecule.chains.find((chain) => chain.id === name);
  const graphChain = reference.component_graph.chains.find((chain) => chain.chain_id === name);
  assert.equal(graphChain.copies, 1);
  assert.equal(graphChain.components.length, 1);
  const { origin, sequence } = graphChain.components[0];
  const unit = units.find(({id}) => origin.binding_unit_id === id);
  const unitChain = unit.chains.find(({id}) => id === name);
  assert.deepEqual(origin, { binding_unit_id: unit.id, chain_id: name, start: 1, end: sourceChain.sequence.length });
  assert.deepEqual(unitChain.origin, { molecule_id: publicMolecule.id, chain_id: name, start: 1, end: sourceChain.sequence.length });
  assert.ok(unit.source.name.includes(registry.approvalID));
  assert.ok(unit.source.version.includes(sha));
  assert.equal(publicChain.sequence, sourceChain.sequence);
  assert.equal(sequence, sourceChain.sequence);
  assert.equal(unitChain.sequence, sourceChain.sequence);
  assert.equal(reference.chains.find((chain) => chain.id === name).sequence, sourceChain.sequence);
  return { name, subunitIndex: +n, subunitUuid: sourceChain.uuid, length: sequence.length, unitId: unit.id, componentId: graphChain.components[0].id };
});
assert.deepEqual(chains.map((row) => row.length), [448, 444, 214, 214]);
assert.equal(new Set(chains.map((row) => row.subunitUuid)).size, 4);
assert.notEqual(subunits[1].sequence, subunits[2].sequence);
assert.equal(subunits[3].sequence, subunits[4].sequence);
assert.notEqual(chains[2].unitId, chains[3].unitId);
assert.equal(chains[0].unitId, chains[2].unitId);
assert.equal(chains[1].unitId, chains[3].unitId);
assert.equal(bondPairs.length, 4);
assert.equal(projected.length, 3);
const retained = reference.component_graph.connections.map(({left,right,kind}) => {
  for (const endpoint of [left,right]) {
    const row = chains.find(({name}) => endpoint.chain_id === name);
    assert.equal(row.componentId, endpoint.component_id);
  }
  assert.equal(kind, 'disulfide');
  return unordered([left.chain_id,right.chain_id]);
}).sort();
assert.deepEqual(retained, projected);
assert.deepEqual(alternative.chains, reference.chains);
assert.deepEqual(alternative.component_graph.chains, reference.component_graph.chains);
assert.deepEqual(alternative.component_graph.connections, reference.component_graph.connections.filter(({left,right}) => unordered([left.chain_id,right.chain_id]) !== 'J/Q'));
assert.equal(lineage.parent_id, reference.id);
assert.equal(lineage.child_id, alternative.id);
assert.deepEqual(lineage.change_set.before.component_graph, reference.component_graph);
assert.deepEqual(lineage.change_set.after.component_graph, alternative.component_graph);
assert.equal(hypothesis.status, 'proposed');
assert.ok(hypothesis.lineage_ids.includes(lineage.id));
const evidence = records.filter((record) => record.type === 'evidence');
assert.equal(evidence.length, 1);
assert.equal(evidence[0].kind, 'annotation');
assert.equal(evidence[0].subject_id, reference.id);
assert.ok(evidence[0].timestamp && evidence[0].source.name);
const result = {
  status: 'PASS',
  source: { approvalId: registry.approvalID, version: registry.version, sha256: sha, chains, interchainResidueLinks: bondPairs, expectedComponentPairs: projected, savedComponentPairs: retained },
  alternative: { sameChains: true, sameOrigins: true, omittedComponentPair: 'J/Q', evidenceKind: 'annotation', hypothesisStatus: 'proposed' },
  edges: {},
};
let child, browser;
const outbound = [], browserErrors = [];

(async () => {
  child = spawn(process.env.PYTHON, ['-m', 'workspace_app.server', '--database', path.join(review, 'edge.sqlite3'), '--port', '0'], {cwd: snapshot, windowsHide: true});
  const origin = await new Promise((resolve, reject) => {
    const timeout = setTimeout(() => reject(Error('Server startup timeout')), 20000);
    child.on('error', reject);
    child.on('exit', (code) => reject(Error('Server exited ' + code)));
    child.stdout.on('data', (data) => {
      const match = String(data).match(/http:\/\/127\.0\.0\.1:\d+/);
      if (match) { clearTimeout(timeout); resolve(match[0]); }
    });
  });
  browser = await chromium.launch({channel: 'chrome', headless: true});
  const context = await browser.newContext({viewport: {width: 1440, height: 1000}});
  await context.route('**/*', (route) => {
    const url = route.request().url();
    if (url.startsWith(origin + '/')) return route.continue();
    outbound.push(url);
    return route.abort();
  });
  const page = await context.newPage();
  page.on('pageerror', (error) => browserErrors.push(error.message));
  await page.goto(origin);
  const button = (name) => page.getByRole('button', {name,exact:true});
  const exact = (id) => page.locator('[id="' + id + '"]');
  const read = () => page.evaluate(async (project) => (await fetch('/api/bundle?project_id=' + project)).json(), exported.project.id);
  await button('Import data').click();
  await exact('import-file').setInputFiles(file);
  await button('Validate & preview').click();
  await exact('commit-import').click();
  await exact('import-dialog').waitFor({state:'hidden'});
  await page.waitForFunction(() => !document.querySelector('#import-button').disabled && document.querySelector('#project-select').value);
  assert.deepEqual(await read(), exported);
  for (const unit of units) await page.locator('[data-unit-select="' + unit.id + '"]').check();
  await button('Design an explicit composition').click();
  const side = page.locator('[data-composition-compare="left"]');
  const selectReference = async () => {
    await side.selectOption(reference.id);
    await button('Use this design as parent recipe').click();
  };
  await selectReference();
  await exact('composition-name').fill('Test missing endpoint');
  await exact('composition-external').fill('EDGE-MISSING');
  await exact('composition-reason').fill('Verify dangling source link handling.');
  await page.locator('[data-chain-remove="3"]').click();
  await page.getByText('Endpoint missing or renamed. Choose both intended endpoints before previewing.', {exact:true}).waitFor();
  const rejected = page.waitForResponse((response) => response.url().endsWith('/api/composition-review'));
  await button('Review new composition before saving').click();
  const rejection = await rejected;
  const payload = await rejection.json();
  assert.equal(rejection.status(), 422);
  assert.match(payload.error, /Connection endpoint is not defined/);
  await exact('notification').getByText(payload.error, {exact:true}).or(page.getByText(payload.error, {exact:true})).first().waitFor();
  assert.equal(await exact('composition-preview-dialog').isVisible(), false);
  assert.deepEqual(await read(), exported);
  await page.screenshot({path:path.join(review,'browser','edge-missing-endpoint.png')});
  result.edges.removedEndpoint = {httpStatus: rejection.status(), error: payload.error, persistedBundleUnchanged: true};

  await selectReference();
  await exact('composition-name').fill('Test same-sequence origin swap');
  await exact('composition-external').fill('EDGE-SWAP');
  await exact('composition-reason').fill('Test explicit source identity with sequence-identical light chains.');
  for (const [index, sourceChain] of [[2, chains[3]], [3, chains[2]]]) {
    const part = page.locator('fieldset[data-recipe-chain="' + index + '"] .composition-part');
    await part.locator('[data-part-unit]').selectOption(sourceChain.unitId);
    await part.locator('[data-part-source-chain]').selectOption(sourceChain.name);
    await part.getByRole('button', {name:'Use full declared source chain',exact:true}).click();
  }
  await button('Review new composition before saving').click();
  await exact('composition-preview-dialog').waitFor({state:'visible'});
  const preview = JSON.parse(await page.locator('#composition-preview-content > pre').textContent());
  const changed = preview.entities.find((record) => record.type === 'molecule');
  const changedLineage = preview.entities.find((record) => record.type === 'lineage');
  assert.deepEqual(changed.chains, reference.chains);
  assert.deepEqual(changed.component_graph.connections, reference.component_graph.connections);
  assert.notDeepEqual(changedLineage.change_set.before, changedLineage.change_set.after);
  for (const [index, sourceChain] of [[2, chains[3]], [3, chains[2]]]) {
    assert.deepEqual(changed.component_graph.chains[index].components[0].origin, {
      binding_unit_id: sourceChain.unitId, chain_id: sourceChain.name, start: 1, end: 214
    });
  }
  await button('Save reviewed composition records').click();
  await exact('composition-preview-dialog').waitFor({state:'hidden'});
  const columns = page.locator('#composition-contexts article');
  await columns.last().getByRole('heading', {name:/EDGE-SWAP/}).waitFor();
  await columns.last().locator('li').filter({hasText:chains[2].componentId}).filter({hasText:'Source ' + chains[3].unitId + ' / L2 raw 1–214'}).waitFor();
  await columns.first().locator('li').filter({hasText:chains[2].componentId}).filter({hasText:'Source ' + chains[2].unitId + ' / L1 raw 1–214'}).waitFor();
  await page.locator('#composition-compare').screenshot({path:path.join(review,'browser','edge-source-swap.png')});
  await page.reload();
  const persisted = await read();
  assert.deepEqual(persisted.entities.slice(0, records.length), records);
  assert.deepEqual(persisted.entities.find(({id}) => id === changed.id), changed);
  assert.deepEqual(persisted.entities.find(({id}) => id === changedLineage.id), changedLineage);
  result.edges.sameSequenceSwap = {sequencesUnchanged: true, endpointsUnchanged: true, provenanceRecordedAsDistinctChange: true, persistedOriginalsUnchanged: true, sourcesBefore: [chains[2].unitId, chains[3].unitId], sourcesAfter: [chains[3].unitId, chains[2].unitId]};
  result.browser = browser.version();
  result.browserErrors = browserErrors;
  result.outbound = outbound;
  assert.deepEqual(browserErrors, []);
  assert.deepEqual(outbound, []);
  fs.writeFileSync(path.join(review,'edge-results.json'),JSON.stringify(result,null,2) + '\n');
  console.log(JSON.stringify(result));
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
}).finally(async () => {
  await browser?.close();
  child?.kill();
});



