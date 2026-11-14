const assert = require('node:assert/strict');
const {spawn} = require('node:child_process');
const {createHash} = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {chromium} = require('playwright');
const input = process.env.AWX_PAIR_INPUT_DIRECTORY;
assert(input, 'Set AWX_PAIR_INPUT_DIRECTORY to the prepared public input directory');
const compareNumbered = process.argv.includes('--numbered-comparison');
const artifacts = fs.mkdtempSync(path.join(os.tmpdir(), 'awx-m14-independent-result-'));
const sources = [
  {name:'D44.1', pdb:'1MLC', cif:path.resolve('fixtures/public/1MLC.cif'), numbering:path.resolve('fixtures/public/1MLC-AB.anarci.txt'), antigen:'E'},
  {name:'D44.1des', pdb:'6GC2', cif:path.join(input,'6GC2.cif'), antigen:null},
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
    await page.locator('#structure-map-dialog').waitFor({state:'hidden'});
  }
  for (const source of sources) await page.getByRole('combobox',{name:'Chain for '+source.name,exact:true}).selectOption('H');
  const stored = await read();

  const cases = [
    {oneLetter:'W', residue:'TRP', author:'B', atoms:14, ca:[46.192,20.883,59.269]},
    {oneLetter:'Y', residue:'TYR', author:'H', atoms:12, ca:[-19.892,101.616,-3.883]}
  ];
  const dimension = await page.evaluate(() => [innerWidth,innerHeight]);
  assert.deepEqual(dimension,[1440,1000]);
  const comp = (name) => page.getByRole('combobox',{name:'Chain for '+name,exact:true});
  const sequence = (source,chain,index) => page.locator('[data-position-molecule="'+source.id+'"][data-position-chain="'+chain+'"][data-position="'+index+'"]');
  const waitState = (id) => page.waitForFunction((sourceId) => StructureUI.contextFor(sourceId)?.selectionAtoms !== undefined,id);
  const context = (source) => page.evaluate((id) => {
    const active = StructureUI.contextFor(id);
    return {model:active.model,mapId:active.data.map.id,label:active.host.querySelector('.structure-selection').textContent,focus:!active.host.querySelector('[data-focus-structure]').disabled,atoms:active.selectionAtoms};
  },source.id);
  const setViewportTop = () => page.evaluate(() => window.scrollTo(0,0));
  const elementBounds = (loc) => loc.evaluate((node) => {
    const {x,y,width,height,top,bottom,right,left} = node.getBoundingClientRect();
    const scroller = node.closest('[data-sequence-viewport]');
    const clip = scroller?.getBoundingClientRect();
    return {x,y,width,height,top,bottom,right,left,scrollY:scrollY,documentY:scrollY+y,
      clipped:!!clip && (top < clip.top || bottom > clip.bottom + 1 || left < clip.left || right > clip.right)};
  });
  const inViewport = (bounds) => bounds.top >= 0 && bounds.bottom <= 1000 && bounds.left >= 0 && bounds.right <= 1440 && !bounds.clipped;
  function storedPosition(source,chain,raw) {
    const map = stored.entities.find((e) => e.type === 'structure_map' && e.molecule_id === source.id);
    return {map,entry:map.residues.find((entry) => entry.chain_id === chain && entry.sequence_index === raw)};
  }
  async function verifyEmpty(source) {
    await waitState(source.id);
    const current = await context(source);
    assert.deepEqual(current.atoms,[]);
    assert.equal(current.focus,false);
    return current;
  }
  const checked = [];
  for (const [index,source] of sources.entries()) {
    const other = sources[1-index], expected = cases[index];
    await waitState(source.id);
    await waitState(other.id);
    await setViewportTop();
    const target = sequence(source,'H',47);
    const initialTarget = await elementBounds(target);
    assert.equal((await target.textContent()).trim(),'47'+expected.oneLetter);
    await target.click();
    await waitState(source.id);
    await waitState(other.id);
    const label = page.locator('[data-structure-host="'+source.id+'"] .structure-selection');
    const canvases = await Promise.all(sources.map((item) => elementBounds(page.locator('[data-structure-host="'+item.id+'"] canvas'))));
    const labelBounds = await elementBounds(label), targetBounds = await elementBounds(target);
    const current = await context(source);
    const {map,entry} = storedPosition(source,'H',47);
    assert.equal(current.mapId,map.id);
    assert.equal(current.label,`Mapped H raw index 47 ↔ model 1 / author ${expected.author}:47? / label B:47 / segment unknown / ${expected.residue} / conformer common`);
    assert.equal(current.focus,true);
    assert.equal(await target.getAttribute('aria-pressed'),'true');
    assert.equal(await page.locator('[data-sequence-viewport] [aria-pressed=true]').count(),1);
    const otherSelection = await verifyEmpty(other);
    assert.equal(otherSelection.label.includes('Mapped H raw index 47'),false);
    assert.equal(await sequence(other,'H',47).getAttribute('aria-pressed'),'false');
    assert(inViewport(targetBounds), JSON.stringify(targetBounds));
    assert(inViewport(labelBounds),JSON.stringify(labelBounds));
    assert(canvases.every(inViewport), JSON.stringify(canvases));
    assert.equal(targetBounds.scrollY,0);
    assert.equal(current.atoms.length,expected.atoms);
    for (const atom of current.atoms) {
      for (const [key,value] of Object.entries(entry.structure_residue)) assert.equal(atom[key],value,key);
    }
    assert.deepEqual(current.atoms.filter((atom) => atom.atom_name === 'CA').map((a)=>[a.x,a.y,a.z]),[expected.ca]);
    assert.equal(entry.structure_residue.auth_chain,expected.author);
    assert.equal(entry.structure_residue.label_asym,'B');
    assert.equal(entry.structure_residue.label_number,47);
    assert.equal(entry.structure_residue.model,1);
    assert.equal(entry.structure_residue.residue_name,expected.residue);
    assert.ok(current.atoms.length > 0);
    await page.screenshot({path:path.join(artifacts,source.pdb+'-selection.png')});
    checked.push({name:source.name,pdb:source.pdb,exactSelected:current.label,coordinatePreview:source.coordinatePreview,initialTarget,target:targetBounds,label:labelBounds,canvases,atoms:current.atoms.length,ca:expected.ca});
  }
  const modified = sources[1], original = sources[0];
  await comp(modified.name).selectOption('L');
  await verifyEmpty(modified);
  await verifyEmpty(original);
  assert.equal(await page.locator('[data-sequence-viewport] [aria-pressed=true]').count(),0);
  const missing = storedPosition(modified,'L',1).entry;
  assert.equal(missing.status,'unavailable');
  await sequence(modified,'L',1).click();
  const noCoordinates = await verifyEmpty(modified);
  assert.match(noCoordinates.label,/Mapping unavailable/);
  assert.equal(await sequence(modified,'L',1).getAttribute('aria-pressed'),'true');
  const model20 = storedPosition(modified,'L',20).entry;
  assert.equal(model20.status,'mapped');
  await sequence(modified,'L',20).click();
  await waitState(modified.id);
  const mapped20 = await context(modified);
  assert.match(mapped20.label,/Mapped L raw index 20.*author L:1\?.*label A:20/);
  assert.equal(mapped20.focus,true);
  assert.equal(mapped20.atoms.every((atom)=>atom.model===1 && atom.auth_chain==='L' && atom.auth_number===1 && atom.label_asym==='A' && atom.label_number===20),true);
  await sequence(modified,'L',47).click();
  await waitState(modified.id);
  const mapped47L = await context(modified);
  assert.match(mapped47L.label,/Mapped L raw index 47.*label A:47/);
  assert.equal(mapped47L.atoms.every((atom)=>atom.model===1 && atom.auth_chain==='L' && atom.label_asym==='A' && atom.label_number===47),true);
  await comp(modified.name).selectOption('H');
  await verifyEmpty(modified);
  assert.equal(await page.locator('[data-sequence-viewport] [aria-pressed=true]').count(),0);
  await setViewportTop();
  await sequence(modified,'H',47).press('Enter');
  await waitState(modified.id);
  assert.equal(await sequence(modified,'H',47).evaluate((node)=>node === document.activeElement),true);
  await page.keyboard.press('Tab');
  assert.equal(await sequence(modified,'H',48).evaluate((node)=>node === document.activeElement),true);
  await page.keyboard.press('Enter');
  await waitState(modified.id);
  const keyboard48 = await context(modified);
  assert.match(keyboard48.label,/Mapped H raw index 48.*author H:48\?.*label B:48/);
  assert(inViewport(await elementBounds(sequence(modified,'H',48))));
  await page.locator('nav [data-screen="R"]').click();
  const selectionInR = await page.evaluate(() => JSON.parse(localStorage.getItem('awx-state-'+localStorage.getItem('awx-project'))).residueSelection);
  assert.deepEqual(selectionInR,{molecule_id:modified.id,chain_id:'H',sequence_index:48});
  await page.locator('nav [data-screen="W"]').click();
  await waitState(modified.id);
  assert.equal((await context(modified)).label,keyboard48.label);
  assert.equal(await sequence(modified,'H',48).getAttribute('aria-pressed'),'true');
  assert.equal(await page.locator('#selection-count').textContent(),'2 selected');
  assert.match(await page.locator('#breadcrumb').textContent(),/D44\.1des \/ H \/ index 48$/);
  const jump = page.locator('[data-jump="'+modified.id+'"]');
  await jump.fill('201');
  await jump.press('Tab');
  await waitState(modified.id);
  const nearEnd = await context(modified);
  assert.match(nearEnd.label,/Mapped H raw index 201.*label B:201/);
  assert.equal(await sequence(modified,'H',201).getAttribute('aria-pressed'),'true');
  assert.equal(await sequence(modified,'H',200).count(),0);
  assert.equal((await elementBounds(sequence(modified,'H',201))).clipped,false);
  assert.deepEqual(await read(),stored);
  assert.deepEqual(errors,[]);
  assert.deepEqual(outside,[]);
  const report = {status:'PASS',browser:await browser.version(),viewport:dimension,checked,edges:{
    switchedSameRawAcrossCandidates:true,
    switchedActiveHeavyToLightClearsSelection:true,
    unobserved6GC2L1:{expectedSource:missing.reason,actual:noCoordinates.label},
    observed6GC2L20:mapped20.label,
    switchedSameRawAcrossChains:mapped47L.label,
    keyboard47To48AndRReturn:keyboard48.label,jumpAcross200Boundary:nearEnd.label
  },noDatabaseWritesDuringInspection:true,errors,outside};
  fs.writeFileSync(path.join(artifacts,'independent.json'),JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify(report),artifacts);
}
run().catch((e) => { console.error(e); console.log(artifacts); process.exitCode=1; }).finally(async () => { try { await browser?.close(); } finally { server.kill(); } });

