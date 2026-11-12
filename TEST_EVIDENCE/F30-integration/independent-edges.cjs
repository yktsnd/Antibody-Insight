const assert = require('node:assert/strict');
const {spawn, spawnSync} = require('node:child_process');
const {writeFileSync} = require('node:fs');
const path = require('node:path');
const {chromium} = require('playwright');

const root = process.cwd();
const output = path.join(root, '..');
const cases = [];
const errors = [];
const outbound = [];
const fixtureSource = `
import json
from workspace_app.structure_fixtures import structure_bundle
from workspace_app.fixtures import STAMP, fixture_id

bundle = structure_bundle()
molecules = [e for e in bundle["entities"] if e["type"] == "molecule"]

def numbered(molecule, domain, start, positions, verified):
    sequence = next(chain["sequence"] for chain in molecule["chains"] if chain["id"] == "H")
    bundle["entities"].append({
        "id": fixture_id("residue_map", domain), "type": "residue_map",
        "project_id": bundle["project"]["id"], "created_at": STAMP,
        "molecule_id": molecule["id"], "chain_id": "H", "domain_id": domain,
        "chain_type": "heavy", "scheme": "IMGT", "definition": "rearranged_v_domain",
        "status": "mapped", "reason": None, "sequence_start": start,
        "sequence_end": start + len(positions) - 1,
        "source": {"name": "Synthetic numbering coordinate edge fixture", "version": "1"},
        "verification": {"status": "engineering_fixture" if verified else "unverified",
                         "reference": None, "reviewer": None, "reviewed_at": None},
        "entries": [{"sequence_index": index, "aa": sequence[index - 1], "number": number, "ins_code": insertion}
                    for index, (number, insertion) in enumerate(positions, start)]
    })

numbered(molecules[0], "Primary A", 1, [(105, ""), (111, ""), (111, ".1"), (112, ".2"), (112, ".1"), (112, "")], True)
numbered(molecules[0], "Alternative A", 2, [(110, ""), (111, ""), (112, ".1"), (112, "")], False)
numbered(molecules[1], "Primary B", 1, [(105, ""), (106, ""), (111, ""), (111, ".2"), (112, ".2"), (112, "")], True)
print(json.dumps(bundle))
`;
const made = spawnSync(process.env.PYTHON, ['-c', fixtureSource], {cwd: root, encoding:'utf8'});
assert.equal(made.status, 0, made.stderr);
const fixture = JSON.parse(made.stdout);
const [a,b] = fixture.entities.filter(e => e.type === 'molecule');
const map = domain => fixture.entities.find(e => e.domain_id === domain);
const server = spawn(process.env.PYTHON, ['-m','workspace_app.server','--database', path.join(output, 'edges-' + process.pid + '.sqlite3'),'--port','0'], {cwd:root, windowsHide:true});
let browser;
let page;

async function check(name, test) {
  try {
    const evidence = await test();
    cases.push({name, status:'PASS', evidence});
  } catch (error) {
    cases.push({name, status:'FAIL', error: String(error), stack: error.stack});
  }
  console.log(JSON.stringify(cases.at(-1)));
}

async function run() {
  const origin = await new Promise((resolve,reject) => {
    const timeout = setTimeout(() => reject(new Error('Startup timeout')), 15000);
    server.on('error',reject);
    server.stdout.on('data',(chunk) => {
      const match = chunk.toString().match(/http:\/\/127\.0\.0\.1:\d+/);
      if (match) { clearTimeout(timeout); resolve(match[0]); }
    });
  });
  browser = await chromium.launch({headless:true, channel:'chrome', args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
  const context = await browser.newContext({viewport:{width:1440,height:1000}});
  page = await context.newPage();
  page.setDefaultTimeout(16000);
  page.on('pageerror',error => errors.push(error.message));
  await context.route('**/*', route => {
    if (route.request().url().startsWith(origin + '/')) return route.continue();
    outbound.push(route.request().url());
    return route.abort();
  });
  await page.goto(origin);
  await page.getByRole('button',{name:'Import data',exact:true}).click();
  await page.locator('#import-format').selectOption('json');
  await page.locator('#import-text').fill(JSON.stringify(fixture));
  await page.getByRole('button',{name:'Validate & preview',exact:true}).click();
  await page.getByRole('button',{name:/Save \d+ valid rows/}).click();
  for (const molecule of [a,b]) await page.getByRole('checkbox',{name:'Select '+molecule.external_id,exact:true}).check();
  const nav = screen => page.locator('nav [data-screen="'+screen+'"]').click();
  await nav('W');
  const table = page.getByRole('table',{name:'Imported IMGT coordinates'});
  const primaryMapA = page.getByRole('combobox',{name:'Numbering map for STR-001 H',exact:true});
  const host = molecule => page.locator('[data-structure-host="'+molecule.id+'"]');
  const active = molecule => page.locator('[data-position-molecule="'+molecule.id+'"].residue.active');
  const cell = (molecule, label) => table.getByRole('button',{name:molecule.external_id+' H IMGT '+label,exact:true});
  const viewer = molecule => page.waitForFunction(id => !!window.StructureUI.contextFor(id)?.selectionAtoms,molecule.id);
  const selectedAtoms = molecule => page.evaluate(id => StructureUI.contextFor(id).selectionAtoms.map(atom =>
    ({chain:atom.auth_chain,number:atom.auth_number,insertion:atom.insertion_code})), molecule.id);
  const design = () => page.getByRole('button',{name:'Design a substitution at the selected residue',exact:true}).click();
  const bundle = () => page.evaluate(async id => (await fetch('/api/bundle?project_id='+id)).json(),fixture.project.id);
  const initial = await bundle();
  assert.equal(initial.entities.length,fixture.entities.length);

  await check('Ambiguous domain requires explicit choice and asymmetric insertions sort by the IMGT contract', async () => {
    assert.equal(await table.count(),0);
    assert.equal(await primaryMapA.inputValue(),'');
    await primaryMapA.selectOption(map('Primary A').id);
    const headers = await table.locator('thead th').allTextContents();
    assert.deepEqual(headers.slice(1),['105','106','111','111.1','111.2','112.2','112.1','112']);
    assert.deepEqual(await table.getByRole('rowheader').allTextContents(),
      ['STR-001 / HPrimary A · engineering_fixture','STR-002 / HPrimary B · engineering_fixture']);
    return {headers};
  });
  for (const molecule of [a,b]) {
    await page.getByRole('combobox',{name:'Source model for '+molecule.external_id,exact:true}).selectOption('1');
    await viewer(molecule);
  }
  await check('Present numbering with missing atoms and missing peer annotation remain distinct', async () => {
    await cell(a,'111.1 D, raw index 3').click();
    assert.equal(await active(a).getAttribute('data-position'),'3');
    assert.equal(await active(b).count(),0);
    const bRow = table.getByRole('rowheader',{name:/STR-002/}).locator('..');
    assert.equal(await bRow.locator('td').nth(3).getByLabel('No annotation at this position').count(),1);
    assert.equal(await bRow.locator('td').nth(3).getByRole('button').count(),0);
    await host(a).locator('.structure-selection').filter({hasText:/Mapping unavailable/}).waitFor();
    await viewer(b);
    assert.deepEqual(await selectedAtoms(a),[]);
    assert.deepEqual(await selectedAtoms(b),[]);
    return {raw:3, numbering:'111.1', structure:'unavailable', peer:'no annotation'};
  });
  await check('Asymmetric inserted coordinate selects only the exact source atoms and passes exact map to Design', async () => {
    await cell(b,'112.2 F, raw index 5').click();
    await host(b).locator('.structure-selection').filter({hasText:/Mapped H raw index 5/}).waitFor();
    await viewer(a);
    assert.deepEqual(await selectedAtoms(b),[{chain:'H-author',number:104,insertion:''}]);
    assert.deepEqual(await selectedAtoms(a),[]);
    assert.equal(await active(a).getAttribute('data-position'),'4');
    assert.equal(await active(b).getAttribute('data-position'),'5');
    assert.equal(await table.getByRole('button',{pressed:true}).count(),1);
    await design();
    assert.equal(await page.locator('#design-parent').inputValue(),b.id);
    assert.equal(await page.locator('#design-map').inputValue(),map('Primary B').id);
    assert.equal(await page.locator('#design-position-filter').inputValue(),'112.2');
    await nav('W');
    return {raw:[4,5], map:map('Primary B').id, source:[{chain:'H-author',number:104,insertion:''}]};
  });
  await check('Second candidate residue identity appears in the workspace breadcrumb', async () => {
    await cell(b,'105 A, raw index 1').click();
    await page.evaluate(() => scrollTo(0,0));
    await page.screenshot({path:path.join(output,'second-candidate-breadcrumb.png')});
    const breadcrumb = await page.locator('#breadcrumb').textContent();
    assert.match(breadcrumb,/STR-002 \/ H \/ index 1$/);
    return {breadcrumb};
  });
  await check('Changing the selected row from H to L clears the selected raw position', async () => {
    await cell(b,'105 A, raw index 1').click();
    const chainB = page.getByRole('combobox',{name:'Chain for STR-002',exact:true});
    await chainB.selectOption('L');
    await page.evaluate(() => scrollTo(0,0));
    await page.screenshot({path:path.join(output,'after-chain-switch.png')});
    const selected = await page.locator('.residue.active').evaluateAll(nodes => nodes.map(node => node.getAttribute('aria-label')));
    const details = await page.locator('.sequence-details').allTextContents();
    await chainB.selectOption('H');
    assert.deepEqual(selected,[],JSON.stringify(details));
    return {selected,details};
  });
  await check('Explicit unverified alternative is viewable while design action refuses its annotation', async () => {
    await primaryMapA.selectOption(map('Alternative A').id);
    assert.match(await table.getByRole('rowheader',{name:/STR-001/}).textContent(),/Alternative A · unverified/);
    await cell(a,'111 D, raw index 3').click();
    await design();
    await page.locator('#notification').filter({hasText:/Choose an eligible source map/}).waitFor();
    assert.equal(await page.locator('nav [data-screen="W"]').getAttribute('aria-current'),'page');
    await primaryMapA.selectOption('');
    assert.equal(await table.count(),0);
    return {status:'unverified', designBlocked:true, noImplicitFallback:true};
  });
  await check('Inspection leaves the persisted bundle and external-request count unchanged', async () => {
    assert.deepEqual(await bundle(),initial);
    assert.deepEqual(errors,[]);
    assert.deepEqual(outbound,[]);
    return {entityCount:initial.entities.length, errors, outbound};
  });
  return browser.version();
}

let browserVersion;
run().then(version => { browserVersion = version; }).catch(error => {
  cases.push({name:'Independent review harness',status:'NEEDS-EVIDENCE',error:String(error),stack:error.stack});
}).finally(async () => {
  const status = cases.some(test => test.status === 'FAIL') ? 'FAIL' : cases.every(test => test.status === 'PASS') ? 'PASS' : 'NEEDS-EVIDENCE';
  writeFileSync(path.join(output,'independent-edges.json'),JSON.stringify({
    status, reviewer:'/root/numbered_review', timestamp:new Date().toISOString(), browserVersion, cases, errors, outbound
  },null,2)+'\n');
  await browser?.close();
  server.kill();
  if (status !== 'PASS') process.exitCode = 1;
});
