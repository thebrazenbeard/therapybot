/* Node-only source smoke: a real adapter turn, without visiting a public URL. */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const repo = path.resolve(__dirname, '../..');
const sandbox = { setTimeout, clearTimeout, AbortController };
sandbox.window = sandbox;
sandbox.globalThis = sandbox;
vm.createContext(sandbox);
for (const name of ['catalog.js', 'engine.js', 'conversation_adapter.js']) {
  const source = fs.readFileSync(path.join(repo, 'embedded', name), 'utf8');
  vm.runInContext(source, sandbox, { filename: name, timeout: 2000 });
}
const provider = {
  id: 'embedded-semantic',
  kind: 'bounded-semantic',
  execution: 'browser-local',
  respond: sandbox.TherapyBotEmbedded.respond
};
async function main() {
  const session = sandbox.TherapyBotConversationAdapter.createSession({
    providers: [provider], defaultProviderId: provider.id
  });
  const first = await session.turn({
    message: 'My supervisor refused to reimburse gasoline for the work truck.',
    mode: 'direct', timeoutMs: 10000
  });
  assert.equal(first.status, 'ok', JSON.stringify(first));
  assert.ok(typeof first.reply === 'string' && first.reply.length > 40);
  assert.equal(first.kind, 'bounded-semantic');
  assert.equal(first.clinicalQualification, 'none');
  assert.equal(first.providerNetworkVerified, false);
  assert.equal(first.providerStorageVerified, false);
  const second = await session.turn({
    message: 'I am concerned about getting fired.', mode: 'direct', timeoutMs: 10000
  });
  assert.equal(second.status, 'ok', JSON.stringify(second));
  assert.equal(session.snapshot().length, 4);
  session.clear();
  assert.equal(session.snapshot().length, 0);
  console.log('PASS: two genuine local turns, unvalidated qualification, history and reset.');
}
main().catch((error) => { console.error(error); process.exitCode = 1; });
