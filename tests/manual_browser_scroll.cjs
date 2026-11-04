/* Opt-in real-browser regression for 14-turn responsive chat scroll behavior.
 * Set THERAPYBOT_PUPPETEER_PATH, THERAPYBOT_EDGE_PATH, THERAPYBOT_FIREFOX_PATH.
 * Uses loopback + temporary browser profiles; no network or persistent storage.
 */
'use strict';
const fs = require('node:fs');
const http = require('node:http');
const os = require('node:os');
const path = require('node:path');

const sourceRoot = process.env.THERAPYBOT_SOURCE_ROOT || path.resolve(__dirname, '..');
const root = path.join(sourceRoot, 'embedded');
const puppeteer = require(process.env.THERAPYBOT_PUPPETEER_PATH || 'puppeteer-core');
const files = {'/':'index.html','/style.css':'style.css','/catalog.js':'catalog.js','/engine.js':'engine.js','/council.js':'council.js','/conversation_adapter.js':'conversation_adapter.js','/ui.js':'ui.js'};
const metrics = () => {
  const el = document.querySelector('#conversation-log');
  const max = Math.max(0, el.scrollHeight - el.clientHeight);
  const last = el.querySelector('.message:last-child');
  const e = el.getBoundingClientRect();
  const l = last?.getBoundingClientRect();
  return {top:el.scrollTop, max, height:el.clientHeight, scrollHeight:el.scrollHeight,
    lastVisible: Boolean(l && l.bottom <= e.bottom + 3 && l.top >= e.top - 3),
    gap: max - el.scrollTop};
};
const server = http.createServer((req, res) => {
  const pathname = new URL(req.url, 'http://127.0.0.1').pathname;
  if (pathname === '/favicon.ico') {res.writeHead(204).end();return;}
  const name = files[pathname];
  if (!name || req.method !== 'GET') {res.writeHead(404).end('not found');return;}
  const target = path.join(root,name);
  res.writeHead(200,{'Content-Type': name.endsWith('.css')?'text/css':name.endsWith('.js')?'text/javascript':'text/html','Cache-Control':'no-store'});
  fs.createReadStream(target).pipe(res);
});

async function main() {
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  const origin = 'http://127.0.0.1:'+server.address().port;
  const cases = [
    {name:'Edge156',browser:'chrome',executablePath:process.env.THERAPYBOT_EDGE_PATH || 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'},
    {name:'Firefox159',browser:'firefox',executablePath:process.env.THERAPYBOT_FIREFOX_PATH || 'C:\\Program Files\\Mozilla Firefox\\firefox.exe'}
  ];
  const report={sourceRoot,origin,cases:[],timestamp:new Date().toISOString()};
  for (const target of cases) {
    const profile=fs.mkdtempSync(path.join(os.tmpdir(),'tb-scroll-wave3-'));
    let browser;
    const result={name:target.name,assertions:[],errors:[],external:[]};
    report.cases.push(result);
    const check=(name,condition,details)=>result.assertions.push({name,pass:Boolean(condition),details});
    try {
      browser=await puppeteer.launch({browser:target.browser,executablePath:target.executablePath,headless:true,userDataDir:profile,args:['--disable-background-networking','--no-first-run','--disable-sync']});
      const page=await browser.newPage();
      await page.setViewport({width:1365,height:900,deviceScaleFactor:1});
      page.on('pageerror',e=>result.errors.push(String(e)));
      page.on('console',m=>{if(m.type()==='error')result.errors.push(m.text());});
      await page.setRequestInterception(true);
      page.on('request',req=>{if(!req.url().startsWith(origin+'/')&&!req.url().startsWith('data:')){result.external.push(req.url());req.abort('blockedbyclient').catch(()=>{});}else req.continue().catch(()=>{});});
      await page.goto(origin+'/',{waitUntil:'networkidle0',timeout:20000});
      await page.waitForFunction(()=>document.querySelector('#engine-status')?.textContent?.includes('Rules only'),{timeout:8000});
      for(let i=0;i<14;i++){
        const prior=await page.$$eval('.message--assistant',nodes=>nodes.length);
        const prompt='Round '+(i+1)+': I want a grounded explanation of working with uncertainty, autonomy and boundaries. How would I compare evidence and assumptions about this?';
        await page.$eval('#message',(e,s)=>{e.value=s;e.dispatchEvent(new Event('input',{bubbles:true}));},prompt);
        await page.click('#send-message');
        await page.waitForFunction(prior=>document.querySelectorAll('.message--assistant').length>prior,{timeout:9000},prior);
      }
      let settledAtBottom=true;
      try {await page.waitForFunction(()=>{const e=document.querySelector('#conversation-log');return e.scrollHeight-e.clientHeight-e.scrollTop<=2;},{polling:50,timeout:4000});}catch{settledAtBottom=false;}
      const before=await page.evaluate(metrics);
      check('desktop-follow-before-resize',settledAtBottom && before.gap<=2,{before});
      await page.setViewport({width:390,height:844,deviceScaleFactor:1});
      let followed=true;
      try {await page.waitForFunction(()=>{const e=document.querySelector('#conversation-log');return e.scrollHeight-e.clientHeight-e.scrollTop<=2;},{polling:50,timeout:4000});}catch{followed=false;}
      const after=await page.evaluate(metrics);
      check('14turn-desktop-to-390-bottom-visible',followed && after.gap<=2 && after.lastVisible,{before,after});
      await page.$eval('#conversation-log',e=>e.scrollTo({top:0,behavior:'instant'}));
      let topReached=true;
      try {await page.waitForFunction(()=>document.querySelector('#conversation-log').scrollTop<=20,{polling:50,timeout:3000});}catch{topReached=false;}
      const atTop=await page.evaluate(metrics);
      check('programmatic-scroll-to-top',topReached && atTop.top<=20,{atTop});
      await page.setViewport({width:1365,height:900,deviceScaleFactor:1});
      await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
      const afterReturn=await page.evaluate(metrics);
      check('resize-does-not-steal-reading-position',afterReturn.top<=40,{afterReturn});
      await page.$eval('#conversation-log',e=>e.scrollTo({top:e.scrollHeight,behavior:'instant'}));
      await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
      await page.setViewport({width:390,height:844,deviceScaleFactor:1});
      await page.waitForFunction(()=>{const e=document.querySelector('#conversation-log');return e.scrollHeight-e.clientHeight-e.scrollTop<=2;},{polling:50,timeout:4000});
      await page.hover('#conversation-log');
      await page.mouse.wheel({deltaY:-2000});
      await page.waitForFunction(()=>{const e=document.querySelector('#conversation-log');return e.scrollHeight-e.clientHeight-e.scrollTop>=1500;},{polling:50,timeout:4000});
      const afterWheel = await page.evaluate(metrics);
      await page.setViewport({width:1365,height:900,deviceScaleFactor:1});
      await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
      const wheelReturn = await page.evaluate(metrics);
      check('wheel-reader-intent-survives-resize',wheelReturn.gap>100,{afterWheel,wheelReturn});
      await page.$eval('#conversation-log',e=>e.scrollTo({top:e.scrollHeight,behavior:'instant'}));
      await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
      await page.focus('#conversation-log');
      await page.keyboard.press('PageUp');
      await page.waitForFunction(()=>{const e=document.querySelector('#conversation-log');return e.scrollHeight-e.clientHeight-e.scrollTop>=100;},{polling:50,timeout:4000});
      const afterKeyboard = await page.evaluate(metrics);
      await page.setViewport({width:390,height:844,deviceScaleFactor:1});
      await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
      const keyboardReturn = await page.evaluate(metrics);
      check('keyboard-reader-intent-survives-resize',keyboardReturn.gap>100,{afterKeyboard,keyboardReturn});
      check('zero-external-and-script-errors',!result.external.length&&!result.errors.length,{external:result.external,errors:result.errors});
    }catch(e){result.errors.push(String(e.stack||e));}
    finally{if(browser)await browser.close().catch(()=>{});fs.rmSync(profile,{recursive:true,force:true});}
  }
  server.close();
  report.pass=report.cases.every(c=>c.assertions.length===7 && c.assertions.every(a=>a.pass));
  process.stdout.write(JSON.stringify(report,null,2));
  process.exitCode=report.pass?0:1;
}
main().catch(e=>{server.close();console.error(e);process.exitCode=2;});
