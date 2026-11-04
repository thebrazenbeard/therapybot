'use strict';

// Browser-DOM interaction smoke with a minimal fake DOM, not a real-browser test.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const root = path.resolve(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'static/offline.html'), 'utf8');
const localScripts = [...html.matchAll(/<script\s+src="([^"]+)"\s*><\/script>/g)].map((m) => m[1]);
assert.deepEqual(localScripts, ['semantic_core.js']);
assert(!/<script[^>]+src="https?:\/\//i.test(html), 'remote script asset');
assert(!/<iframe\b/i.test(html), 'embedded iframe');

const inline = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)];
assert.equal(inline.length, 1, 'exactly one inline UI script');

class MockNode {
  constructor(tagName) {
    this.tagName = tagName;
    this.children = [];
    this.listeners = {};
    this.dataset = {};
    this.value = '';
    this.textContent = '';
    this.scrollTop = 0;
    this.scrollHeight = 0;
  }
  addEventListener(type, handler) { this.listeners[type] = handler; }
  get childNodes() { return this.children; }
  append(...items) { this.children.push(...items); }
  remove() { this.removed = true; }
  replaceChildren(...items) { this.children = items; }
  focus() { this.focused = true; }
}

const names = ['engine-status', 'message', 'compose', 'conversation', 'empty',
  'clear', 'style', 'depth', 'feedback'];
const nodes = Object.fromEntries(names.map((name) => [name, new MockNode(name)]));
nodes.style.value = 'direct';
nodes.depth.value = 'balanced';

const doc = {
  getElementById: (name) => nodes[name] ?? null,
  createElement: (tag) => new MockNode(tag),
  createTextNode: (value) => ({ tagName: '#text', textContent: String(value) }),
};

let egress = 0;
let persistentWrites = 0;
const prohibited = () => { egress += 1; throw Error('Unexpected outbound request'); };
const storage = { setItem: () => { persistentWrites += 1; throw Error('Unexpected persistence'); },
  getItem: () => { persistentWrites += 1; throw Error('Unexpected storage read'); } };
const context = {
  document: doc,
  URL,
  fetch: prohibited,
  XMLHttpRequest: prohibited,
  WebSocket: prohibited,
  localStorage: storage,
  sessionStorage: storage,
  indexedDB: { open: () => { persistentWrites += 1; throw Error('IndexedDB used'); } },
};
context.window = { TherapyBotSemanticCore: require(path.join(root, 'static/semantic_core.js')) };
vm.runInNewContext(inline[0][1], context, { timeout: 3000 });
assert.match(nodes['engine-status'].textContent, /ready/i);

const submit = (message) => {
  nodes.message.value = message;
  let prevented = false;
  nodes.compose.listeners.submit({ preventDefault() { prevented = true; } });
  assert(prevented, 'form should not navigate');
};

submit('My mother and I argued today');
submit('I said my sister, not my mother');
submit('What should I do about that?');
assert.equal(nodes.conversation.children.length, 6, 'three user/guide exchange pairs');
const replies = nodes.conversation.children.filter((entry) => entry.tagName === 'article');
assert(replies.some((entry) => entry.children.some((child) => /your sister/.test(child.textContent))),
  'context correction not reflected in rendered conversation: ' +
    JSON.stringify(replies.map((entry) => entry.children.map((child) => child.textContent))));
assert.equal(egress, 0, 'page should not contact network in a conversation');
assert.equal(persistentWrites, 0, 'page should not persist chat or retrieve stored data');

nodes.clear.listeners.click();
assert.equal(nodes.conversation.children.length, 1, 'clear should erase visible dialogue');
assert.match(nodes.conversation.children[0].textContent, /Session cleared/);

process.stdout.write('PASS: offline DOM smoke; 3-turn correction; no egress/storage; clear session\n');
