import { createRequire } from 'node:module';
import { execFileSync } from 'node:child_process';
import { writeFile } from 'node:fs/promises';
import assert from 'node:assert/strict';
const require = createRequire(new URL('../bot-screen-plugin/package.json', import.meta.url));
const { chromium } = require('playwright');
const browser = await chromium.launch({ executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true });
const context = await browser.newContext({ viewport: { width: 1600, height: 1000 } });
await context.addInitScript(() => {
  const Native = window.WebSocket;
  window.__languageSockets = [];
  window.WebSocket = new Proxy(Native, { construct(Target, args) { const socket = new Target(...args); window.__languageSockets.push(socket); return socket; } });
});
const page = await context.newPage(), origin = 'http://127.0.0.1:9124';
const credentials = JSON.parse(execFileSync('docker', ['exec', 'bot-screen-integration', '/opt/hermes-venv/bin/python', '-c', "from pathlib import Path;print(Path('/lab/test-login.json').read_text())"], { encoding: 'utf8' }));
const result = { gates: {}, errors: [], passed: false };
const section = page.getByTestId('bot-screen');
page.on('pageerror', error => result.errors.push(error.message));
const ready = () => page.waitForFunction(() => document.querySelector('[data-testid=bot-screen]')?.dataset.connection === 'ready');
async function language(value) {
  if (!await page.getByTestId('language-select').count()) await section.locator('.bs-more-button').click();
  await page.getByTestId('language-select').selectOption(value);
}
try {
  assert.equal((await page.request.post(origin + '/auth/password-login', { data: { ...credentials, provider: 'basic' } })).status(), 200);
  await page.goto(origin + '/bot-screen'); await ready();
  await page.evaluate(() => { localStorage.removeItem('bot-screen:language:v1'); localStorage.setItem('hermes-locale', 'en'); });
  await page.reload(); await ready();
  assert.equal(await section.getAttribute('data-locale'), 'en');
  assert.equal(await section.getAttribute('data-language-preference'), 'auto');
  result.gates.followHermesEnglish = true;
  await section.locator('[data-action=watch]').click();
  await page.waitForFunction(() => document.querySelector('[data-testid=bot-screen]')?.dataset.connected === 'true');
  await section.locator('[data-action=takeover]').click();
  await page.waitForTimeout(400);
  const sockets = await page.evaluate(() => window.__languageSockets.length);
  const canvas = await section.locator('canvas').elementHandle();
  for (const locale of ['zh-Hant', 'zh-Hans', 'en']) {
    await language(locale);
    assert.equal(await section.getAttribute('data-locale'), locale);
    assert.equal(await section.getAttribute('data-connected'), 'true');
    assert.ok((await section.getAttribute('class')).includes('bs-controlling'));
    assert.equal(await page.evaluate(() => window.__languageSockets.length), sockets);
    assert.equal(await canvas.evaluate(element => element.isConnected), true);
  }
  result.gates.switchDuringControlPreservesSocketsCanvasAndLease = true;
  await section.locator('[data-action=handback]').click();
  assert.equal(await section.getByTestId('control-state').innerText(), 'Watch mode');
  result.gates.handbackInEnglish = true;
  await language('zh-Hans'); await page.reload(); await ready();
  assert.equal(await section.getAttribute('data-locale'), 'zh-Hans');
  result.gates.preferencePersists = true;
  await language('auto');
  await page.evaluate(() => localStorage.setItem('hermes-locale', 'zh-hant'));
  await page.reload(); await ready();
  assert.equal(await section.getAttribute('data-locale'), 'zh-Hant');
  result.gates.followHermesTraditional = true;
  await page.setViewportSize({ width: 390, height: 844 });
  for (const locale of ['en', 'zh-Hans', 'zh-Hant']) {
    await language(locale);
    assert.ok(await section.evaluate(element => element.scrollWidth <= element.clientWidth + 1));
    await section.locator('.bs-more-button').click();
    assert.ok((await page.getByTestId('language-select').boundingBox()).height >= 44);
  }
  await page.screenshot({ path: 'evidence/i18n-mobile.png' });
  result.gates.mobileLanguagesFit = true;
  assert.deepEqual(result.errors, []); result.passed = true;
} catch (error) { result.errors.push(error.message); process.exitCode = 1; }
finally { await writeFile('evidence/i18n-review.json', JSON.stringify(result, null, 2)); console.log(JSON.stringify(result, null, 2)); await browser.close(); }
