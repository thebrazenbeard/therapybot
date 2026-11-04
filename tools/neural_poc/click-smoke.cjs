// Actual user-controls browser smoke: no direct Wllama calls or model-result injection.
const args=process.argv;
const option=name=>{const i=args.indexOf(name);return i<0?null:args[i+1]};
const puppeteer=require(option('--puppeteer-dir')||'puppeteer');
const path=require('path');
const ff=args.includes('--firefox');
const browserName=ff?'firefox':'edge';
const executable=option('--browser-bin')||(ff?'C:\\Program Files\\Mozilla Firefox\\firefox.exe':'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe');
const port=Number(option('--port')||43877);
if(!Number.isInteger(port)||port<1025||port>65535)throw new Error('Invalid local port');
const origin='http://127.0.0.1:'+port;
(async()=>{
  const browser=await puppeteer.launch({
    executablePath:executable,browser:ff?'firefox':'chrome',protocol:ff?'webDriverBiDi':'cdp',
    headless:true,userDataDir:path.join(__dirname,'click-smoke-'+browserName+'-profile'),
    args:ff?[]:['--no-first-run','--no-default-browser-check','--disable-application-cache']
  });
  const page=await browser.newPage();
  page.setDefaultTimeout(180000);
  const requests=[],errors=[],consoleErrors=[],started=Date.now();
  page.on('request',r=>requests.push({host:new URL(r.url()).host,method:r.method(),type:ff?'bidi':r.resourceType()}));
  page.on('pageerror',e=>errors.push(e.message));
  page.on('console',m=>{if(m.type()==='error')consoleErrors.push(m.text())});
  try{
    const res=await page.goto(origin+'/index.html',{waitUntil:'domcontentloaded',timeout:20000});
    if(![200,304].includes(res.status()))throw new Error('Local page HTTP '+res.status());
    const before=await page.evaluate(async()=>({
      model:document.querySelector('#model').value,
      status:document.querySelector('#status').textContent,
      consent:document.querySelector('#consent').checked,
      downloadDisabled:document.querySelector('#download').disabled,
      generationDisabled:document.querySelector('#generate').disabled,
      cacheKeys:typeof caches==='undefined'?null:await caches.keys()
    }));
    if(before.model!=='smol'||before.consent||!before.downloadDisabled||!before.generationDisabled)throw new Error('Unsafe preconsent UI state');
    if(requests.some(r=>r.host!=='127.0.0.1:'+port))throw new Error('Preconsent external request');
    await page.click('#consent');
    await page.click('#download');
    await page.waitForFunction(()=>/Loaded locally|NOT LOADED:/.test(document.querySelector('#status').textContent),{timeout:150000});
    const loaded=await page.evaluate(()=>({
      status:document.querySelector('#status').textContent,
      model:document.querySelector('#model').value,
      generationDisabled:document.querySelector('#generate').disabled
    }));
    if(!/Loaded locally/.test(loaded.status)||loaded.generationDisabled)throw new Error('Selected GGUF did not load: '+loaded.status);
    await page.click('#prompt');
    await page.keyboard.down('Control');
    await page.keyboard.press('A');
    await page.keyboard.up('Control');
    await page.keyboard.type('What are two practical questions to ask before accepting a new work shift?');
    await page.click('#generate');
    await page.waitForFunction(()=>/Time:|Local generation failed:/.test(document.querySelector('#reply').textContent),{timeout:90000});
    const after=await page.evaluate(async()=>({
      reply:document.querySelector('#reply').textContent,
      status:document.querySelector('#status').textContent,
      cacheKeys:typeof caches==='undefined'?null:await caches.keys(),
      indexedDbNames:typeof indexedDB.databases==='function'?(await indexedDB.databases()).map(x=>x.name):null
    }));
    if(/Local generation failed:|No visible model reply/.test(after.reply))throw new Error('No useful visible token output: '+after.reply);
    const screenshot=path.join(__dirname,'click-smoke-'+browserName+'-result.png');
    await page.screenshot({path:screenshot,fullPage:true});
    console.log(JSON.stringify({tag:'USER_CLICK_REAL_INFERENCE_PASS',browser:browserName,before,loaded,after,requests,errors,consoleErrors,elapsedMs:Date.now()-started,screenshot}));
  }catch(err){
    console.log(JSON.stringify({tag:'USER_CLICK_REAL_INFERENCE_FAIL',browser:browserName,error:String(err?.stack||err),requests:requests.slice(-30),errors,consoleErrors,elapsedMs:Date.now()-started}));
    process.exitCode=1;
  }finally{await browser.close()}
})().catch(err=>{console.error(String(err?.stack||err));process.exitCode=2});
