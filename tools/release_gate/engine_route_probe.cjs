'use strict';
// Separate source-executed corroboration: actual rules engine, no generic adapter stub.
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const engineFile=path.resolve(__dirname,'..','..','embedded','engine.js');
const fixturesFile=path.join(__dirname,'fixtures.json');

function runEngine(message) {
  const sandbox={window:{}};
  vm.runInNewContext(fs.readFileSync(engineFile,'utf8'),sandbox,
    {filename:'embedded/engine.js',timeout:1500});
  const engine=sandbox.window.TherapyBotEmbedded;
  if (typeof engine?.respond!=='function') throw new Error('Actual embedded engine missing');
  return engine.respond({message,history:[]});
}
function evaluate() {
  const fixtures=JSON.parse(fs.readFileSync(fixturesFile,'utf8')).cases;
  const selected=fixtures.filter(item=>item.domain==='third_party_acute'||
    item.domain==='self_acute'||item.domain==='fiction_only'||
    item.domain==='historical_only');
  const outcomes=selected.map(item=>{
    const response=runEngine(item.messages[0]);
    const route=response?.safety?.route||'MISSING_SAFETY_ROUTE';
    const observed=route==='urgent_review'?'urgent':'nonurgent';
    return {id:item.id,domain:item.domain,expected:item.expected,
      actualSourceRoute:route,observed,passes:observed===item.expected};
  });
  return {
    evidenceClass:'ACTUAL_EMBEDDED_ENGINE_SOURCE_EXECUTED_IN_NODE_VM',
    validation:'NO_BROWSER_OR_CLINICAL_VALIDATION',
    subject:'embedded/engine.js',
    total:outcomes.length,failed:outcomes.filter(item=>!item.passes).length,
    thirdPartySourceMisses:outcomes.filter(item=>item.domain==='third_party_acute'&&!item.passes).length,
    outcomes
  };
}
if (require.main===module) {
  try {
    const report=evaluate();
    console.log(JSON.stringify(report,null,2));
    if(process.argv.includes('--enforce')&&report.failed>0) process.exitCode=2;
  }catch(error) {console.error(error);process.exitCode=3;}
}
module.exports={evaluate,runEngine};
