import en from './locales/en.json' with { type: 'json' };
import traditional from './locales/zh-Hant.json' with { type: 'json' };
import simplified from './locales/zh-Hans.json' with { type: 'json' };

export const LANGUAGE_STORAGE_KEY = 'bot-screen:language:v1';
export const SUPPORTED_LANGUAGES = [
  { value: 'zh-Hant', label: '繁體中文' },
  { value: 'zh-Hans', label: '简体中文' },
  { value: 'en', label: 'English' },
];
export const translations = { en, 'zh-Hant': traditional, 'zh-Hans': simplified };

export function normalizeLocale(value) {
  const locale = String(value || '').trim().replaceAll('_', '-').toLowerCase();
  if (/^zh-(hant|tw|hk|mo)(-|$)/.test(locale)) return 'zh-Hant';
  if (/^zh(-|$)/.test(locale)) return 'zh-Hans';
  if (/^en(-|$)/.test(locale)) return 'en';
  return null;
}
export function validPreference(value) {
  return value === 'auto' || Object.hasOwn(translations, value);
}
export function readPreference(storage) {
  try { const value = storage.getItem(LANGUAGE_STORAGE_KEY); return validPreference(value) ? value : 'auto'; }
  catch { return 'auto'; }
}
export function savePreference(storage, value) {
  if (!validPreference(value)) return false;
  try { storage.setItem(LANGUAGE_STORAGE_KEY, value); return true; }
  catch { return false; }
}
export function resolveLocale(preference, hostLocale, browserLocales = []) {
  if (preference !== 'auto' && validPreference(preference)) return preference;
  if (hostLocale) return normalizeLocale(hostLocale) || 'en';
  for (const candidate of browserLocales) {
    const locale = normalizeLocale(candidate);
    if (locale) return locale;
  }
  return 'en';
}
export function translate(locale, key, params = {}) {
  const dictionary = translations[normalizeLocale(locale) || 'en'];
  const text = dictionary[key] || en[key] || key;
  return text.replace(/\{(\w+)\}/g, (match, name) => Object.hasOwn(params, name) ? String(params[name]) : match);
}
export function errorMessage(error) {
  const key = `error.${error?.code}`;
  if (Object.hasOwn(en, key)) return { key };
  return { key: 'error.backend', params: { detail: error?.message || String(error) } };
}
