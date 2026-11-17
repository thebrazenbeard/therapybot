/* Firefox WebDriver BiDi, no dependencies; isolated local browser and loopback server. */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const browserPort = Number(process.argv[2] || 43324);
const url = process.argv[3] || 'http://127.0.0.1:43325/index.html';
const receipt = process.argv[4] || null;
const requests = [];
const errors = [];
const ws = new WebSocket('ws://127.0.0.1:' + browserPort + '/session');
const pending = new Map();
let nextId = 0;
ws.addEventListener('message',event=>{
 const message = JSON.parse(String(event.data));
 if (typeof message.id === 'number') {
  const resolver=pending.get(message.id);
  if(resolver){pending.delete(message.id);message.type==='error'?resolver.reject(Error(message.error+': '+message.message)):resolver.resolve(message.result);}
 } else if(message.method==='network.beforeRequestSent') {
  requests.push(message.params.request.url);
 } else if(message.method==='log.entryAdded' && message.params.level==='error') {
  errors.push(message.params.text);
 }
});
async function rpc(method,params={}){
 const id=++nextId;
 const promise=new Promise((resolve,reject)=>pending.set(id,{resolve,reject}));
 ws.send(JSON.stringify({id,method,params}));
 return Promise.race([promise,new Promise((_,reject)=>setTimeout(()=>reject(Error(method+' timeout')),15000))]);
}
async function main(){
 await new Promise((resolve,reject)=>{
  ws.addEventListener('open',resolve,{once:true});
  ws.addEventListener('error',reject,{once:true});
 });
 try{
  const session=await rpc('session.new',{capabilities:{alwaysMatch:{browserName:'firefox'}}});
  assert.equal(session.capabilities.browserName,'firefox');
  const tree=await rpc('browsingContext.getTree',{});
  const context=tree.contexts.find(x=>x.parent===null).context;
  await rpc('session.subscribe',{events:['network.beforeRequestSent','log.entryAdded']});
  await rpc('browsingContext.navigate',{context,url,wait:'complete'});
  async function evalJs(expression){
   const value=await rpc('script.evaluate',{expression,target:{context},awaitPromise:true,resultOwnership:'none'});
   if(value.type!=='success')throw Error('script.evaluate failed: '+JSON.stringify(value));
   return value.result.value;
  }
  async function keys(chars){
   const actions=[];
   for(const c of chars){actions.push({type:'keyDown',value:c},{type:'keyUp',value:c});}
   await rpc('input.performActions',{context,actions:[{type:'key',id:'keyboard',actions}]});
  }
  async function ctrlEnter() {
   await rpc('input.performActions',{context,actions:[{type:'key',id:'keyboard',actions:[
    {type:'keyDown',value:'\uE009'},{type:'keyDown',value:'\uE007'},
    {type:'keyUp',value:'\uE007'},{type:'keyUp',value:'\uE009'}
   ]}]});
  }
  async function waitCount(expected) {
   for(let i=0;i<50;i++){
    if(await evalJs("document.querySelectorAll('.message').length")===expected)return;
    await new Promise(r=>setTimeout(r,120));
   }
   throw Error('Expected '+expected+' chat messages');
  }
  await waitCount(1);
  assert.equal(await evalJs("document.getElementById('status').textContent.includes('Rules-only')"),true);
  assert.equal(await evalJs("document.activeElement.id"),'message');
  await keys('my boss refuses reimbursement'.split(''));
  await ctrlEnter();
  await waitCount(3);
  const first=await evalJs("document.querySelectorAll('.assistant-message')[1].textContent");
  assert.ok(first.length>55);
  assert.ok(!first.includes('my boss refuses reimbursement'));
  await evalJs("document.getElementById('message').focus()");
  await keys('i might lose my job'.split(''));
  await ctrlEnter();
  await waitCount(5);
  const second=await evalJs("document.querySelectorAll('.assistant-message')[2].textContent");
  assert.notEqual(first,second);
  await evalJs("document.getElementById('message').focus()");
  await keys(['\uE004']);
  assert.equal(await evalJs("document.activeElement.id"),'send');
  await evalJs("document.getElementById('message').focus()");
  for(let i=0;i<2;i++) {
   await rpc('input.performActions',{context,actions:[{type:'key',id:'keyboard',actions:[
    {type:'keyDown',value:'\uE008'},{type:'keyDown',value:'\uE004'},
    {type:'keyUp',value:'\uE004'},{type:'keyUp',value:'\uE008'}
   ]}]});
  }
  assert.equal(await evalJs("document.activeElement.id"),'clear');
  await keys(['\uE007']);
  await waitCount(1);
  assert.equal(await evalJs("document.activeElement.id"),'message');
  await keys('i am in immediate danger'.split(''));
  await ctrlEnter();
  await waitCount(3);
  const urgent = await evalJs("document.querySelectorAll('.assistant-message')[1].textContent");
  assert.ok(urgent.includes('emergency services') && urgent.includes('911'));
  await keys('stop'.split(''));
  await ctrlEnter();
  await waitCount(5);
  const stop = await evalJs("document.querySelectorAll('.assistant-message')[2].textContent");
  assert.ok(stop.includes('Replies paused'));
  assert.equal(await evalJs("document.getElementById('pause').getAttribute('aria-pressed')"),'true');
  assert.equal(await evalJs("document.getElementById('send').disabled"),true);
  const local=new URL(url).origin+'/';
  const outside=requests.filter(x=>!x.startsWith(local)&&!x.startsWith('data:'));
  assert.deepEqual(outside,[]);
  const image=await rpc('browsingContext.captureScreenshot',{context,origin:'viewport'});
  if(receipt)fs.writeFileSync(receipt,Buffer.from(image.data,'base64'));
  console.log(JSON.stringify({
   browser:'Firefox '+session.capabilities.browserVersion+' WebDriver BiDi',
   url,requests,outsidePageRequests:outside.length,consoleErrors:errors,
   firstReplyLength:first.length,secondReplyLength:second.length,urgentReplyLength:urgent.length,stopReplyLength:stop.length,
   assertions:['ready','textarea focus','actual character-key input','Ctrl+Enter 2 turns','distinct non-echo replies','Tab->Send','Enter->Clear','focus restored','explicit danger help','stop honored','no outbound requests']
  },null,2));
 } finally{
  try{await rpc('session.end',{});}catch(_){}
  ws.close();
 }
}
main().catch(error=>{console.error(error);process.exitCode=1;ws.close();});
