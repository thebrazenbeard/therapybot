'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const {
  validateAssistantTurn, requireDistinctAnswers, parseOptions
} = require('./therapybot_browser_neural_smoke.cjs');

const warning = 'Experimental 135M model output, permitted by a limited lexical filter—not clinical validation.';
test('accepts a genuine attributed neural reply', () => {
  assert.doesNotThrow(() => validateAssistantTurn('Check the hours and who approves the change.', warning));
});
test('rejects no-visible-token sentinel even with attribution', () => {
  assert.throws(() => validateAssistantTurn('The local model returned no visible text.', warning), /no actual model tokens/i);
});
test('rejects errors and rules-only replies with attribution', () => {
  assert.throws(() => validateAssistantTurn('Local inference failed. Timeout', warning), /no actual model tokens/i);
  assert.throws(() => validateAssistantTurn(' ', warning), /no actual model tokens/i);
  assert.throws(() => validateAssistantTurn('Check the hours.', ''), /experimental attribution/i);
});
test('requires distinct outputs for two synthetic prompts', () => {
  assert.throws(() => requireDistinctAnswers(['same words', 'same words']), /distinct/i);
  assert.doesNotThrow(() => requireDistinctAnswers(['First answer', 'Different second answer']));
});
test('accepts only loopback, explicit browser and mode options', () => {
  const o = parseOptions(['--browser','firefox','--origin','http://127.0.0.1:43877','--browser-bin','/usr/bin/firefox','--mode','online']);
  assert.equal(o.browser, 'firefox');
  assert.equal(o.mode, 'online');
  assert.throws(() => parseOptions(['--browser','edge','--origin','https://example.org','--browser-bin','/usr/bin/edge','--mode','online']), /loopback/i);
});

test('heavy browser workflow is public, label-gated and has no publish or artifact path', () => {
  const fs = require('node:fs');
  const path = require('node:path');
  const source = fs.readFileSync(path.join(__dirname,'..','.github','workflows',
    'therapybot-browser-neural-smoke.yml'),'utf8');
  assert.match(source,/pull_request:\s*\n\s*types:\s*\[labeled\]/);
  assert.match(source,/github\.event\.repository\.private == false/);
  assert.match(source,/github\.event\.label\.name == 'bt2-browser-neural-smoke'/);
  assert.match(source,/github\.event\.pull_request\.head\.repo\.full_name == github\.repository/);
  assert.match(source,/persist-credentials: false/);
  assert.match(source,/permissions:\s*\n\s*contents: read/);
  assert.doesNotMatch(source,/^\s+(?:pull_request_target|workflow_dispatch|push|schedule):/m);
  assert.doesNotMatch(source,/^\s*uses:\s*actions\/(?:cache|upload-artifact|deploy-pages)@/m);
  assert.match(source,/npm ci --prefix ci/);
  assert.match(source,/--mode online/);
});
