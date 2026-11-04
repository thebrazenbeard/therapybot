const puppeteer=require('C:\\Users\\patri\\AppData\\Local\\Executor\\DesktopCommanderMCP\\node_modules\\puppeteer');
const path=require('path');
const assert=require('node:assert/strict');
(async()=>{
  const ff=process.argv.includes('--firefox');
  const executable=ff?'C:\\Program Files\\Mozilla Firefox\\firefox.exe':'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
  const browser=await puppeteer.launch({executablePath:executable,browser:ff?'firefox':'chrome',protocol:ff?'webDriverBiDi':'cdp',headless:true,userDataDir:path.join(__dirname,ff?'firefox-smoke-profile':'edge-smoke-profile'),args:ff?[]:['--no-first-run','--no-default-browser-check']});
  const page=await browser.newPage();
  const requests=[],errors=[],consoleErrors=[];
  page.on('request',r=>requests.push({url:r.url(),method:r.method(),type:ff?'bidi-unknown':r.resourceType()}));
  page.on('pageerror',e=>errors.push(e.message));
  page.on('console',m=>{if(m.type()==='error')consoleErrors.push(m.text())});
  try{
    const response=await page.goto('http://127.0.0.1:43187/index.html',{waitUntil:'networkidle0',timeout:20000});
    assert.ok([200,304].includes(response.status()),`Unexpected HTTP ${response.status()}`);
    const before=await page.evaluate(()=>({status:document.querySelector('#status').textContent,downloadDisabled:document.querySelector('#download').disabled,generateDisabled:document.querySelector('#generate').disabled,caches:typeof caches==='undefined'?'unavailable':'available'}));
    assert.match(before.status,/No model loaded|Idle/);
    assert.equal(before.downloadDisabled,true);
    assert.equal(before.generateDisabled,true);
    const startupExternal=requests.filter(x=>!x.url.startsWith('http://127.0.0.1:43187'));
    assert.equal(startupExternal.length,0);
    await page.click('#preflight');
    await page.waitForFunction(()=>/preflight PASS|NOT LOADED:/.test(document.querySelector('#status').textContent),{timeout:30000});
    const after=await page.evaluate(()=>({status:document.querySelector('#status').textContent,modelReady:!document.querySelector('#generate').disabled,usedCacheStorage:typeof caches!=='undefined'&&false}));
    const external=requests.filter(x=>!x.url.startsWith('http://127.0.0.1:43187')).map(x=>({host:new URL(x.url).host,method:x.method,type:x.type}));
    const report={before,after,external,errors,consoleErrors,ok:/preflight PASS/.test(after.status),startupExternalCount:startupExternal.length};
    console.log(JSON.stringify(report));
    if(errors.some(x=>!/favicon\.ico/.test(x))||!report.ok)process.exitCode=1;
  }catch(err){console.log(JSON.stringify({fatal:err.message,requests:requests.length,errors,consoleErrors}));process.exitCode=2;}
  finally{await browser.close();}
})().catch(e=>{console.error(e.stack||e);process.exitCode=3});
