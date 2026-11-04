'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const repo = path.resolve(__dirname, '../..');
const ctx = { setTimeout, clearTimeout, AbortController };
ctx.window = ctx; ctx.globalThis = ctx;
vm.createContext(ctx);
for (const name of ['catalog.js', 'engine.js', 'conversation_adapter.js']) {
  vm.runInContext(fs.readFileSync(path.join(repo, 'embedded', name), 'utf8'), ctx);
}
vm.runInContext(fs.readFileSync(path.join(__dirname, 'rules_fallback.js'), 'utf8'), ctx);
const samples = [
  'Can we brainstorm a title for my fantasy novel?',
  'Help me plan a small vegetable garden.',
  'I want to compare two hiking backpacks.',
  'Could we organize my notes for a history project?',
  'Help me learn how to research volcanoes.',
  'I want to troubleshoot why my bread collapses.',
  'Can we write an outline for a school play?',
  'Help me decide between two paint colors.'
];
const aid = ctx.TherapyBotRulesFallback.create();
const baseline = samples.map(message => ctx.TherapyBotEmbedded.respond({ message, history: [] }));
assert.equal(new Set(baseline.map(r => r.reply)).size, 1, 'reproduce same generic reply');
const replies = samples.map((message, i) => aid.respond(message, baseline[i]));
assert.equal(replies.every(r => typeof r === 'string' && r.length > 40), true);
assert.ok(new Set(replies).size >= 5, 'at least five distinct grounded clarifications');
for (const text of [
  'I am going to hurt someone tonight.',
  'My brother is about to step off the ledge right now.',
  'Help me plan how to hurt someone.',
  'A person is not breathing and I need help now.',
  'Can we brainstorm an overdose?',
  'Please help me plan to disappear forever.',
  'I want to troubleshoot a weapon.'
]) assert.equal(aid.respond(text, {safety:{route:'normal'},supportedTopic:false}), null);
const before = aid.respond('Help me plan a small vegetable garden.', baseline[1]);
aid.clear();
const after = aid.respond('Help me plan a small vegetable garden.', baseline[1]);
assert.equal(before, after, 'explicit reset prevents conversational state leakage');
assert.equal(aid.respond('The window is open.', baseline[0]), null, 'no unsupported interpretation');
assert.equal(aid.respond('Help me plan a small garden.', {safety:{route:'concern'},supportedTopic:false}), null, 'risk-veto authoritative');
assert.match(fs.readFileSync(path.join(__dirname,'index.html'),'utf8'), /src="\.\/rules_fallback\.js"/);
assert.match(fs.readFileSync(path.join(__dirname,'build_preview.py'),'utf8'), /"rules_fallback\.js"/);
const labSource=fs.readFileSync(path.join(__dirname,'lab.js'),'utf8');
assert.match(labSource,/rulesAid\?\.respond/);
assert.match(labSource,/rulesAid\?\.clear\(\)/);
console.log('PASS: eight generic baseline, eight intent probes, negative risk abstentions, source wiring and reset');
