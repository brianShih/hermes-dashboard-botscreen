import test from 'node:test';
import assert from 'node:assert/strict';
import { translations, normalizeLocale, resolveLocale, translate, readPreference, savePreference, errorMessage } from '../src/i18n.mjs';

test('all languages have complete messages and matching placeholders', () => {
  for (const dictionary of Object.values(translations)) {
    assert.deepEqual(Object.keys(dictionary).sort(), Object.keys(translations.en).sort());
    for (const [key, value] of Object.entries(dictionary)) {
      assert.ok(value.trim(), key);
      assert.deepEqual(value.match(/\{\w+\}/g), translations.en[key].match(/\{\w+\}/g), key);
    }
  }
});
test('locale aliases and host preference resolve predictably', () => {
  for (const value of ['zh-TW', 'zh_HK', 'zh-hant']) assert.equal(normalizeLocale(value), 'zh-Hant');
  for (const value of ['zh', 'zh-CN', 'zh-Hans']) assert.equal(normalizeLocale(value), 'zh-Hans');
  assert.equal(resolveLocale('auto', 'zh-hant', ['en']), 'zh-Hant');
  assert.equal(resolveLocale('en', 'zh-hant'), 'en');
  assert.equal(resolveLocale('auto', 'fr', ['zh-TW']), 'en');
  assert.equal(resolveLocale('auto', '', ['fr', 'zh-TW']), 'zh-Hant');
});
test('language preference survives storage and tolerates inaccessible storage', () => {
  let value; const storage = { getItem: () => value, setItem: (_, next) => { value = next; } };
  assert.equal(readPreference(storage), 'auto');
  assert.equal(savePreference(storage, 'zh-Hans'), true);
  assert.equal(readPreference(storage), 'zh-Hans');
  assert.equal(savePreference(storage, 'invalid'), false);
  assert.equal(readPreference(null), 'auto');
  assert.equal(savePreference(null, 'en'), false);
});
test('known errors translate and backend diagnostics remain intact', () => {
  const message = errorMessage({ code: 'notConnected' });
  assert.equal(translate('en', message.key), translations.en['error.notConnected']);
  const raw = errorMessage(Error("No module named 'fcntl'"));
  assert.ok(translate('zh-Hant', raw.key, raw.params).includes("No module named 'fcntl'"));
  assert.equal(translate('fr', 'button.watch'), translations.en['button.watch']);
  assert.equal(translate('en', 'missing.key'), 'missing.key');
});
