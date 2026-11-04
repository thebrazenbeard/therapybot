'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');

function loadAdapter() {
  const root = { AbortController, setTimeout, clearTimeout };
  root.window = root;
  vm.createContext(root);
  vm.runInContext(fs.readFileSync(path.join(__dirname, '../embedded/conversation_adapter.js'), 'utf8'), root);
  return root.TherapyBotConversationAdapter;
}

function localProvider(respond = () => ({ reply: 'Synthetic response.', safety: { route: 'normal' } })) {
  return { id: 'semantic', kind: 'bounded-semantic', execution: 'browser-local', respond };
}

test('registered semantic engine handles multi-turn memory only through explicit history', async () => {
  const observed = [];
  const session = loadAdapter().createSession({
    providers: [localProvider(({ message, history }) => {
      observed.push({ message, history: JSON.parse(JSON.stringify(history)) });
      return { reply: `Reply to ${message}`, engine: 'untrusted-provider-claimed-id', safety: { route: 'normal' } };
    })], defaultProviderId: 'semantic'
  });
  assert.equal((await session.turn({ message: 'Question one' })).status, 'ok');
  assert.equal((await session.turn({ message: 'Question two' })).status, 'ok');
  assert.equal(observed[0].history.length, 0);
  assert.equal(observed[1].history.length, 2);
  assert.equal(observed[1].history[0].content, 'Question one');
  assert.equal(session.snapshot().length, 4);
  assert.equal((await session.turn({ message: 'Third' })).providerId, 'semantic');
  session.clear();
  assert.deepEqual(Array.from(session.snapshot()), []);
  assert.deepEqual(Array.from(session.registeredProviders()), ['semantic']);
});

test('no engine, unknown engine, invalid input and unknown mode fail without fallback', async () => {
  const empty = loadAdapter().createSession({ providers: [] });
  assert.equal((await empty.turn({ message: 'Hello' })).status, 'unavailable');
  const session = loadAdapter().createSession({ providers: [localProvider()], defaultProviderId: 'semantic' });
  assert.equal((await session.turn({ message: 'Hello', providerId: 'cloud-api' })).status, 'unavailable');
  assert.equal((await session.turn({ message: ' ' })).status, 'invalid');
  assert.equal((await session.turn({ message: 'Hello', mode: 'unsupported' })).status, 'invalid');
  assert.deepEqual(Array.from(session.snapshot()), []);
});

test('rejects provider declarations that masquerade as local without meeting contract', () => {
  const create = loadAdapter().createSession;
  assert.throws(() => create({ providers: [{ id: 'remote', kind: 'in-browser-neural', execution: 'remote', respond() {} }] }), /Invalid/);
  assert.throws(() => create({ providers: [localProvider(), localProvider()] }), /duplicate/);
  assert.throws(() => create({ providers: [localProvider()], defaultProviderId: 'phantom' }), /explicitly registered/);
});

test('neural candidate is not called without an output gate', async () => {
  let calls = 0;
  const session = loadAdapter().createSession({
    providers: [{ id: 'local-neural', kind: 'in-browser-neural', execution: 'browser-local', respond() { calls++; return { reply: 'text' }; } }],
    defaultProviderId: 'local-neural'
  });
  const result = await session.turn({ message: 'Hello' });
  assert.equal(result.status, 'unavailable');
  assert.equal(calls, 0);
  assert.deepEqual(Array.from(session.snapshot()), []);
});

test('explicit experimental output gate can suppress or permit, but never claims clinical qualification', async () => {
  const neural = { id: 'local-neural', kind: 'in-browser-neural', execution: 'browser-local',
    respond: () => ({ reply: 'Synthetic model completion', safety: { route: 'normal' } }) };
  const blocked = loadAdapter().createSession({ providers: [neural], defaultProviderId: 'local-neural',
    outputGate: () => ({ allow: false }) });
  assert.equal((await blocked.turn({ message: 'Prompt' })).status, 'suppressed');
  assert.deepEqual(Array.from(blocked.snapshot()), []);
  const allowed = loadAdapter().createSession({ providers: [neural], defaultProviderId: 'local-neural',
    outputGate: () => ({ allow: true }) });
  const result = await allowed.turn({ message: 'Prompt' });
  assert.equal(result.status, 'ok');
  assert.equal(result.kind, 'in-browser-neural');
  assert.equal(result.clinicalQualification, 'none');
  assert.equal(result.outputGateQualification, 'unspecified-experimental');
  assert.equal(result.safety.route, 'unknown');
  assert.equal(result.providerNetworkVerified, false);
  assert.equal(result.providerStorageVerified, false);
  assert.equal(result.sourceClaimsVerified, false);
});

test('Council is a separately selected simulation and detected concern vetoes its invocation', async () => {
  let councilCalls = 0;
  const council = { respond({ baseResult, members }) {
    councilCalls++;
    assert.equal(members[0].name, 'Skeptic');
    return { ...baseResult, reply: 'Synthetic Skeptic reflection', state: { councilMode: 'council', topic: 'inner-council' } };
  } };
  const normal = loadAdapter().createSession({ providers: [localProvider()], defaultProviderId: 'semantic', council });
  const councilResult = await normal.turn({ message: 'How should I weigh this?', mode: 'council', members: [{ name: 'Skeptic' }] });
  assert.equal(councilResult.status, 'ok');
  assert.equal(councilResult.modeApplied, 'council');
  assert.equal(councilCalls, 1);
  const concerned = loadAdapter().createSession({ providers: [localProvider(() => ({ reply: 'Static cautious route', safety: { route: 'concern' } }))], defaultProviderId: 'semantic', council });
  const riskResult = await concerned.turn({ message: 'SYNTHETIC_RISK_CANARY', mode: 'council', members: [{ name: 'Skeptic' }] });
  assert.equal(riskResult.reply, 'Static cautious route');
  assert.equal(riskResult.modeApplied, 'direct');
  assert.equal(councilCalls, 1);
});

test('neural Council request is explicitly unavailable before model call instead of silently becoming direct chat', async () => {
  let councilCalls = 0;
  let neuralCalls = 0;
  const session = loadAdapter().createSession({
    providers: [{ id: 'neural', kind: 'in-browser-neural', execution: 'browser-local', respond: () => { neuralCalls++; return { reply: 'Synthetic answer', safety: { route: 'normal' } }; } }],
    defaultProviderId: 'neural', outputGate: () => ({ allow: true }),
    council: { respond: () => { councilCalls++; return { reply: 'Fake Council' }; } }
  });
  const result = await session.turn({ message: 'Synthetic ask', mode: 'council', members: [{ name: 'Skeptic' }] });
  assert.equal(result.status, 'unavailable');
  assert.match(result.reason, /no silent direct-chat/);
  assert.equal(neuralCalls, 0);
  assert.equal(councilCalls, 0);
  assert.equal(session.snapshot().length, 0);
});

test('source pointers are bounded identifiers, not verified citations', async () => {
  const session = loadAdapter().createSession({ providers: [localProvider(() => ({
    reply: 'Original synthetic answer', safety: { route: 'normal' },
    sources: ['nimh', { id: 'cdc' }, { id: 'cdc' }, { id: 'javascript:alert(1)' }, { id: 'X HTML' }]
  }))], defaultProviderId: 'semantic' });
  const result = await session.turn({ message: 'How does it work?' });
  assert.equal(result.sourceRelation, 'background-reading-not-reply-verification');
  assert.deepEqual(Array.from(result.sourceIds), ['nimh', 'cdc']);
});

test('clear aborts pending provider and no late result mutates new conversation', async () => {
  let resolveLate;
  let started;
  const startedPromise = new Promise((resolve) => { started = resolve; });
  const session = loadAdapter().createSession({ providers: [localProvider(() => {
    started();
    return new Promise((resolve) => { resolveLate = resolve; });
  })], defaultProviderId: 'semantic' });
  const pending = session.turn({ message: 'Old question' });
  await startedPromise;
  session.clear();
  const canceled = await pending;
  assert.equal(canceled.status, 'canceled');
  resolveLate({ reply: 'Old late response', safety: { route: 'normal' } });
  await Promise.resolve();
  assert.deepEqual(Array.from(session.snapshot()), []);
});

test('external abort resolves even if provider never cooperates', async () => {
  let started;
  const ready = new Promise((resolve) => { started = resolve; });
  const session = loadAdapter().createSession({ providers: [localProvider(() => { started(); return new Promise(() => {}); })], defaultProviderId: 'semantic' });
  const controller = new AbortController();
  const pending = session.turn({ message: 'Cancel me', signal: controller.signal });
  await ready;
  controller.abort();
  assert.equal((await pending).status, 'canceled');
  assert.deepEqual(Array.from(session.snapshot()), []);
});

test('timeout resolves and rejects a stale reply without transcript write', async () => {
  const session = loadAdapter().createSession({ providers: [localProvider(() => new Promise(() => {}))], defaultProviderId: 'semantic' });
  const result = await session.turn({ message: 'Timeout example', timeoutMs: 10 });
  assert.equal(result.status, 'timed_out');
  assert.deepEqual(Array.from(session.snapshot()), []);
});

test('timeout also interrupts an uncooperative neural output gate', async () => {
  const session = loadAdapter().createSession({
    providers: [{ id: 'neural', kind: 'in-browser-neural', execution: 'browser-local', respond: () => ({ reply: 'Synthetic answer' }) }],
    defaultProviderId: 'neural', outputGate: () => new Promise(() => {})
  });
  const result = await session.turn({ message: 'Synthetic prompt', timeoutMs: 10 });
  assert.equal(result.status, 'timed_out');
  assert.equal(session.snapshot().length, 0);
});

test('clear also interrupts an uncooperative Council without accepting a late reply', async () => {
  let councilStarted;
  const ready = new Promise((resolve) => { councilStarted = resolve; });
  const session = loadAdapter().createSession({
    providers: [localProvider()], defaultProviderId: 'semantic',
    council: { respond: () => { councilStarted(); return new Promise(() => {}); } }
  });
  const pending = session.turn({ message: 'Council: Synthetic dilemma', mode: 'council', members: [{ name: 'Skeptic' }] });
  await ready;
  session.clear();
  assert.equal((await pending).status, 'canceled');
  assert.equal(session.snapshot().length, 0);
});

test('second concurrent turn is busy, and malformed result does not persist', async () => {
  let resolveLate;
  let started;
  const ready = new Promise((resolve) => { started = resolve; });
  const session = loadAdapter().createSession({ providers: [localProvider(() => {
    started();
    return new Promise((resolve) => { resolveLate = resolve; });
  })], defaultProviderId: 'semantic' });
  const pending = session.turn({ message: 'First' });
  await ready;
  assert.equal((await session.turn({ message: 'Second' })).status, 'busy');
  resolveLate({ nope: true });
  assert.equal((await pending).status, 'error');
  assert.deepEqual(Array.from(session.snapshot()), []);
});

test('disposed session refuses all turns', async () => {
  const session = loadAdapter().createSession({ providers: [localProvider()], defaultProviderId: 'semantic' });
  session.dispose();
  assert.equal((await session.turn({ message: 'Hello' })).status, 'unavailable');
});

test('real PR11 embedded semantic and Inner Council objects satisfy the adapter seam', async () => {
  const root = { AbortController, setTimeout, clearTimeout };
  root.window = root;
  vm.createContext(root);
  const sourceDir = path.resolve(__dirname, '../embedded');
  for (const file of ['catalog.js', 'engine.js', 'council.js']) {
    vm.runInContext(fs.readFileSync(path.join(sourceDir, file), 'utf8'), root);
  }
  vm.runInContext(fs.readFileSync(path.join(__dirname, '../embedded/conversation_adapter.js'), 'utf8'), root);
  const session = root.TherapyBotConversationAdapter.createSession({
    providers: [{
      id: 'embedded-semantic', kind: 'bounded-semantic', execution: 'browser-local',
      respond: root.TherapyBotEmbedded.respond
    }], defaultProviderId: 'embedded-semantic', council: root.TherapyBotCouncil
  });
  const direct = await session.turn({ message: 'At work I have an unresolved expense.' });
  assert.equal(direct.status, 'ok');
  assert.equal(direct.providerId, 'embedded-semantic');
  const council = await session.turn({
    message: 'Council: I need to decide what to say to my boss.', mode: 'council',
    members: [
      { name: 'Skeptic', role: 'Look for unsupported assumptions', focus: 'Evidence' },
      { name: 'Protector', role: 'Protect boundaries', focus: 'Practical risk' }
    ]
  });
  assert.equal(council.status, 'ok');
  assert.equal(council.modeApplied, 'council');
  assert.equal(council.presentation.councilMode, 'council');
  assert.equal(council.presentation.speakers.length, 2);
  assert.match(council.reply, /Skeptic/);
  assert.match(council.reply, /Protector/);
  assert.equal(session.snapshot().length, 4);
});
