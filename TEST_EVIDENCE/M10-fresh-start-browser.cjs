const assert = require('node:assert/strict');
const {spawn, spawnSync} = require('node:child_process');
const fs = require('node:fs');
const {createHash} = require('node:crypto');
const os = require('node:os');
const path = require('node:path');
const {chromium} = require('playwright');
const temp = fs.mkdtempSync(path.join(os.tmpdir(),'awx-fresh-start-'));
const db = path.join(temp,'workspace.sqlite3');
const errors = [];
const external = [];
let server, browser;
function start() {
  server = spawn('pwsh',['-NoProfile','-File','start.ps1','-Database',db,'-Port','0'],{windowsHide:true});
  return new Promise((resolve,reject)=>{
    const timeout=setTimeout(()=>reject(Error('Startup timed out')),20000);
    server.once('error',reject);
    server.once('exit',(code)=>{clearTimeout(timeout);reject(Error('Launcher exited '+code));});
    server.stdout.on('data',(chunk)=>{
      const match=chunk.toString().match(/http:\/\/127\.0\.0\.1:\d+/);
      if(match){clearTimeout(timeout);resolve(match[0]);}
    });
  });
}
async function stop() {
  if (server && server.exitCode===null && server.signalCode===null) {
    const exited = new Promise((resolve)=>server.once('exit',resolve));
    const result=spawnSync('taskkill.exe',['/PID',String(server.pid),'/T','/F'],{windowsHide:true});
    assert.equal(result.status,0);
    await exited;
  }
}
async function open(origin) {
  const page=await browser.newPage({acceptDownloads:true});
  page.on('pageerror',(error)=>errors.push(error.message));
  await page.route('**/*',(route)=>{
    if(route.request().url().startsWith(origin+'/'))return route.continue();
    external.push(route.request().url());
    return route.abort();
  });
  await page.goto(origin);
  await page.waitForFunction(()=>!document.querySelector('#import-button').disabled);
  return page;
}
const bundle = (page,id) => page.evaluate(async (id)=>(await fetch('/api/bundle?project_id='+id)).json(),id);
(async()=>{
  const origin=await start();
  browser=await chromium.launch({headless:true,channel:'chrome'});
  let page=await open(origin);
  await page.locator('#import-button').click();
  await page.locator('#import-file').setInputFiles(path.resolve('validation/public/3OGO-E.fasta'));
  await page.waitForFunction(() => document.querySelector('#import-text').value.startsWith('>3OGO-E'));
  await page.locator('#project-title').fill('Public VHH setup smoke');
  const preview = page.waitForResponse((res)=>res.url().endsWith('/api/preview') && res.request().method()==='POST');
  await page.getByRole('button',{name:'Validate & preview',exact:true}).click();
  const response = await preview;
  assert.equal(response.status(),200,await response.text());
  await page.locator('#commit-import').click();
  await page.locator('#candidate-count').waitFor();
  const id=await page.locator('#project-select').inputValue();
  const saved=await bundle(page,id);
  assert.equal(saved.entities.length,1);
  assert.equal(saved.entities[0].external_id,'3OGO-E');
  assert.equal(saved.entities[0].chains[0].sequence.length,123);
  const sourceSha = createHash('sha256').update(fs.readFileSync(path.resolve('validation/public/3OGO-E.fasta'))).digest('hex');
  assert.equal(saved.entities[0].source.version,'sha256:'+sourceSha);
  const download=page.waitForEvent('download');
  await page.locator('#export-button').click();
  const archive=path.join(temp,'public-vhh.awx.json');
  await (await download).saveAs(archive);
  assert.deepEqual(JSON.parse(fs.readFileSync(archive,'utf8')),saved);
  await page.close();
  await stop();
  page=await open(await start());
  assert.equal(await page.locator('#project-select').inputValue(),id);
  assert.deepEqual(await bundle(page,id),saved);
  assert.deepEqual(errors,[]);
  assert.deepEqual(external,[]);
  console.log(JSON.stringify({status:'PASS',scope:'Fresh Windows checkout and documented launcher; public FASTA import, byte-source digest retained, JSON export and same DB restart',molecule:saved.entities[0].external_id,sequence_length:123,errors,external}));
})().catch((e)=>{console.error(e);process.exitCode=1;}).finally(async()=>{try{await browser?.close();}finally{await stop();}});
