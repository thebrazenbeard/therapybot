#!/usr/bin/env node
/* Synthetic DOM execution of the actual embedded/ui.js, not a real browser. */
'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

const EMBEDDED = path.resolve(__dirname, '../embedded');

class FakeElement {
  constructor(tagName, document, id = '') {
    this.tagName = tagName;
    this.document = document;
    this.id = id;
    this.children = [];
    this.handlers = {};
    this.className = '';
    this.hidden = false;
    this.value = '';
    this.dataset = {};
    this.attributes = {};
    this.textContent = '';
    this.scrollTop = 0;
    this.scrollHeight = 0;
    this.clientHeight = 0;
    this.classList = { toggle() {}, add() {}, remove() {} };
  }
  set innerHTML(_value) { throw new Error('DOM HTML sink is prohibited'); }
  addEventListener(name, action) { (this.handlers[name] ||= []).push(action); }
  setAttribute(name, value) { this.attributes[name] = String(value); }
  getAttribute(name) { return this.attributes[name] ?? null; }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this.children = [...children]; }
  remove() { this.document.elements.delete(this.id); }
  focus() { this.document.activeElement = this; }
  scrollTo({ top }) {
    this.scrollTop = Math.min(top, Math.max(0, this.scrollHeight - this.clientHeight));
  }
  reset() {
    for (const field of ['member-name', 'member-role', 'member-notes']) {
      this.document.getElementById(field).value = '';
    }
  }
  get childElementCount() { return this.children.length; }
  querySelector(selector) {
    if (selector !== 'a') throw new Error('Unexpected DOM selector: ' + selector);
    return descendants(this, (element) => element.tagName === 'a')[0] || null;
  }
  async fire(name) {
    for (const action of this.handlers[name] || []) await action({ preventDefault() {} });
  }
}

function createFakeDom() {
  const document = {
    activeElement: null,
    elements: new Map(),
    getElementById(id) { return this.elements.get(id) || null; },
    createElement(tagName) { return new FakeElement(tagName, this); },
    querySelectorAll(selector) {
      assert.equal(selector, '[data-suggestion]');
      return [];
    }
  };
  for (const id of [
    'conversation-form', 'message', 'conversation-log', 'send-message',
    'clear-chat', 'clear-all', 'engine-status', 'form-feedback',
    'convene-council', 'manage-council', 'council-setup', 'member-form',
    'member-list', 'member-name', 'member-role', 'member-notes',
    'save-member', 'cancel-member-edit', 'member-feedback',
    'council-count', 'style', 'depth', 'welcome'
  ]) {
    const node = new FakeElement('div', document, id);
    document.elements.set(id, node);
  }
  document.getElementById('style').value = 'direct';
  document.getElementById('depth').value = 'balanced';
  const effects = [];
  const window = {
    document,
    handlers: {},
    addEventListener(name, callback) { (this.handlers[name] ||= []).push(callback); },
    fire(name) { for (const action of this.handlers[name] || []) action(); },
    requestAnimationFrame(callback) { callback(); },
    confirm: () => true,
    localStorage: { getItem() { effects.push('localStorage.get'); throw new Error('storage'); }, setItem() { effects.push('localStorage.set'); throw new Error('storage'); } },
    sessionStorage: { getItem() { effects.push('sessionStorage.get'); throw new Error('storage'); }, setItem() { effects.push('sessionStorage.set'); throw new Error('storage'); } },
    fetch() { effects.push('fetch'); throw new Error('network'); }
  };
  const context = vm.createContext({ window, document, AbortController, setTimeout, clearTimeout, URL, console });
  for (const filename of ['catalog.js', 'engine.js', 'council.js', 'conversation_adapter.js', 'ui.js']) {
    vm.runInContext(fs.readFileSync(path.join(EMBEDDED, filename), 'utf8'), context, { filename, timeout: 2500 });
  }
  return { window, document, effects };
}

function descendants(root, predicate) {
  const result = [];
  function visit(node) {
    if (predicate(node)) result.push(node);
    for (const child of node.children || []) visit(child);
  }
  visit(root);
  return result;
}

test('actual UI uses the registered adapter for ordinary message, source links and transient Clear', async () => {
  const { document, effects } = createFakeDom();
  assert.match(document.getElementById('engine-status').textContent, /ready/);
  document.getElementById('message').value = 'My manager expects me to pay for company fuel.';
  await document.getElementById('send-message').fire('click');
  const log = document.getElementById('conversation-log');
  assert.equal(log.children.length, 2);
  assert.match(descendants(log, (el) => el.className === 'message-content').map((n) => n.textContent).join(' '), /workplace|work|practical/i);
  document.getElementById('clear-chat').fire('click');
  assert.equal(log.children.length, 1);
  assert.equal(log.children[0].id, 'welcome');
  assert.deepEqual(effects, []);
});

test('actual UI creates user-authored Council, convenes, contains and forgets everything', async () => {
  const { document, effects } = createFakeDom();
  document.getElementById('member-name').value = 'Skeptic';
  document.getElementById('member-role').value = 'Ask what evidence is missing';
  document.getElementById('member-notes').value = 'No assumed consensus';
  await document.getElementById('save-member').fire('click');
  document.getElementById('member-name').value = 'Guardian';
  document.getElementById('member-role').value = 'Watch practical boundaries';
  await document.getElementById('save-member').fire('click');
  assert.match(document.getElementById('council-count').textContent, /2 members/);
  await document.getElementById('convene-council').fire('click');
  document.getElementById('message').value = 'What should I do about my boss?';
  await document.getElementById('send-message').fire('click');
  const log = document.getElementById('conversation-log');
  const speakers = descendants(log, (el) => el.className === 'council-speaker');
  assert.equal(speakers.length, 2, 'Council cards must remain in actual UI after adapter integration');
  const generated = descendants(log, (el) => el.className === 'council-speaker-name').map((el) => el.textContent);
  assert.deepEqual(generated, ['Perspective 1', 'Perspective 2']);
  const labels = descendants(log, (el) => el.className === 'council-speaker-user-label').map((el) => el.textContent);
  assert.deepEqual(labels, ['Your label: Skeptic', 'Your label: Guardian']);
  document.getElementById('message').value = 'Containment: Return to direct conversation.';
  await document.getElementById('send-message').fire('click');
  assert.equal(document.getElementById('convene-council').getAttribute('aria-pressed'), 'false');
  await document.getElementById('clear-all').fire('click');
  assert.match(document.getElementById('council-count').textContent, /No members defined/);
  assert.equal(log.children.length, 1);
  assert.deepEqual(effects, []);
});
