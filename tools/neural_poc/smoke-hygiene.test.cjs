// Guard against accidentally restoring the obsolete, misleading preflight driver.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const fixture = name => path.join(__dirname, name);

test('obsolete hardcoded smoke driver is absent', () => {
  assert.equal(fs.existsSync(fixture('smoke.cjs')), false,
    'smoke.cjs hardcoded a user profile, port 43187 and fabricated cache telemetry');
});

test('maintained click driver exposes host options and observed cache telemetry', () => {
  const source = fs.readFileSync(fixture('click-smoke.cjs'), 'utf8');
  assert.match(source, /--puppeteer-dir/);
  assert.match(source, /--browser-bin/);
  assert.match(source, /--port/);
  assert.match(source, /cacheKeys:/);
  assert.doesNotMatch(source, /DesktopCommanderMCP|usedCacheStorage|43187/);
});
