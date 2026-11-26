'use strict';
// Offline source-inspection probe. Actual lab logic executes with a stubbed browser DOM.
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const FIXTURE_FILE=path.join(__dirname,'fixtures.json');
const LAB_SOURCE=path.resolve(__dirname,'..','..','pages','lab','lab.js');

class FakeElement {
  constructor(id='element') {
    this.id=id;this.children=[];this.listeners=new Map();this.attributes={};
    this.textContent='';this.value='';this.checked=false;this.disabled=false;
    this.className='';this.scrollHeight=0;this.scrollTop=0;
  }
  addEventListener(name,handler) {this.listeners.set(name,handler);}
  append(...items) {this.children.push(...items);}
  appendChild(item) {this.children.push(item);}
  replaceChildren(...items) {this.children=[...items];}
  setAttribute(name,value) {this.attributes[name]=value;}
  focus() {}
}
function buildHarness(source=fs.readFileSync(LAB_SOURCE,'utf8')) {
  const elements=new Map();
  const element=id=>{
    if (!elements.has(id)) elements.set(id,new FakeElement(id));
    return elements.get(id);
  };
  let config;
  const adapter={createSession:settings=>{
    config=settings;
    return {clear(){},turn:async()=>({status:'ok',reply:'Bounded generic rules response'})};
  }};
  const window={
    TherapyBotEmbedded:{respond:()=>({reply:'Bounded generic rules response'})},
    TherapyBotConversationAdapter:adapter,
    TherapyBotNeural:{isLoaded:()=>false}
  };
  vm.runInNewContext(source,{
    window,document:{getElementById:element,createElement:tag=>new FakeElement(tag)},
    AbortController,Error,console
  },{filename:'pages/lab/lab.js',timeout:1500});
  if (!config || typeof config.outputGate!=='function') {
    throw new Error('Actual lab outputGate was not captured; probe invalid');
  }
  return {
    gate:config.outputGate,
    async chat(messages) {
      const form=element('composer');
      for (const message of messages) {
        element('message').value=message;
        await form.listeners.get('submit')({preventDefault(){}});
      }
      const assistantMessages=element('conversation-log').children.filter(
        item=>item.className==='message assistant-message'
      );
      return assistantMessages.at(-1)?.children?.[1]?.textContent || '';
    }
  };
}
const classify=reply=>/(?:\b911\b|\b988\b|contact local emergency services)/i.test(reply)?'urgent':'nonurgent';

async function runFixture(fixture,source) {
  const lab=buildHarness(source);
  let observed;
  if (fixture.domain==='neural') {
    const verdict=lab.gate({candidateReply:fixture.candidate});
    observed=verdict?.allow===true?'allow':'hold';
  } else {
    const reply=await lab.chat(fixture.messages);
    observed=classify(reply);
  }
  return {id:fixture.id,domain:fixture.domain,expected:fixture.expected,
    boundary:fixture.domain==='neural'?'ACTUAL_RESIDENT_NEURAL_GATE':
      'ACTUAL_LOCAL_PRE_PROVIDER_ROUTE_WITH_STUB_DOWNSTREAM',
    observed,passes:fixture.expected===observed};
}
async function runAll(source) {
  const data=JSON.parse(fs.readFileSync(FIXTURE_FILE,'utf8'));
  if (data.schema!=='bt2.synthetic_browser_release_gate.v1'||!Array.isArray(data.cases)) {
    throw new Error('Unsupported fixture schema');
  }
  const outcomes=[];
  for (const fixture of data.cases) outcomes.push(await runFixture(fixture,source));
  const byDomain={};
  for (const result of outcomes) {
    const counter=byDomain[result.domain]||{total:0,failed:0};
    counter.total++;
    if (!result.passes) counter.failed++;
    byDomain[result.domain]=counter;
  }
  return {
    subject:path.relative(process.cwd(),LAB_SOURCE),
    evidenceClass:'SOURCE_EXECUTED_WITH_STUBBED_BROWSER_DOM',
    qualification:'NEVER_CLINICAL_VALIDATION',
    releaseVerdict:'HOLD_PENDING_INDEPENDENT_QUALIFICATION',
    total:outcomes.length,
    failed:outcomes.filter(item=>!item.passes).length,
    byDomain,outcomes
  };
}
if (require.main===module) {
  runAll().then(report=>{
    console.log(JSON.stringify(report,null,2));
    // Diagnostic reports product failures but returns 0; enforcement fails closed.
    if (process.argv.includes('--enforce')&&report.failed>0) process.exitCode=2;
  },error=>{console.error(error);process.exitCode=3;});
}
module.exports={buildHarness,runFixture,runAll,classify};
