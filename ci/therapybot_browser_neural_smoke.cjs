'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const crypto = require('node:crypto');

const PROMPTS = Object.freeze([
  'List two questions I can ask about my work shift.',
  'What does writing down my work schedule help prevent?'
]);
const ALLOWED_REMOTE = [
  'https://huggingface.co/',
  'https://us.aws.cdn.hf.co/'
];

function validateAssistantTurn(answer, attribution) {
  const text = String(answer || '').trim();
  if (text.length < 16 || /^(the local model returned no visible text|local inference failed|a local error interrupted)/i.test(text)) {
    throw new Error('No actual model tokens in the visible assistant reply');
  }
  if (!String(attribution || '').startsWith('Experimental 135M model output, permitted by a limited lexical filter')) {
    throw new Error('Missing experimental attribution for neural reply');
  }
  return text;
}
function requireDistinctAnswers(answers) {
  if (answers.length !== 2 || answers[0].trim() === answers[1].trim()) {
    throw new Error('Two distinct generated model answers required');
  }
}
function parseOptions(argv) {
  const options = {};
  const keys = new Set(['--browser', '--origin', '--browser-bin', '--mode']);
  if (argv.length !== 8) throw new Error('Expected --browser, --origin, --browser-bin and --mode');
  for (let i=0;i<argv.length;i+=2) {
    if (!keys.has(argv[i]) || !argv[i+1] || options[argv[i]]) throw new Error('Invalid or repeated option '+argv[i]);
    options[argv[i]] = argv[i+1];
  }
  const browser = options['--browser'], mode = options['--mode'];
  if (!['edge','firefox'].includes(browser)) throw new Error('Invalid browser');
  if (!['online','offline'].includes(mode)) throw new Error('Invalid test mode');
  if (!path.isAbsolute(options['--browser-bin'])) throw new Error('Browser binary must be absolute');
  let url;
  try { url = new URL(options['--origin']); } catch { throw new Error('Invalid loopback origin'); }
  if (url.protocol !== 'http:' || url.hostname !== '127.0.0.1' || !url.port ||
      url.username || url.password || (url.pathname !== '/' && url.pathname !== '') ||
      url.search || url.hash) throw new Error('Only explicit HTTP 127.0.0.1 loopback origin accepted');
  return {browser, mode, executable:options['--browser-bin'], origin:url.origin};
}
function isExternal(requestUrl, origin) {
  if (/^(?:blob:|data:|about:)/.test(requestUrl)) return false;
  return !requestUrl.startsWith(origin+'/');
}
function isAllowlistedRemote(requestUrl) {
  return ALLOWED_REMOTE.some(prefix=>requestUrl.startsWith(prefix));
}
const delay = ms => new Promise(resolve=>setTimeout(resolve,ms));

async function run(options) {
  const puppeteer = require('puppeteer-core');
  const profile = fs.mkdtempSync(path.join(process.env.RUNNER_TEMP || os.tmpdir(),'bt2-neural-'+options.browser+'-'));
  const ff = options.browser === 'firefox';
  let browser;
  const requests = [], pageErrors = [], blocked = [];
  const started = Date.now();
  try {
    browser = await puppeteer.launch({
      executablePath:options.executable, browser:ff?'firefox':'chrome',
      protocol:ff?'webDriverBiDi':'cdp', headless:true, userDataDir:profile,
      args:ff?[]:['--no-first-run','--no-default-browser-check']
    });
    const page = await browser.newPage();
    page.setDefaultTimeout(180000);
    if (options.mode === 'offline') await page.setRequestInterception(true);
    page.on('request',request=>{
      const url=request.url();
      requests.push(url);
      if (options.mode === 'offline') {
        if (url.startsWith('https://huggingface.co/') || url.startsWith('https://us.aws.cdn.hf.co/')) {
          blocked.push(url); request.abort('failed').catch(()=>{});
        } else request.continue().catch(()=>{});
      }
    });
    page.on('pageerror',error=>pageErrors.push(String(error?.message || error)));
    const response = await page.goto(options.origin+'/index.html',{waitUntil:'domcontentloaded',timeout:30000});
    assert.ok([200,304].includes(response.status()),'Local preview did not serve index.html');
    await page.waitForFunction(()=>document.getElementById('status')?.textContent.includes('Rules-only') &&
      Boolean(window.TherapyBotNeural),{timeout:20000});
    const before = await page.evaluate(()=>({
      consent:document.getElementById('model-consent').checked,
      disabled:document.getElementById('model-load').disabled,
      loaded:Boolean(window.TherapyBotNeural?.isLoaded())
    }));
    assert.deepEqual(before,{consent:false,disabled:true,loaded:false},'Unsafe preconsent state');
    const modelPin = await page.evaluate(()=>window.TherapyBotNeural.model);
    assert.equal(modelPin.size,105454144,'Model byte pin differs from approved artifact');
    assert.equal(modelPin.hash,'8030f04528538d47bda434f6f0bdf3952c40a58123e4d5e755332f23731a8684',
      'Model SHA-256 pin differs from approved artifact');
    assert.deepEqual(requests.filter(url=>isExternal(url,options.origin)),[],'External request before consent');
    await page.click('#model-consent');
    assert.equal(await page.$eval('#model-load',el=>el.disabled),false,'Consent did not enable model load');
    await page.click('#model-load');
    await page.waitForFunction(()=>Boolean(window.TherapyBotNeural?.isLoaded()) ||
      document.getElementById('model-status')?.textContent.startsWith('Model NOT LOADED:'),{timeout:300000});
    const load = await page.evaluate(()=>({
      loaded:Boolean(window.TherapyBotNeural?.isLoaded()),
      status:document.getElementById('model-status').textContent
    }));
    if (options.mode === 'offline') {
      assert.equal(load.loaded,false,'Offline test unexpectedly loaded a model');
      assert.match(load.status,/^Model NOT LOADED:/,'Offline failure did not fail closed');
      assert.ok(blocked.length>=1,'Expected pinned model fetch to be blocked');
      console.log(JSON.stringify({tag:'NEURAL_OFFLINE_FAIL_CLOSED_PASS',browser:options.browser,
        modelLoaded:false,blockedRequests:blocked.length,elapsedMs:Date.now()-started}));
      return;
    }
    assert.ok(load.loaded,'Pinned model did not load: '+load.status);
    assert.match(load.status,/Opt-in model loaded locally/i,'Loaded status not evidenced');
    const answers = [];
    for (const prompt of PROMPTS) {
      const previous = await page.$$eval('.assistant-message',elements=>elements.length);
      await page.click('#message');
      await page.type('#message',prompt,{delay:0});
      await page.click('#send');
      await page.waitForFunction(previousCount=>document.querySelectorAll('.assistant-message').length>previousCount,
        {timeout:180000},previous);
      const result = await page.evaluate(()=>{
        const turns=document.querySelectorAll('.assistant-message');
        const last=turns[turns.length-1];
        return {answer:last?.querySelector('p:not(.warning)')?.textContent||'',
          attribution:last?.querySelector('p.warning')?.textContent||''};
      });
      answers.push(validateAssistantTurn(result.answer,result.attribution));
    }
    requireDistinctAnswers(answers);
    const external = requests.filter(url=>isExternal(url,options.origin));
    assert.ok(external.some(url=>url.startsWith('https://huggingface.co/')),'Pinned HF model not requested');
    assert.ok(external.every(isAllowlistedRemote),'Non-allowlisted external request observed');
    assert.deepEqual(pageErrors,[],'JavaScript runtime exception');
    const storage = await page.evaluate(async()=>({
      cacheKeys:typeof caches==='undefined'?null:await caches.keys(),
      indexedDB:typeof indexedDB.databases==='function'?(await indexedDB.databases()).map(db=>db.name):null,
      localStorageKeys:localStorage.length,
      serviceWorkers:typeof navigator.serviceWorker?.getRegistrations==='function'?
        (await navigator.serviceWorker.getRegistrations()).length:null
    }));
    assert.deepEqual(storage.cacheKeys||[],[],'Application CacheStorage contains entries');
    assert.deepEqual(storage.indexedDB||[],[],'IndexedDB contains entries');
    assert.equal(storage.localStorageKeys,0,'Unexpected localStorage persistence');
    assert.equal(storage.serviceWorkers||0,0,'Unexpected service worker registration');
    console.log(JSON.stringify({
      tag:'NEURAL_USER_CLICK_TWO_PROMPTS_PASS',browser:options.browser,
      loaded:true,pinnedModelSize:modelPin.size,pinnedModelSha256:modelPin.hash,answers:answers.map(x=>({
        length:x.length,sha256:crypto.createHash('sha256').update(x).digest('hex')
      })),externalOrigins:[...new Set(external.map(x=>new URL(x).origin))],
      storage,elapsedMs:Date.now()-started,clinicalQualification:'none'
    }));
  } finally {
    if (browser) await browser.close().catch(()=>{});
    fs.rmSync(profile,{recursive:true,force:true});
  }
}

if (require.main === module) {
  Promise.resolve().then(()=>run(parseOptions(process.argv.slice(2)))).catch(error=>{
    console.error('NEURAL_BROWSER_CI_FAIL '+String(error?.stack || error));
    process.exitCode=1;
  });
}
module.exports = {validateAssistantTurn,requireDistinctAnswers,parseOptions};
