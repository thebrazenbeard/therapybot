/* Synthetic DOM/HTTP state-machine exercise; not an actual browser test. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const html = fs.readFileSync(process.env.THERAPYBOT_HTML_PATH || path.join(__dirname, '..', 'static', 'index.html'), 'utf8');
const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];
const event = { preventDefault() {} };

function harness() {
  const elements = new Map();
  const counters = { unlock: 0, lock: 0, objectUrls: 0 };
  let storage = 'locked';
  let lockReadback = 'locked';
  let lockRelease = null;
  let backupRelease = null;

  class Element {
    constructor(id = '') {
      this.id = id;
      this.handlers = {};
      this.textContent = '';
      this.value = '';
      this.childNodes = [];
      this.disabled = false;
      this.checked = false;
      this.classList = { toggle() {}, add() {}, remove() {} };
    }
    addEventListener(name, fn) { this.handlers[name] = fn; }
    append(...children) { this.childNodes.push(...children); }
    replaceChildren() { this.childNodes = []; }
    setAttribute() {}
    removeAttribute() {}
    focus() {}
    remove() {}
    click() {}
  }

  function elem(id) {
    if (!elements.has(id)) elements.set(id, new Element(id));
    return elements.get(id);
  }
  elem('passphrase').value = 'synthetic-passphrase-0001';

  const document = {
    getElementById: elem,
    querySelector() { return { content: 'synthetic-csrf' }; },
    querySelectorAll() { return []; },
    createElement(name) { return new Element(name); },
    createTextNode(text) { return new Element(String(text)); },
    body: { append() {} },
  };
  const jsonResponse = (body) => ({ ok: true, json: async () => body });
  async function fetch(url) {
    if (url === '/api/status') return jsonResponse({ storage, initialized: storage === 'unlocked', model_name: 'synthetic', ready: false });
    if (url === '/api/sources') return jsonResponse({ sources: [] });
    if (url === '/api/unlock') { counters.unlock++; storage = 'unlocked'; return jsonResponse({ storage, session: 'synthetic-session-a' }); }
    if (url === '/api/lock') {
      counters.lock++;
      if (lockRelease) await new Promise(resolve => { lockRelease.resolve = resolve; });
      storage = lockReadback;
      return jsonResponse({ storage: 'locked' });
    }
    if (url === '/api/backup') {
      return { ok: true, blob: async () => {
        if (backupRelease) await new Promise(resolve => { backupRelease.resolve = resolve; });
        return { synthetic: true };
      } };
    }
    throw Error('Unexpected synthetic API endpoint: ' + url);
  }
  class MockURL extends URL {}
  MockURL.createObjectURL = () => { counters.objectUrls++; return 'blob:synthetic'; };
  MockURL.revokeObjectURL = () => {};
  const ctx = { document, fetch, URL: MockURL, setTimeout() {} };
  vm.createContext(ctx);
  vm.runInContext(script, ctx);

  return {
    elements, elem, counters,
    setLockReadback(value) { lockReadback = value; },
    holdLock() { lockRelease = {}; },
    releaseLock() { lockRelease.resolve(); },
    holdBackup() { backupRelease = {}; },
    releaseBackup() { backupRelease.resolve(); },
  };
}

async function unlock(h) { await h.elem('unlock-form').handlers.submit(event); }
async function lock(h) { await h.elem('lock-button').handlers.click(); }

(async () => {
  const h = harness();
  await unlock(h);
  assert.match(h.elem('vault-badge').textContent, /unlocked in this tab/);
  h.holdLock();
  h.setLockReadback('unlocked'); // simulates concurrent unlock in another tab
  const locking = lock(h);
  await unlock(h); // must not issue a second unlock while lock is pending
  assert.equal(h.counters.unlock, 1);
  assert.equal(h.elem('unlock-button').disabled, true);
  h.releaseLock();
  await locking;
  assert.match(h.elem('vault-feedback').textContent, /could not be confirmed/);
  assert.doesNotMatch(h.elem('vault-feedback').textContent, /^Vault locked\./);
  assert.match(h.elem('vault-badge').textContent, /re-enter passphrase/);

  const success = harness();
  await unlock(success);
  success.setLockReadback('locked');
  await lock(success);
  assert.equal(success.elem('vault-feedback').textContent, 'Vault locked.');
  assert.match(success.elem('vault-badge').textContent, /locked/);

  const stale = harness();
  await unlock(stale);
  stale.holdBackup();
  const backup = stale.elem('backup-button').handlers.click();
  await lock(stale);
  stale.releaseBackup();
  await backup;
  assert.equal(stale.counters.objectUrls, 0, 'no backup download after the tab has locked');
  console.log('3/3 synthetic vault UI state tests pass (not browser E2E)');
})().catch(err => { console.error(err); process.exitCode = 1; });
