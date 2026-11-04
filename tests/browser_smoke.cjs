#!/usr/bin/env node
/*
 * Real-browser, development-only smoke test for embedded/index.html.
 *
 * Run on Windows Lappy with an installed Edge and Puppeteer / Puppeteer-core:
 *   $env:PUPPETEER_CORE_PATH = 'C:\\path\\to\\node_modules\\puppeteer-core'
 *   $env:EDGE_EXECUTABLE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
 *   node tests/browser_smoke.cjs
 *
 * No package installation, remote inference, public deployment, user profile,
 * or real personal information is needed. Screenshots and a structured report
 * are written to an isolated temporary artifact directory (or the exact path
 * given by BROWSER_SMOKE_OUTPUT_DIR). Only the test browser profile is deleted.
 */
'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const os = require('node:os');
const path = require('node:path');

const ROOT = path.resolve(__dirname, '..');
const EMBEDDED = path.join(ROOT, 'embedded');
const FILES = Object.freeze({
  '/': ['index.html', 'text/html; charset=utf-8'],
  '/index.html': ['index.html', 'text/html; charset=utf-8'],
  '/style.css': ['style.css', 'text/css; charset=utf-8'],
  '/catalog.js': ['catalog.js', 'text/javascript; charset=utf-8'],
  '/engine.js': ['engine.js', 'text/javascript; charset=utf-8'],
  '/council.js': ['council.js', 'text/javascript; charset=utf-8'],
  '/conversation_adapter.js': ['conversation_adapter.js', 'text/javascript; charset=utf-8'],
  '/ui.js': ['ui.js', 'text/javascript; charset=utf-8'],
});

const report = {
  schema: 'therapybot.browser_smoke.v1',
  startedAt: new Date().toISOString(),
  status: 'failed',
  browser: 'Edge (isolated headless profile)',
  tests: [],
  transcript: [],
  requestedExternalUrls: [],
  pageErrors: [],
  consoleErrors: [],
  screenshots: [],
};

function puppeteerModule() {
  const attempts = [process.env.PUPPETEER_CORE_PATH, 'puppeteer-core', 'puppeteer'].filter(Boolean);
  const errors = [];
  for (const candidate of attempts) {
    try { return require(candidate); } catch (error) { errors.push(candidate + ': ' + error.message); }
  }
  throw new Error('Puppeteer is unavailable. Set PUPPETEER_CORE_PATH to the installed package path. ' + errors.join(' | '));
}

function edgeExecutable() {
  const candidates = [
    process.env.EDGE_EXECUTABLE,
    'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
    'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe',
  ].filter(Boolean);
  const found = candidates.find((candidate) => fs.existsSync(candidate));
  if (!found) throw new Error('Edge was not found. Set EDGE_EXECUTABLE to the installed msedge.exe.');
  return found;
}

function localServer() {
  return http.createServer((request, response) => {
    let url;
    try { url = new URL(request.url || '/', 'http://127.0.0.1'); } catch {
      response.writeHead(400).end();
      return;
    }
    if (url.pathname === '/favicon.ico') {
      response.writeHead(204).end();
      return;
    }
    const allowed = FILES[url.pathname];
    if (!allowed || request.method !== 'GET') {
      response.writeHead(404).end('Not found');
      return;
    }
    const [filename, contentType] = allowed;
    const source = path.join(EMBEDDED, filename);
    if (!fs.existsSync(source)) {
      response.writeHead(404).end('Missing bundled asset');
      return;
    }
    response.writeHead(200, {
      'Content-Type': contentType,
      'Cache-Control': 'no-store',
      'X-Content-Type-Options': 'nosniff',
      'Referrer-Policy': 'no-referrer',
    });
    fs.createReadStream(source).pipe(response);
  });
}

async function test(name, action) {
  const started = Date.now();
  try {
    const detail = await action();
    report.tests.push({ name, status: 'pass', durationMs: Date.now() - started, detail: detail ?? null });
    process.stdout.write('PASS ' + name + '\n');
  } catch (error) {
    report.tests.push({ name, status: 'fail', durationMs: Date.now() - started, error: String(error?.stack || error) });
    process.stderr.write('FAIL ' + name + ': ' + error.message + '\n');
    throw error;
  }
}

async function count(page, selector) {
  return page.$$eval(selector, (nodes) => nodes.length);
}

async function send(page, message) {
  const prior = await count(page, '.message--assistant');
  await page.$eval('#message', (field, text) => {
    field.value = text;
    field.dispatchEvent(new Event('input', { bubbles: true }));
  }, message);
  await page.click('#send-message');
  await page.waitForFunction((previous) => {
    return document.querySelectorAll('.message--assistant').length > previous;
  }, { timeout: 12000 }, prior);
  const snapshot = await page.evaluate(() => {
    const elements = [...document.querySelectorAll('.message')];
    const latest = elements[elements.length - 1];
    return {
      reply: latest?.querySelector('.message-content, .council-speakers, .council-facilitator')?.textContent?.trim() || '',
      text: latest?.innerText || '',
      speakers: [...(latest?.querySelectorAll('.council-speaker-name') || [])].map((element) => element.textContent),
      userLabels: [...(latest?.querySelectorAll('.council-speaker-user-label') || [])].map((element) => element.textContent),
      meta: latest?.querySelector('.message-meta')?.textContent || '',
      feedback: document.querySelector('#form-feedback')?.textContent || '',
      warning: latest?.classList.contains('message--warning') || false,
    };
  });
  report.transcript.push({ input: message, ...snapshot });
  return snapshot;
}

async function addMember(page, name, role, notes = '') {
  await page.$eval('#member-name', (node, value) => { node.value = value; }, name);
  await page.$eval('#member-role', (node, value) => { node.value = value; }, role);
  await page.$eval('#member-notes', (node, value) => { node.value = value; }, notes);
  await page.click('#save-member');
}

async function screenshot(page, artifactDir, filename) {
  const target = path.join(artifactDir, filename);
  await page.screenshot({ path: target, fullPage: true, animations: 'disabled' });
  report.screenshots.push(target);
}

async function run() {
  let server;
  let browser;
  let page;
  let artifactDir;
  let taskProfile;
  try {
    const puppeteer = puppeteerModule();
    const executablePath = edgeExecutable();
    for (const file of Object.values(FILES)) {
      assert(fs.existsSync(path.join(EMBEDDED, file[0])), 'Missing required embedded asset: ' + file[0]);
    }
    artifactDir = process.env.BROWSER_SMOKE_OUTPUT_DIR
      ? path.resolve(process.env.BROWSER_SMOKE_OUTPUT_DIR)
      : fs.mkdtempSync(path.join(os.tmpdir(), 'therapybot-browser-smoke-'));
    fs.mkdirSync(artifactDir, { recursive: true });
    taskProfile = fs.mkdtempSync(path.join(os.tmpdir(), 'therapybot-edge-smoke-profile-'));
    report.artifactDir = artifactDir;
    report.edgeExecutable = executablePath;

    server = localServer();
    await new Promise((resolve, reject) => {
      server.once('error', reject);
      server.listen(0, '127.0.0.1', resolve);
    });
    const port = server.address().port;
    const origin = 'http://127.0.0.1:' + port;
    report.localOrigin = origin;

    browser = await puppeteer.launch({
      executablePath,
      headless: true,
      userDataDir: taskProfile,
      args: [
        '--no-first-run',
        '--no-default-browser-check',
        '--disable-background-networking',
        '--disable-component-update',
        '--disable-sync',
      ],
    });
    page = await browser.newPage();
    await page.setViewport({ width: 1365, height: 900, deviceScaleFactor: 1 });
    page.on('pageerror', (error) => report.pageErrors.push(String(error)));
    page.on('console', (item) => {
      if (item.type() === 'error') report.consoleErrors.push(item.text());
    });
    await page.setRequestInterception(true);
    page.on('request', (request) => {
      const requested = request.url();
      if (!requested.startsWith(origin + '/') && requested !== origin) {
        report.requestedExternalUrls.push(requested);
        request.abort('blockedbyclient').catch(() => {});
        return;
      }
      request.continue().catch(() => {});
    });
    await page.goto(origin + '/', { waitUntil: 'networkidle0', timeout: 20000 });
    await page.waitForFunction(() => document.querySelector('#engine-status')?.textContent?.includes('ready'));

    await test('Fresh tab has no Inner Council roster', async () => {
      assert.match(await page.$eval('#council-count', (element) => element.textContent), /No members defined/);
      assert.equal(await count(page, '.member-card'), 0);
      assert.equal(await count(page, '.message'), 0);
      assert.equal(await page.$eval('#convene-council', (element) => element.getAttribute('aria-pressed')), 'false');
      await screenshot(page, artifactDir, '01-empty.png');
    });

    await test('Emergency contacts remain available without JavaScript', async () => {
      const disabled = await browser.newPage();
      try {
        await disabled.setJavaScriptEnabled(false);
        await disabled.goto(origin + '/', { waitUntil: 'load', timeout: 20000 });
        const panel = await disabled.evaluate(() => {
          const section = document.querySelector('#immediate-help');
          return {
            label: section?.querySelector('#emergency-title')?.textContent || '',
            links: [...(section?.querySelectorAll('a') || [])].map((link) => link.getAttribute('href')),
            visible: section ? getComputedStyle(section).display !== 'none' : false,
            shortcut: document.querySelector('.emergency-shortcut a')?.getAttribute('href') || '',
          };
        });
        assert.match(panel.label, /Need urgent help/i);
        assert.equal(panel.visible, true);
        assert(panel.links.includes('tel:911'));
        assert(panel.links.includes('tel:18002221222'));
        assert(panel.links.includes('tel:988'));
        assert.equal(panel.shortcut, '#immediate-help');
        await disabled.click('.emergency-shortcut a');
        assert.equal(new URL(disabled.url()).hash, '#immediate-help');
      } finally {
        await disabled.close();
      }
    });

    await test('Convene without members prompts authorship, not invented people', async () => {
      await page.click('#convene-council');
      assert.equal(await page.$eval('#council-setup', (element) => element.hidden), false);
      assert.match(await page.$eval('#member-feedback', (element) => element.textContent), /Add at least one perspective/);
      assert.equal(await page.$eval('#convene-council', (element) => element.getAttribute('aria-pressed')), 'false');
    });

    await test('Create two user-authored perspectives', async () => {
      await addMember(page, 'Strategist', 'Consider consequences before acting', 'I value practical options.');
      await addMember(page, 'Guardian', 'Protect boundaries without threats', 'I need a deliberate pace.');
      assert.equal(await count(page, '.member-card'), 2);
      assert.match(await page.$eval('#council-count', (element) => element.textContent), /2 members/);
    });

    await test('Without JavaScript, Add member cannot submit private text or navigate', async () => {
      const disabled = await browser.newPage();
      try {
        await disabled.setJavaScriptEnabled(false);
        await disabled.goto(origin + '/', { waitUntil: 'load', timeout: 20000 });
        // Only unhide the native controls for a failure-mode probe; no page JS.
        await disabled.addStyleTag({ content: '#council-setup[hidden] { display: block !important; }' });
        await disabled.type('#member-name', 'SyntheticSecretName');
        await disabled.type('#member-role', 'SyntheticSecretRole');
        await disabled.type('#member-notes', 'SyntheticSecretNotes');
        const navigations = [];
        disabled.on('request', (request) => {
          if (request.isNavigationRequest()) navigations.push(request.url());
        });
        const navigation = disabled.waitForNavigation({ timeout: 1200 }).then(() => true, () => false);
        await disabled.click('#save-member');
        assert.equal(await navigation, false, 'A disabled-script editor must not submit a native request');
        assert.equal(disabled.url(), origin + '/');
        assert.deepEqual(navigations, []);
      } finally {
        await disabled.close();
      }
    });

    await test('Without JavaScript, Send cannot submit conversation text or navigate', async () => {
      const disabled = await browser.newPage();
      try {
        await disabled.setJavaScriptEnabled(false);
        await disabled.goto(origin + '/', { waitUntil: 'load', timeout: 20000 });
        await disabled.type('#message', 'SyntheticPrivateConversationDoNotTransmit');
        assert.equal(await disabled.$eval('.noscript-notice', (element) => getComputedStyle(element).display !== 'none'), true);
        const navigations = [];
        disabled.on('request', (request) => {
          if (request.isNavigationRequest()) navigations.push(request.url());
        });
        const navigation = disabled.waitForNavigation({ timeout: 1200 }).then(() => true, () => false);
        await disabled.click('#send-message');
        assert.equal(await navigation, false, 'A disabled-script composer must not submit a native request');
        assert.equal(disabled.url(), origin + '/');
        assert.deepEqual(navigations, []);
      } finally {
        await disabled.close();
      }
    });

    await test('Convene and conduct a live two-turn Council exchange', async () => {
      await page.click('#convene-council');
      assert.equal(await page.$eval('#convene-council', (element) => element.getAttribute('aria-pressed')), 'true');
      assert.equal(await page.$eval('#council-setup', (element) => element.hidden), true,
        'The editor must collapse so conversation can take priority.');
      const first = await send(page, 'I want to set a clear boundary with a colleague. What am I overlooking?');
      assert.deepEqual(first.speakers, ['Perspective 1', 'Perspective 2']);
      assert.deepEqual(first.userLabels, ['Your label: Strategist', 'Your label: Guardian']);
      assert.match(first.text, /not evidence of separate people or diagnoses/i);
      const second = await send(page, 'If I speak plainly but calmly to my colleague about that boundary, what would each perspective want me to remember?');
      assert.deepEqual(second.speakers, ['Perspective 1', 'Perspective 2']);
      assert.equal(await count(page, '.message--user'), 2);
      await screenshot(page, artifactDir, '02-council-conversation.png');
    });

    await test('Unverified Council question abstains instead of inventing a debate', async () => {
      const answer = await send(page, 'Council: qwerty unknown situation xyz');
      assert.deepEqual(answer.speakers, []);
      assert.match(answer.text, /cannot establish a supported topic/i);
      assert.equal(answer.warning, true);
    });

    await test('Typed Solo command addresses only a configured member', async () => {
      // After an unsupported prompt, the earlier topic is not assumed safe to
      // resurrect. State the actual work context when requesting Solo mode.
      const answer = await send(page, 'Solo Strategist: For my work conversation with a colleague, what is the next practical question to ask?');
      assert.deepEqual(answer.speakers, ['Perspective 1']);
      assert.match(answer.text, /user-defined lens/i);
    });

    await test('Known explicit danger bypasses the simulated Council', async () => {
      const answer = await send(page, 'I am going to kill myself tonight, and I have a plan.');
      assert.equal(answer.speakers.length, 0);
      assert.match(answer.meta, /Safety route: urgent_review/);
      assert.equal(answer.warning, true);
    });

    await test('Containment command pauses Council and returns to direct chat', async () => {
      const answer = await send(page, 'Containment: Please pause the Council.');
      assert.equal(answer.speakers.length, 0);
      assert.match(answer.text, /Council is paused/i);
      assert.equal(await page.$eval('#convene-council', (element) => element.getAttribute('aria-pressed')), 'false');
    });

    await test('Ordinary direct conversation remains available after Containment', async () => {
      const answer = await send(page, 'How can I tell a healthy work boundary from avoidance?');
      assert.equal(answer.speakers.length, 0);
      assert.equal(answer.warning, false);
      assert.match(answer.meta, /Experimental · not clinically validated/);
      assert(answer.text.length > 50, 'Expected a nonempty ordinary response.');
    });

    await test('Clear chat leaves authored Council members intact', async () => {
      await page.click('#clear-chat');
      assert.equal(await count(page, '.message'), 0);
      assert.equal(await count(page, '.member-card'), 2);
      assert.match(await page.$eval('#council-count', (element) => element.textContent), /2 members/);
    });

    await test('User-provided HTML is text, never executable markup', async () => {
      const payload = '<img src=x onerror="window.__therapybot_injected=true">';
      await send(page, 'I am testing this literal text: ' + payload);
      const values = await page.evaluate(() => ({
        userText: [...document.querySelectorAll('.message--user .message-content')].at(-1)?.textContent || '',
        userImages: document.querySelectorAll('.message--user img').length,
        injected: Boolean(window.__therapybot_injected),
      }));
      assert(values.userText.includes(payload));
      assert.equal(values.userImages, 0);
      assert.equal(values.injected, false);
    });

    await test('Forget all requires confirmation and then erases Council and chat', async () => {
      page.once('dialog', (dialog) => { dialog.dismiss().catch(() => {}); });
      await page.click('#clear-all');
      assert.equal(await count(page, '.member-card'), 2);
      page.once('dialog', (dialog) => { dialog.accept().catch(() => {}); });
      await page.click('#clear-all');
      assert.equal(await count(page, '.member-card'), 0);
      assert.equal(await count(page, '.message'), 0);
      assert.match(await page.$eval('#council-count', (element) => element.textContent), /No members defined/);
      await screenshot(page, artifactDir, '03-forgotten.png');
    });

    await test('Mobile viewport fits without horizontal page overflow', async () => {
      await page.setViewport({ width: 390, height: 844, deviceScaleFactor: 1, isMobile: true });
      const layout = await page.evaluate(() => ({
        viewport: window.innerWidth,
        documentWidth: document.documentElement.scrollWidth,
        bodyWidth: document.body.scrollWidth,
      }));
      assert(layout.documentWidth <= layout.viewport + 1, JSON.stringify(layout));
      assert(layout.bodyWidth <= layout.viewport + 1, JSON.stringify(layout));
      await screenshot(page, artifactDir, '04-mobile.png');
      return layout;
    });

    await test('No external network or JavaScript exceptions', async () => {
      assert.deepEqual(report.requestedExternalUrls, []);
      assert.deepEqual(report.pageErrors, []);
      assert.deepEqual(report.consoleErrors, []);
    });

    report.status = 'passed';
  } catch (error) {
    report.failure = String(error?.stack || error);
    if (page && artifactDir) {
      try { await screenshot(page, artifactDir, 'failure.png'); } catch { /* Preserve original error. */ }
    }
    process.exitCode = 1;
  } finally {
    if (browser) {
      try { await browser.close(); } catch (error) { report.cleanupError = String(error); process.exitCode = 1; }
    }
    if (server?.listening) {
      await new Promise((resolve) => server.close(resolve));
    }
    if (taskProfile) {
      try { fs.rmSync(taskProfile, { recursive: true, force: true }); } catch (error) {
        report.profileCleanupError = String(error);
        process.exitCode = 1;
      }
    }
    report.finishedAt = new Date().toISOString();
    report.totalTests = report.tests.length;
    report.passedTests = report.tests.filter((entry) => entry.status === 'pass').length;
    if (artifactDir) {
      const resultFile = path.join(artifactDir, 'report.json');
      fs.writeFileSync(resultFile, JSON.stringify(report, null, 2) + '\n', { encoding: 'utf8', mode: 0o600 });
      process.stdout.write('ARTIFACTS ' + artifactDir + '\n');
      process.stdout.write('REPORT ' + resultFile + '\n');
    } else {
      process.stderr.write('SETUP FAILURE ' + report.failure + '\n');
    }
  }
}

run().catch((error) => {
  process.stderr.write('UNHANDLED ' + String(error?.stack || error) + '\n');
  process.exitCode = 1;
});
