'use strict';
/* Synthetic, newly selected conversational holdout; not a clinical evaluation. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const repo = path.resolve(__dirname, '../..');
const ctx = {setTimeout,clearTimeout,AbortController};
ctx.window = ctx; ctx.globalThis = ctx;
vm.createContext(ctx);
for (const file of ['catalog.js','engine.js','conversation_adapter.js'])
  vm.runInContext(fs.readFileSync(path.join(repo,'embedded',file),'utf8'),ctx);
vm.runInContext(fs.readFileSync(path.join(__dirname,'rules_fallback.js'),'utf8'),ctx);
const dialog = [
  'Could we brainstorm a balcony herb garden?',
  'There is very little sun.',
  'Can we compare indoor lights and moving the pots?',
  'I would rather avoid extra electricity.',
  'Can you help me plan the first week?',
  'What if I forget watering?',
  'Let us organize what I know.',
  'How would I choose a seed kit?'
];
async function main() {
  const session=ctx.TherapyBotConversationAdapter.createSession({
    providers:[{id:'embedded-semantic',kind:'bounded-semantic',execution:'browser-local',respond:ctx.TherapyBotEmbedded.respond}],
    defaultProviderId:'embedded-semantic'
  });
  const aid=ctx.TherapyBotRulesFallback.create();
  const original=[], observed=[];
  for(const message of dialog){
    const result=await session.turn({message,mode:'direct'});
    assert.equal(result.status,'ok');
    const scaffold=aid.respond(message,{safety:result.safety,supportedTopic:result.presentation.supportedTopic});
    original.push(result.reply);
    observed.push(scaffold || result.reply);
  }
  const originalUnique=new Set(original).size, newUnique=new Set(observed).size;
  const changed=observed.filter((reply,i)=>reply!==original[i]).length;
  console.log('HOLDOUt benign eight-turn distinct before='+originalUnique+' after='+newUnique+' changed='+changed+'/8');
  assert.equal(originalUnique,1);
  assert.equal(newUnique,5);
  assert.equal(changed,4);
}
main().catch(e=>{console.error(e);process.exitCode=1;});
