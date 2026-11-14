const assert = require('node:assert/strict');
const {spawn} = require('node:child_process');
const {createHash} = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {chromium} = require('playwright');
const input = process.env.AWX_PAIR_INPUT_DIRECTORY;
assert(input, 'Set AWX_PAIR_INPUT_DIRECTORY to the prepared public input directory');
const baseline = process.argv.includes('--baseline');
const artifacts = fs.mkdtempSync(path.join(os.tmpdir(), 'awx-real-pair-'));
const sources = [
  {name:'D44.1', pdb:'1MLC', cif:path.resolve('fixtures/public/1MLC.cif'), numbering:path.resolve('fixtures/public/1MLC-AB.anarci.txt'), antigen:'E'},
  {name:'D44.1des', pdb:'6GC2', cif:path.join(input,'6GC2.cif'), antigen:null},
];
const python = process.env.PYTHON || 'python';
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
  await page.locator('#project-title').fill('D44.1 and D44.1des public structure comparison');
  await preview();
  await page.locator('#group-molecular-format').fill('Fab');
  for (const [index,name,chain,role] of [[1,'D44.1','L','light'],[2,'D44.1','H','heavy'],[3,'D44.1des','L','light'],[4,'D44.1des','H','heavy']]) {
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

  }
  for (const source of sources) await page.locator('[data-select="'+source.id+'"]').check();
  await page.locator('nav [data-screen="W"]').click();
  for (const source of sources) {
    const button = page.locator('[data-edit-correspondence="'+source.id+'"]');
    await button.click();
    for (const [asym,chain] of [['A','L'],['B','H'],...(source.antigen?[[source.antigen,null]]:[])]) {
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

  const positions = ['W','Y'];
  const mapped = [];
  for (const [i,source] of sources.entries()) {
    const host = page.locator('[data-structure-host="'+source.id+'"]');
    await host.locator('canvas').waitFor();
    await page.evaluate(() => window.scrollTo(0,0));
    const target=page.locator('[data-position-molecule="'+source.id+'"][data-position="47"]');
    const initial = await target.evaluate(el=>Math.round(el.getBoundingClientRect().top));
    const expected=positions[i];
    assert.equal((await target.textContent()).trim(),'47'+expected);
    await target.click();
    const clickScrollY=await page.evaluate(()=>Math.round(window.scrollY));
    const label=host.locator('.structure-selection').filter({hasText:/Mapped H raw index 47 .*label B:47/});
    await label.waitFor();
    assert.match(await label.textContent(), i === 0 ? /author B:47.*TRP/ : /author H:47.*TYR/);
    const labelTop=await label.evaluate(el=>Math.round(el.getBoundingClientRect().top+window.scrollY));
    const canvasTop=await host.locator('canvas').evaluate(el=>Math.round(el.getBoundingClientRect().top+window.scrollY));
    const initialView = await target.evaluate(el => { const b=el.getBoundingClientRect(), pane=el.closest('.sequence-viewport')?.getBoundingClientRect(); return {targetTop:b.top,targetBottom:b.bottom,paneTop:pane?.top,paneBottom:pane?.bottom}; });
    const canvasBottom=await host.locator('canvas').evaluate(el=>el.getBoundingClientRect().bottom);
    if (!baseline) assert.ok(initialView.targetTop >= initialView.paneTop && initialView.targetBottom <= initialView.paneBottom);
    if (!baseline) assert.ok(canvasBottom <= 1000, 'Entire canvas must be in the 1440x1000 viewport: '+canvasBottom);
    await page.screenshot({path:path.join(artifacts,source.pdb+'-initial-selection.png')});
    await host.locator('canvas').scrollIntoViewIfNeeded();
    const structureScrollY=await page.evaluate(()=>Math.round(window.scrollY));
    if (!baseline) assert.equal(structureScrollY, 0);
    await page.screenshot({path:path.join(artifacts,source.pdb+'-selection.png')});
    mapped.push({name:source.name,pdb:source.pdb,exactSelected:await label.textContent(),coordinatePreview:source.coordinatePreview,initialTargetTop:initial,clickScrollY,canvasTop,labelTop,canvasBottom,structureScrollY,initialView});
  }
  await page.locator('nav [data-screen="R"]').click();
  await page.locator('[data-research-task=decision]').click();
  await page.locator('#decision-add-context').waitFor();
  const facts=await page.locator('#decision-add-context option').allTextContents();
  assert.equal(stored.entities.filter((e)=>e.type==='evidence').length,0);
  assert.deepEqual(await read(),stored);
  assert.deepEqual(errors,[]);
  assert.deepEqual(outside,[]);
  const report={status:'PASS',viewport:'1440x1000',mapped,oneSelectionClickPerCandidate:true,measuredEvidence:0,decisionContext:facts,errors,outside};
  fs.writeFileSync(path.join(artifacts,'case-baseline.json'),JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify(report),artifacts);
}
run().catch((e) => { console.error(e); console.log(artifacts); process.exitCode=1; }).finally(async () => { try { await browser?.close(); } finally { server.kill(); } });
