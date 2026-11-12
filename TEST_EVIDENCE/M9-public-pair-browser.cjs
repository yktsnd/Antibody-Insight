const assert = require('node:assert/strict');
const {spawn} = require('node:child_process');
const {createHash} = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {chromium} = require('playwright');
const input = process.env.AWX_PAIR_INPUT_DIRECTORY;
assert(input, 'Set AWX_PAIR_INPUT_DIRECTORY to the prepared public input directory');
const artifacts = fs.mkdtempSync(path.join(os.tmpdir(), 'awx-real-pair-'));
const sources = [
  {name:'D44.1', pdb:'1MLC', cif:path.resolve('fixtures/public/1MLC.cif'), numbering:path.resolve('fixtures/public/1MLC-AB.anarci.txt'), antigen:'E'},
  {name:'D1.3', pdb:'1FDL', cif:path.join(input,'1FDL.cif'), numbering:path.join(input,'1FDL-AB.anarci.txt'), antigen:'C'},
];
const python = process.env.PYTHON;
const server = spawn(python, ['-m','workspace_app.server','--database',path.join(artifacts,'pair.sqlite3'),'--port','0'], {windowsHide:true});
let browser;
async function run() {
  const origin = await new Promise((resolve,reject) => {
    const timer = setTimeout(() => reject(Error('Server startup timed out')),15000);
    server.on('error',reject);
    server.stdout.on('data',(chunk) => {
      const match = chunk.toString().match(/http:\/\/127\.0\.0\.1:\d+/);
      if (match) { clearTimeout(timer); resolve(match[0]); }
    });
  });
  browser = await chromium.launch({headless:true,channel:'chrome',args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
  const page = await browser.newPage({viewport:{width:1440,height:1000}});
  page.setDefaultTimeout(45000);
  const errors = [], outside = [];
  page.on('pageerror',(e) => errors.push(e.message));
  await page.route('**/*',(route) => {
    if (route.request().url().startsWith(origin + '/')) return route.continue();
    outside.push(route.request().url());
    return route.abort();
  });
  async function openFile(format,file) {
    await page.locator('#import-button').click();
    await page.locator('#import-format').selectOption(format);
    await page.locator('#import-file').setInputFiles(file);
    await page.waitForFunction(() => document.querySelector('#import-text').value.length > 0);
  }
  async function preview() {
    await page.getByRole('button',{name:'Validate & preview',exact:true}).click();
    await page.locator('#import-preview').waitFor();
  }
  async function save(count) {
    const post = page.waitForResponse((res) => res.url().endsWith('/api/import') && res.request().method()==='POST');
    await page.locator('#commit-import').click();
    const res = await post;
    assert.equal(res.status(),200,await res.text());
    await page.locator('#import-dialog').waitFor({state:'hidden'});
    await page.locator('#notification').filter({hasText:'Saved '+count+' entities'}).waitFor();
  }
  const read = () => page.evaluate(async () => {
    const id = document.querySelector('#project-select').value;
    return (await fetch('/api/bundle?project_id='+id)).json();
  });
  await page.goto(origin);
  await openFile('fasta_grouped',path.join(input,'public-fab-pair.fasta'));
  await page.locator('#project-title').fill('D44.1 and D1.3 public structure comparison');
  await preview();
  await page.locator('#group-molecular-format').fill('Fab');
  for (const [index,name,chain,role] of [[1,'D44.1','L','light'],[2,'D44.1','H','heavy'],[3,'D1.3','L','light'],[4,'D1.3','H','heavy']]) {
    await page.getByRole('textbox',{name:'Candidate for record '+index,exact:true}).fill(name);
    await page.getByRole('textbox',{name:'Chain ID for record '+index,exact:true}).fill(chain);
    await page.getByRole('textbox',{name:'Role for record '+index,exact:true}).fill(role);
  }
  await page.locator('#apply-sequence-grouping').click();
  await save(2);
  const initial = await read();
  const molecules = initial.entities.filter((e) => e.type === 'molecule');
  assert.equal(molecules.length,2);
  for (const source of sources) {
    const molecule = molecules.find((m) => m.external_id === source.name);
    source.id = molecule.id;
    await openFile('mmcif',source.cif);
    await page.locator('#structure-molecule').selectOption(molecule.id);
    await page.locator('#structure-origin').selectOption('experimental');
    await preview();
    await save(1);
    await openFile('anarci_text',source.numbering);
    await page.locator('#numbering-tool-version').fill('2026.2.13.2');
    await preview();
    const targets = await page.locator('#numbering-target-chains option').evaluateAll((xs) => xs.map((x) => x.value));
    for (const [index,chain] of [[1,'L'],[2,'H']]) {
      const label = targets.find((label) => label.startsWith(source.name+' / '+chain+' '));
      assert(label);
      await page.getByRole('combobox',{name:'Target for record '+index+' domain 1',exact:true}).fill(label);
    }
    await page.locator('#apply-numbering-bindings').click();
    await save(3);
  }
  for (const source of sources) await page.locator('[data-select="'+source.id+'"]').check();
  await page.locator('nav [data-screen="W"]').click();
  for (const source of sources) {
    const button = page.locator('[data-edit-correspondence="'+source.id+'"]');
    await button.click();
    for (const [asym,chain] of [['A','L'],['B','H'],[source.antigen,null]]) {
      const row = page.locator('.map-chain-row').filter({hasText:new RegExp(' / label '+asym+' / segment ')});
      await row.locator('[data-map-role]').selectOption(chain ? 'antibody' : 'antigen');
      if (chain) await row.locator('[data-map-chain]').selectOption(chain);
      else {
        await row.locator('[data-target-namespace]').fill('PDB-entity');
        await row.locator('[data-target-identifier]').fill(source.pdb+':3');
      }
    }
    await page.locator('[data-map-from-polymer]').click();
    await page.locator('#map-review').filter({hasText:/\d+ mapped residues/}).waitFor();
    source.coordinatePreview = (await page.locator('#map-review').textContent()).match(/\d+ mapped residues/)[0];
    await page.locator('[data-map-save]').click();
    await page.locator('#notification').filter({hasText:'Saved correspondence'}).waitFor();
    await page.locator('#map-dialog').waitFor({state:'hidden'});
  }
  for (const source of sources) await page.getByRole('combobox',{name:'Chain for '+source.name,exact:true}).selectOption('H');
  const stored = await read();
  for (const source of sources) {
    const numbering = stored.entities.filter((e) => e.type==='residue_map' && e.molecule_id===source.id);
    assert.deepEqual(numbering.map((e) => [e.chain_id,e.entries.length,e.verification.status]).sort(),[['H',116,'unverified'],['L',107,'unverified']]);
    const structure = stored.entities.filter((e) => e.type==='structure_map' && e.molecule_id===source.id);
    assert.equal(structure.length,1);
    const heavy = numbering.find((e) => e.chain_id==='H');
    const position = heavy.entries.find((e) => e.number===105 && !e.insertion);
    assert(position);
    await page.locator('[data-position-molecule="'+source.id+'"][data-position="'+position.sequence_index+'"]').click();
    await page.locator('.structure-selection').filter({hasText:new RegExp('Mapped H raw index '+position.sequence_index+' .*label B:'+position.sequence_index+'(?:[^0-9]|$)')}).first().waitFor();
    source.selected = {raw:position.sequence_index, scheme:heavy.scheme, coordinate:String(position.number),depositedLabel:'B:'+position.sequence_index};
  }
  assert.equal(stored.entities.filter((e) => e.type==='evidence').length,0);
  assert.deepEqual(errors,[]);
  assert.deepEqual(outside,[]);
  await page.evaluate(() => scrollTo(0,0));
  await page.screenshot({path:path.join(artifacts,'public-pair-W.png')});
  const sha = (file) => createHash('sha256').update(fs.readFileSync(file)).digest('hex');
  const report = {status:'PASS', scope:'Two genuine public experimental structures and native tool outputs. Human numbering review pending.', candidates:sources.map(({name,pdb,cif,numbering,selected,coordinatePreview})=>({name,pdb,coordinates_sha256:sha(cif),numbering_sha256:sha(numbering),selected,coordinatePreview})), file_input_sha256:sha(path.join(input,'public-fab-pair.fasta')), page_errors:errors, outside};
  fs.writeFileSync(path.join(artifacts,'public-pair-W.json'),JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify(report),artifacts);
}
run().catch((e) => { console.error(e); console.log(artifacts); process.exitCode=1; }).finally(async () => { try { await browser?.close(); } finally { server.kill(); } });
