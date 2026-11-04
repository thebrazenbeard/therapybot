'use strict';
const assert=require('node:assert/strict');
const test=require('node:test');
const fs=require('node:fs');
const path=require('node:path');
const {buildHarness,runFixture,runAll,classify}=require('./probe.cjs');
const fixtures=JSON.parse(fs.readFileSync(path.join(__dirname,'fixtures.json'),'utf8'));

test('original synthetic fixtures have unique IDs, verdicts, required domains',()=>{
  const ids=fixtures.cases.map(item=>item.id);
  assert.equal(new Set(ids).size,ids.length);
  const domains=new Set(fixtures.cases.map(item=>item.domain));
  for (const domain of ['neural','third_party_acute','fiction_only','historical_only','self_acute']) {
    assert.equal(domains.has(domain),true);
  }
  for (const item of fixtures.cases) {
    assert.equal(['allow','hold','urgent','nonurgent'].includes(item.expected),true);
    assert.equal(typeof item.rationale,'string');
  }
});
test('probe captures real gate and drives actual local submit handler',async()=>{
  const lab=buildHarness();
  assert.equal(typeof lab.gate,'function');
  assert.equal(typeof await lab.chat(['I want to talk about plants.']),'string');
});
test('urgent classification observes an emergency contact signal only',()=>{
  assert.equal(classify('Contact local emergency services immediately.'),'urgent');
  assert.equal(classify('I might have misunderstood.'),'nonurgent');
});
test('positive-control danger and direct lexical block are recognized',async()=>{
  const positive=await runFixture(fixtures.cases.find(item=>item.id==='S01'));
  const lexical=await runFixture(fixtures.cases.find(item=>item.id==='N06'));
  assert.equal(positive.passes,true);
  assert.equal(lexical.passes,true);
});
test('reports present defects as failures without upgrading to qualification',async()=>{
  const report=await runAll();
  assert.equal(report.total,fixtures.cases.length);
  assert.equal(report.failed,report.outcomes.filter(item=>!item.passes).length);
  assert.equal(report.qualification,'NEVER_CLINICAL_VALIDATION');
  assert.equal(report.releaseVerdict,'HOLD_PENDING_INDEPENDENT_QUALIFICATION');
});

test('actual embedded engine safety routes are independently observed, without stub',()=>{
  const {evaluate}=require('./engine_route_probe.cjs');
  const report=evaluate();
  assert.equal(report.total,9);
  assert.equal(report.failed,report.outcomes.filter(item=>!item.passes).length);
  assert.equal(report.thirdPartySourceMisses,report.outcomes.filter(
    item=>item.domain==='third_party_acute'&&!item.passes).length);
  assert.equal(report.validation,'NO_BROWSER_OR_CLINICAL_VALIDATION');
});
