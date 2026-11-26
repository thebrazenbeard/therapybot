/* Real Edge UI opt-in neural smoke; no credentials or browser packages. */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const port = Number(process.argv[2] || 43322);
const url = process.argv[3] || 'http://127.0.0.1:43329/index.html';
const screenshot = process.argv[4] || null;
const offline = process.argv.includes('--offline');
async function start() {
const target = (await fetch('http://127.0.0.1:'+port+'/json/list').then(x=>x.json()))
  .find(x=>x.type==='page' && x.webSocketDebuggerUrl);
assert.ok(target, 'Isolated Edge page missing');
const ws = new WebSocket(target.webSocketDebuggerUrl);
const requests=[], errors=[], blocked=[], pending=new Map();
let sequence=0;
ws.addEventListener('message',event=>{
 const data=JSON.parse(String(event.data));
 if(data.id){const p=pending.get(data.id);if(p){pending.delete(data.id);data.error?p.reject(Error(JSON.stringify(data.error))):p.resolve(data.result);}}
 if(data.method==='Network.requestWillBeSent')requests.push(data.params.request.url);
 if(data.method==='Runtime.exceptionThrown')errors.push(data.params.exceptionDetails.text);
 if(data.method==='Network.loadingFailed')blocked.push(data.params.errorText);
});
await new Promise((resolve,reject)=>{ws.addEventListener('open',resolve,{once:true});ws.addEventListener('error',reject,{once:true});});
async function cdp(method,params={}){
 const id=++sequence;
 const answer=new Promise((resolve,reject)=>pending.set(id,{resolve,reject}));
 ws.send(JSON.stringify({id,method,params}));
 return Promise.race([answer,new Promise((_,reject)=>setTimeout(()=>reject(Error('Timeout '+method)),15000))]);
}
async function inspect(expression){
 const r=await cdp('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});
 if(r.exceptionDetails)throw Error(r.exceptionDetails.text);
 return r.result.value;
}
async function click(id){
 await inspect('document.getElementById('+JSON.stringify(id)+').scrollIntoView({block:"center",behavior:"instant"})');
 const pos=await inspect('(()=>{const r=document.getElementById('+JSON.stringify(id)+').getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2}})()');
 await cdp('Input.dispatchMouseEvent',{type:'mouseMoved',x:pos.x,y:pos.y});
 await cdp('Input.dispatchMouseEvent',{type:'mousePressed',x:pos.x,y:pos.y,button:'left',clickCount:1});
 await cdp('Input.dispatchMouseEvent',{type:'mouseReleased',x:pos.x,y:pos.y,button:'left',clickCount:1});
}
async function ctrlEnter(){
 const o={key:'Enter',code:'Enter',windowsVirtualKeyCode:13,nativeVirtualKeyCode:13,modifiers:2};
 await cdp('Input.dispatchKeyEvent',{...o,type:'keyDown'});
 await cdp('Input.dispatchKeyEvent',{...o,type:'keyUp'});
}
async function waitUntil(check,label,seconds=240){
 const stop=Date.now()+seconds*1000;
 while(Date.now()<stop){
  let value=false,status='';
  try{value=await inspect(check)}catch(_){}
  if(value)return;
  try{status=await inspect("document.getElementById('model-status').textContent")}catch(_){}
  if(status.startsWith('Model NOT LOADED:'))throw Error(label+' failed: '+status);
  await new Promise(resolve=>setTimeout(resolve,700));
 }
 throw Error(label+' did not complete');
}
async function main(){
 try{
  await cdp('Network.enable');
  if(offline)await cdp('Network.setBlockedURLs',{urls:['https://huggingface.co/*','https://us.aws.cdn.hf.co/*']});
  await cdp('Page.enable');
  await cdp('Runtime.enable');
  await cdp('Page.navigate',{url});
  await waitUntil("document.getElementById('status').textContent.includes('Rules-only')",'rules-ready',15);
  assert.equal(await inspect("document.getElementById('model-load').disabled"),true);
  const before=requests.filter(x=>x.startsWith('https://'));
  assert.deepEqual(before,[],'Auto remote download before consent');
  await click('model-consent');
  assert.equal(await inspect("document.getElementById('model-consent').checked"),true);
  assert.equal(await inspect("document.getElementById('model-load').disabled"),false);
  console.log('CONSENT_ACTIVATED; now clicking 105MB opt-in.');
  await click('model-load');
  if(offline){
    const until=Date.now()+30000;
    while(Date.now()<until && !(await inspect("document.getElementById('model-status').textContent.startsWith('Model NOT LOADED:')"))){
      await new Promise(r=>setTimeout(r,250));
    }
    assert.equal(await inspect("window.TherapyBotNeural?.isLoaded()"),false);
    assert.equal(await inspect("document.getElementById('model-status').textContent.startsWith('Model NOT LOADED:')"),true);
    assert.ok(blocked.length>0,'Expected a blocked remote model request');
    console.log(JSON.stringify({mode:'offline opt-in',url,externalAttempts:requests.filter(x=>x.startsWith('https://')),blocked,modelLoaded:false,resetToRules:true},null,2));
    return;
  }
  await waitUntil("window.TherapyBotNeural?.isLoaded()", 'Wllama local model',300);
  console.log('MODEL_LOADED',await inspect("document.getElementById('model-status').textContent"));
  await inspect("document.getElementById('message').focus()");
  await cdp('Input.insertText',{text:'List two questions I can ask about my work shift.'});
  await ctrlEnter();
  await waitUntil("document.querySelectorAll('.assistant-message').length>=2",'neural generation',180);
  const answer=await inspect("document.querySelectorAll('.assistant-message')[1].textContent");
  assert.ok(answer.length>10,'Model did not visibly generate words');
  assert.ok(answer.includes('Experimental 135M model output.'),'Model response attribution missing');
  const local=new URL(url).origin+'/';
  const external=requests.filter(x=>!x.startsWith(local)&&!x.startsWith('data:'));
  assert.ok(external.some(x=>x.includes('huggingface.co')),'Expected pinned HF request absent');
  assert.ok(external.every(x=>x.startsWith('https://huggingface.co/')||x.startsWith('https://us.aws.cdn.hf.co/')),'Unexpected external origin');
  assert.deepEqual(errors,[],'JS runtime exceptions');
  const after=await cdp('Page.captureScreenshot',{format:'png'});
  if(screenshot)fs.writeFileSync(screenshot,Buffer.from(after.data,'base64'));
  console.log(JSON.stringify({
   browser:'Edge CDP opt-in neural',url,modelsLoaded:1,modelBytes:105454144,
   externalPageRequests:external.map(x=>new URL(x).origin),
   observedModelReplyLength:answer.length, noAutoDownloadBeforeConsent:true,
   jsExceptions:errors.length,clinicalQualification:'none'
  },null,2));
 } finally{
  if(offline)try{await cdp('Network.setBlockedURLs',{urls:[]});}catch(_){}
  ws.close();
 }
}
main().catch(error=>{console.error(error);process.exitCode=1;ws.close();});

}
start().catch(error=>{console.error(error);process.exitCode=1;});
