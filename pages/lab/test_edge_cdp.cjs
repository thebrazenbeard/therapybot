/* Isolated Edge/CDP visitor proof. Requires an already-running private browser and server. */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const port = Number(process.argv[2] || 43322);
const url = process.argv[3] || 'http://127.0.0.1:43321/index.html';
async function main() {
const targets = await fetch('http://127.0.0.1:' + port + '/json/list').then(r => r.json());
const page = targets.find(t => t.type === 'page' && t.webSocketDebuggerUrl);
assert.ok(page, 'No isolated Edge page target found');
const ws = new WebSocket(page.webSocketDebuggerUrl);
const pending = new Map();
const requests = [];
const exceptions = [];
let sequence = 0;
ws.addEventListener('message', event => {
  const payload = JSON.parse(String(event.data));
  if (payload.id) {
    const item = pending.get(payload.id);
    if (item) {
      pending.delete(payload.id);
      payload.error ? item.reject(Error(JSON.stringify(payload.error))) : item.resolve(payload.result);
    }
  } else if (payload.method === 'Network.requestWillBeSent') {
    requests.push(payload.params.request.url);
  } else if (payload.method === 'Runtime.exceptionThrown') {
    exceptions.push(payload.params.exceptionDetails.text);
  }
});
await new Promise((resolve,reject) => {
  ws.addEventListener('open',resolve,{once:true});
  ws.addEventListener('error',reject,{once:true});
});
async function cdp(method, params={}) {
  const id = ++sequence;
  const answer = new Promise((resolve,reject) => pending.set(id,{resolve,reject}));
  ws.send(JSON.stringify({id,method,params}));
  return await Promise.race([answer,new Promise((_,reject) => setTimeout(() => reject(Error('CDP timeout '+method)),15000))]);
}
async function inspect(expression) {
  const response = await cdp('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});
  if(response.exceptionDetails) throw Error(response.exceptionDetails.text);
  return response.result.value;
}
async function key(key, modifiers=0) {
  const code = key === ' ' ? 'Space' : key;
  const virtualCode = key === 'Tab' ? 9 : key === ' ' ? 32 : 13;
  const payload={key,code,modifiers,windowsVirtualKeyCode:virtualCode,nativeVirtualKeyCode:virtualCode};
  await cdp('Input.dispatchKeyEvent',{...payload,type:'keyDown'});
  await cdp('Input.dispatchKeyEvent',{...payload,type:'keyUp'});
}
async function count(n) {
  for(let i=0;i<50;i++){
    if(await inspect("document.querySelectorAll('.message').length")===n)return;
    await new Promise(r=>setTimeout(r,120));
  }
  throw Error('Expected '+n+' messages');
}
try{
  await cdp('Network.enable');
  await cdp('Page.enable');
  await cdp('Runtime.enable');
  await cdp('Page.navigate',{url});
  await count(1);
  assert.equal(await inspect("document.getElementById('status').textContent.includes('Rules-only')"),true);
  assert.equal(await inspect('document.activeElement.id'),'message');
  await cdp('Input.insertText',{text:'My supervisor will not reimburse gasoline for the work truck.'});
  await key('Enter',2);
  await count(3);
  const first=await inspect("document.querySelectorAll('.assistant-message')[1].innerText");
  assert.ok(first.length>55);
  assert.ok(!first.includes('My supervisor will not reimburse gasoline for the work truck.'),'Echo-only response');
  await inspect("document.getElementById('message').focus()");
  await cdp('Input.insertText',{text:'I feel trapped because I might lose my job.'});
  await key('Enter',2);
  await count(5);
  const second=await inspect("document.querySelectorAll('.assistant-message')[2].innerText");
  assert.ok(second.length>55);
  assert.notEqual(second,first,'Same response to distinct inputs');
  await inspect("document.getElementById('message').focus()");
  await key('Tab');
  assert.equal(await inspect('document.activeElement.id'),'send');
  await inspect("document.getElementById('clear').focus()");
  assert.equal(await inspect('document.activeElement.id'),'clear');
  await key(' ');
  await count(1);
  assert.equal(await inspect('document.activeElement.id'),'message');
  await cdp('Input.insertText',{text:'i am in immediate danger'});
  await key('Enter',2);
  await count(3);
  const urgent = await inspect("document.querySelectorAll('.assistant-message')[1].textContent");
  assert.ok(urgent.includes('emergency services') && urgent.includes('911'));
  await cdp('Input.insertText',{text:'stop'});
  await key('Enter',2);
  await count(5);
  const stop = await inspect("document.querySelectorAll('.assistant-message')[2].textContent");
  assert.ok(stop.includes('Replies paused'));
  assert.equal(await inspect("document.getElementById('pause').getAttribute('aria-pressed')"),'true');
  assert.equal(await inspect("document.getElementById('send').disabled"),true);
  await inspect("document.getElementById('clear').click()");
  await count(1);
  await cdp('Input.insertText',{text:'A character says I might harm myself in my novel.'});
  await key('Enter',2);
  await count(3);
  const hypothetical = await inspect("document.querySelectorAll('.assistant-message')[1].textContent");
  assert.ok(hypothetical.includes('fictional or hypothetical') && !hypothetical.includes('911'));
  await inspect("document.getElementById('clear').click()");
  await count(1);
  await cdp('Input.insertText',{text:"my roommate took pills and isn't responding"});
  await key('Enter',2);
  await count(3);
  const thirdParty = await inspect("document.querySelectorAll('.assistant-message')[1].textContent");
  assert.ok(thirdParty.includes('emergency services'));
  await cdp('Input.insertText',{text:'i might do it now'});
  await key('Enter',2);
  await count(5);
  const contextual = await inspect("document.querySelectorAll('.assistant-message')[2].textContent");
  assert.ok(contextual.includes('emergency services'));
  await cdp('Input.insertText',{text:'i need to stop now'});
  await key('Enter',2);
  await count(7);
  assert.equal(await inspect("document.getElementById('pause').getAttribute('aria-pressed')"), 'true');
  const localOrigin = new URL(url).origin + '/';
  const outside=requests.filter(x => !x.startsWith(localOrigin) && !x.startsWith('data:'));
  assert.deepEqual(outside,[],'Unexpected outbound page request');
  assert.deepEqual(exceptions,[],'Runtime exception');
  const screenshot=await cdp('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});
  const receipt=process.argv[4];
  if(receipt)fs.writeFileSync(receipt,Buffer.from(screenshot.data,'base64'));
  console.log(JSON.stringify({
    browser:'Edge isolated CDP',url,requests,
    outsidePageRequests:outside.length,jsExceptions:exceptions.length,
    firstReplyLength:first.length,secondReplyLength:second.length,urgentReplyLength:urgent.length,stopReplyLength:stop.length,
    assertions:['ready','textarea focus','Ctrl+Enter two user turns','answers distinct and not echo','Tab->Send','Space->Clear','focus restored','explicit danger help','stop honored','fictional framing','third-party acute support','risk-context continuation','natural stop','loopback-only requests']
  },null,2));
}finally{
  ws.close();
}

}
main().catch(error => { console.error(error); process.exitCode=1; });
