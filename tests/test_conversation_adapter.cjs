'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');

function loadAdapter(residentRespond = () => ({ reply: 'Synthetic resident baseline.', safety: { route: 'normal' } })) {
  const root = { AbortController, setTimeout, clearTimeout };
  root.window = root;
  root.TherapyBotEmbedded = { respond: residentRespond };
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
  assert.equal(result.responseOrigin, 'selected-provider');
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
  assert.equal(riskResult.safety.route, 'concern');
  assert.match(riskResult.reply, /provider flagged a possible concern/i);
  assert.doesNotMatch(riskResult.reply, /Static cautious route/);
  assert.equal(riskResult.modeApplied, 'direct');
  assert.equal(councilCalls, 1);
});

test('missing Council safety metadata cannot silently inherit a normal route', async () => {
  const council = { respond({ baseResult }) {
    return { ...baseResult, reply: 'Synthetic abstention', safety: null, supportedTopic: false };
  } };
  const session = loadAdapter().createSession({ providers: [localProvider()], defaultProviderId: 'semantic', council });
  const answer = await session.turn({ message: 'Synthetic question', mode: 'council', members: [{ name: 'Lens' }] });
  assert.equal(answer.status, 'ok');
  assert.equal(answer.safety.route, 'unknown');
  assert.equal(answer.presentation.supportedTopic, false);
});

test('adapter preserves opaque Unicode speaker IDs without converting authored labels into engine speech', async () => {
  const council = { respond({ baseResult }) {
    return {
      ...baseResult,
      reply: 'Perspective 1: Synthetic question.',
      speakers: [{ id: 'réflexion-é', name: 'Perspective 1', role: 'Reflective lens', text: 'Synthetic question.' }],
      state: { councilMode: 'solo', topic: 'work' }
    };
  } };
  const session = loadAdapter().createSession({ providers: [localProvider()], defaultProviderId: 'semantic', council });
  const result = await session.turn({ message: 'What is the next question?', mode: 'solo', members: [{ id: 'réflexion-é', name: 'Évidence' }] });
  assert.equal(result.status, 'ok');
  assert.equal(result.presentation.speakers[0].id, 'réflexion-é');
  assert.equal(result.presentation.speakers[0].name, 'Perspective 1');
  assert.doesNotMatch(result.reply, /Évidence/);
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

test('direct semantic provider cannot forge normal over independently detected urgent danger', async () => {
  const root = { AbortController, setTimeout, clearTimeout };
  root.window = root;
  vm.createContext(root);
  const dir = path.resolve(__dirname, '../embedded');
  for (const file of ['catalog.js', 'engine.js', 'conversation_adapter.js']) {
    vm.runInContext(fs.readFileSync(path.join(dir, file), 'utf8'), root);
  }
  const message = 'I am going to kill myself tonight.';
  const independent = root.TherapyBotEmbedded.respond({ message, history: [] });
  assert.equal(independent.safety.route, 'urgent_review');
  let providerCalls = 0;
  const session = root.TherapyBotConversationAdapter.createSession({
    providers: [localProvider(() => {
      providerCalls++;
      return { reply: 'FORGED_NORMAL_PROVIDER_TEXT', safety: { route: 'normal' }, supportedTopic: true };
    })], defaultProviderId: 'semantic'
  });
  const result = await session.turn({ message });
  assert.equal(result.status, 'ok');
  assert.equal(result.safety.route, 'urgent_review');
  assert.equal(result.reply, independent.reply);
  assert.equal(result.responseOrigin, 'resident-safety');
  assert.doesNotMatch(result.reply, /FORGED_NORMAL_PROVIDER_TEXT/);
  assert.equal(providerCalls, 0);
});

test('untrusted direct safety labels cannot inject warning prose or weaken resident concern', async () => {
  const concerned = loadAdapter(() => ({ reply: 'RESIDENT_CONCERN', safety: { route: 'concern' } })).createSession({
    providers: [localProvider(() => ({ reply: 'FORGED_SAFE_TEXT', safety: { route: 'normal' } }))],
    defaultProviderId: 'semantic'
  });
  const first = await concerned.turn({ message: 'A synthetic concern.' });
  assert.equal(first.safety.route, 'concern');
  assert.equal(first.reply, 'RESIDENT_CONCERN');
  const elevated = loadAdapter().createSession({
    providers: [localProvider(() => ({ reply: 'ATTACKER_URGENT_TEXT', safety: { route: 'urgent_review' } }))],
    defaultProviderId: 'semantic'
  });
  const second = await elevated.turn({ message: 'An ordinary question.' });
  assert.equal(second.safety.route, 'urgent_review');
  assert.equal(second.responseOrigin, 'provider-warning-veto');
  assert.doesNotMatch(second.reply, /ATTACKER_URGENT_TEXT/);
  assert.match(second.reply, /unverified|cannot assess|emergency/i);
});

test('missing resident safety guard fails closed and does not invoke the provider', async () => {
  const session = loadAdapter(() => null).createSession({
    providers: [localProvider(() => ({ reply: 'UNSAFE_UNCHECKED', safety: { route: 'normal' } }))],
    defaultProviderId: 'semantic'
  });
  const response = await session.turn({ message: 'Question.' });
  assert.equal(response.status, 'unavailable');
  assert.deepEqual(Array.from(session.snapshot()), []);
});

test('neural output gate cannot override an independent urgent resident response', async () => {
  let neuralCalls = 0;
  let gateCalls = 0;
  const session = loadAdapter(() => ({
    reply: 'RESIDENT_URGENT_TEXT', safety: { route: 'urgent_review' }
  })).createSession({
    providers: [{ id: 'neural', kind: 'in-browser-neural', execution: 'browser-local',
      respond: () => { neuralCalls++; return { reply: 'FORGED_NEURAL', safety: { route: 'normal' } }; } }],
    defaultProviderId: 'neural', outputGate: () => { gateCalls++; return { allow: true }; }
  });
  const response = await session.turn({ message: 'Synthetic urgent danger.' });
  assert.equal(response.status, 'ok');
  assert.equal(response.safety.route, 'urgent_review');
  assert.equal(response.reply, 'RESIDENT_URGENT_TEXT');
  assert.equal(neuralCalls, 0);
  assert.equal(gateCalls, 0);
});

test('resident acute cue vetoes Council even when the optional provider claims normal', async () => {
  let providerCalls = 0;
  let councilCalls = 0;
  const session = loadAdapter(() => ({ reply: 'RESIDENT_EMERGENCY', safety: { route: 'urgent_review' } })).createSession({
    providers: [localProvider(() => { providerCalls++; return { reply: 'FORGED_NORMAL', safety: { route: 'normal' } }; })],
    defaultProviderId: 'semantic',
    council: { respond: () => { councilCalls++; return { reply: 'FORGED_COUNCIL' }; } }
  });
  const answer = await session.turn({ message: 'Council: Synthetic immediate danger.', mode: 'council', members: [{ name: 'Lens' }] });
  assert.equal(answer.status, 'ok');
  assert.equal(answer.safety.route, 'urgent_review');
  assert.equal(answer.reply, 'RESIDENT_EMERGENCY');
  assert.equal(answer.modeApplied, 'direct');
  assert.equal(providerCalls, 0);
  assert.equal(councilCalls, 0);
});

test('a pending independent resident check is cancelable without provider or history writes', async () => {
  let providerCalls = 0;
  const session = loadAdapter(() => new Promise(() => {})).createSession({
    providers: [localProvider(() => { providerCalls++; return { reply: 'FORGED_NORMAL', safety: { route: 'normal' } }; })],
    defaultProviderId: 'semantic'
  });
  const result = await session.turn({ message: 'A synthetic delay.', timeoutMs: 10 });
  assert.equal(result.status, 'timed_out');
  assert.equal(providerCalls, 0);
  assert.deepEqual(Array.from(session.snapshot()), []);
});

test('malformed provider safety route is unknown with no injected prose or false clearance', async () => {
  const session = loadAdapter().createSession({
    providers: [localProvider(() => ({ reply: 'ATTACKER_MALFORMED_TEXT', safety: { route: 'all_clear' },
      sources: ['bogus-source'], supportedTopic: true }))],
    defaultProviderId: 'semantic'
  });
  const result = await session.turn({ message: 'Ordinary hypothetical.' });
  assert.equal(result.status, 'ok');
  assert.equal(result.safety.route, 'unknown');
  assert.equal(result.responseOrigin, 'provider-warning-veto');
  assert.equal(result.presentation.supportedTopic, false);
  assert.deepEqual(Array.from(result.sourceIds), []);
  assert.doesNotMatch(result.reply, /ATTACKER_MALFORMED_TEXT/);
});

test('resident and bounded provider both normal preserve ordinary direct conversation', async () => {
  const session = loadAdapter().createSession({
    providers: [localProvider()], defaultProviderId: 'semantic'
  });
  const result = await session.turn({ message: 'Ordinary synthetic question.' });
  assert.equal(result.status, 'ok');
  assert.equal(result.safety.route, 'normal');
  assert.equal(result.responseOrigin, 'selected-provider');
  assert.equal(result.reply, 'Synthetic response.');
});

test('resident function captured at session creation resists later global replacement', async () => {
  const root = { AbortController, setTimeout, clearTimeout };
  root.window = root;
  root.TherapyBotEmbedded = { respond: () => ({
    reply: 'CAPTURED_RESIDENT_URGENT', safety: { route: 'urgent_review' }
  }) };
  vm.createContext(root);
  vm.runInContext(fs.readFileSync(path.join(__dirname, '../embedded/conversation_adapter.js'), 'utf8'), root);
  const session = root.TherapyBotConversationAdapter.createSession({
    providers: [localProvider(() => ({ reply: 'FORGED_NORMAL', safety: { route: 'normal' } }))],
    defaultProviderId: 'semantic'
  });
  root.TherapyBotEmbedded.respond = () => ({ reply: 'LATE_FORGED_SAFE', safety: { route: 'normal' } });
  const result = await session.turn({ message: 'Synthetic urgency.' });
  assert.equal(result.safety.route, 'urgent_review');
  assert.equal(result.reply, 'CAPTURED_RESIDENT_URGENT');
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
  assert.match(council.reply, /Perspective 1/);
  assert.match(council.reply, /Perspective 2/);
  assert.deepEqual(Array.from(council.presentation.speakers, speaker => speaker.id), [
    'skeptic', 'protector'
  ]);
  assert.doesNotMatch(council.reply, /Skeptic|Protector/);
  assert.equal(session.snapshot().length, 4);
  const unsupported = await session.turn({
    message: 'Council: qwerty unknown situation xyz', mode: 'council',
    members: [{ name: 'Skeptic', role: 'Check evidence' }]
  });
  assert.equal(unsupported.status, 'ok');
  assert.equal(unsupported.presentation.speakers.length, 0);
  assert.equal(unsupported.safety.route, 'unknown', 'Council abstention must retain the unvalidated unknown route');
  assert.equal(unsupported.presentation.supportedTopic, false);
});
