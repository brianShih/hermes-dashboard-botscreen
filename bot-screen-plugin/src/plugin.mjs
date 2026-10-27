import RFBModule from '@novnc/novnc/lib/rfb.js';
import { ScreenController, RpcClient, socketURL } from './screen.mjs';
import styles from './styles.css';
import { LANGUAGE_STORAGE_KEY, SUPPORTED_LANGUAGES, readPreference, savePreference, resolveLocale, translate, errorMessage } from './i18n.mjs';
const useHostI18n = window.__HERMES_PLUGIN_SDK__.useI18n || (() => ({}));
const codedError = (code) => Object.assign(new Error(code), { code });

const RFB = typeof RFBModule === 'function' ? RFBModule : RFBModule.default;
const { React: R } = window.__HERMES_PLUGIN_SDK__;
const h = R.createElement;
const paths = {
  screen: ['M3 4h18v12H3z', 'M8 21h8M12 16v5'],
  eye: ['M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12Z', 'M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0'],
  hand: ['M8 13V5a2 2 0 0 1 4 0v7-8a2 2 0 0 1 4 0v8-6a2 2 0 0 1 4 0v9c0 4-3 7-7 7h-1c-2 0-3-1-4-2l-5-6a2 2 0 0 1 3-3l2 2'],
  refresh: ['M20 7v5h-5', 'M4 17v-5h5', 'M6 7a7 7 0 0 1 12-1l2 3M4 15l2 3a7 7 0 0 0 12-1'],
  expand: ['M8 3H3v5M16 3h5v5M21 16v5h-5M3 16v5h5'],
  arrow: ['M5 12h14M13 6l6 6-6 6'],
  check: ['m5 12 4 4L19 6'],
  shield: ['M12 3 4 6v6c0 5 8 9 8 9s8-4 8-9V6l-8-3Z', 'm8 12 3 3 5-6'],
  alert: ['m12 3 10 18H2L12 3Z', 'M12 9v5M12 17v.1'],
};
const icon = (name, extra = '') => h('svg', { className: `bs-icon ${extra}`, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: 1.6, strokeLinecap: 'round', strokeLinejoin: 'round', 'aria-hidden': true }, ...(paths[name] || paths.screen).map((d, i) => h('path', { d, key: i })));

function Page() {
  const host = useHostI18n();
  const [preference, setPreference] = R.useState(() => { try { return readPreference(window.localStorage); } catch { return 'auto'; } });
  const locale = resolveLocale(preference, host?.locale || document.documentElement.lang, navigator.languages);
  const t = (key, params) => translate(locale, key, params);
  const [message, setMessage] = R.useState({ key: 'message.connecting' });
  const say = (key, params) => setMessage({ key, params });
  const showError = error => setMessage(errorMessage(error));
  function changeLanguage(value) { setMenu(false); setPreference(value); try { savePreference(window.localStorage, value); } catch {} }
  R.useEffect(() => {
    const sync = event => { if (event.key === LANGUAGE_STORAGE_KEY || event.key === null) { try { setPreference(readPreference(window.localStorage)); } catch {} } };
    window.addEventListener('storage', sync);
    return () => window.removeEventListener('storage', sync);
  }, []);
  const [ready, setReady] = R.useState(false);
  const [running, setRunning] = R.useState(false);
  const [connected, setConnected] = R.useState(false);
  const [busy, setBusy] = R.useState('');
  const [control, setControl] = R.useState(false);
  const [lease, setLease] = R.useState('unknown');
  const [failed, setFailed] = R.useState(false);
  const [loadingFrame, setLoadingFrame] = R.useState(false);
  const [availableHeight, setAvailableHeight] = R.useState('calc(100dvh - 120px)');
  const [fullscreen, setFullscreen] = R.useState(false);
  const [menu, setMenu] = R.useState(false);
  const shell = R.useRef(null), target = R.useRef(null), rpc = R.useRef(null);
  const controller = R.useRef(null), rfb = R.useRef(null);
  const generation = R.useRef(0), viewerGeneration = R.useRef(0), alive = R.useRef(true);
  const menuRef = R.useRef(null);

  function disable() {
    if (rfb.current) rfb.current.viewOnly = true;
    setControl(false);
    if (controller.current) controller.current.controlling = false;
  }
  function dropViewer() {
    viewerGeneration.current++;
    const old = rfb.current;
    rfb.current = null;
    old?.disconnect();
    setConnected(false);
    setLoadingFrame(false);
    disable();
  }
  async function connect() {
    const seq = ++generation.current;
    dropViewer();
    rpc.current?.close();
    setReady(false);
    setFailed(false);
    say('message.connecting');
    const client = new RpcClient();
    const c = new ScreenController((method, params) => client.request(method, params));
    rpc.current = client;
    controller.current = c;
    const current = () => alive.current && generation.current === seq;
    client.onDisconnect = () => {
      if (!current()) return;
      dropViewer();
      c.disconnect();
      setReady(false);
      setFailed(true);
      say('message.disconnected');
    };
    client.onEvent = event => {
      const e = event.method === 'event' ? event.params : null;
      if (!current() || e?.payload?.profile_key !== c.profileKey) return;
      if (e.type === 'display.lease') {
        const next = e.payload.lease;
        if (next?.holder !== 'human' || next.viewer_hash !== c.viewerHash) disable();
        setLease(next?.holder || 'unknown');
      }
      if (e.type === 'display.status') {
        setRunning(!!e.payload.running);
        if (!e.payload.running) { dropViewer(); say('message.stoppedRestart'); }
      }
    };
    try {
      const status = await window.__HERMES_PLUGIN_SDK__.api.getStatus();
      if (!current()) return;
      if (!status.profiles?.includes('bot-screen-lab')) throw codedError('profileMissing');
      await client.connect();
      if (!current()) { client.close(); return; }
      const state = await c.call('display.status');
      if (!current()) return;
      c.profileKey = state.profile_key;
      setReady(true);
      setRunning(!!state.running);
      setLease(state.lease?.holder || 'unknown');
      say(state.running ? 'message.runningPrompt' : 'message.ready');
    } catch (error) {
      if (current()) { client.close(); setFailed(true); showError(error); }
    }
  }

  R.useEffect(() => {
    alive.current = true;
    void connect();
    return () => { alive.current = false; generation.current++; viewerGeneration.current++; rfb.current?.disconnect(); rpc.current?.close(); };
  }, []);
  R.useLayoutEffect(() => {
    const fit = () => {
      if (!shell.current) return;
      setAvailableHeight(Math.max(320, window.innerHeight - shell.current.getBoundingClientRect().top - 8));
      setFullscreen(document.fullscreenElement === shell.current);
    };
    const observer = new ResizeObserver(fit);
    observer.observe(shell.current.parentElement);
    fit();
    window.addEventListener('resize', fit);
    document.addEventListener('fullscreenchange', fit);
    return () => { observer.disconnect(); window.removeEventListener('resize', fit); document.removeEventListener('fullscreenchange', fit); };
  }, []);
  R.useEffect(() => {
    if (!menu) return;
    const outside = event => { if (!menuRef.current?.contains(event.target)) setMenu(false); };
    const escape = event => { if (event.key === 'Escape') { setMenu(false); menuRef.current?.querySelector('button')?.focus(); } };
    document.addEventListener('pointerdown', outside);
    document.addEventListener('keydown', escape);
    return () => { document.removeEventListener('pointerdown', outside); document.removeEventListener('keydown', escape); };
  }, [menu]);

  async function act(name, fn) {
    if (busy) return;
    setBusy(name);
    setFailed(false);
    setMenu(false);
    try { await fn(); }
    catch (error) { if (name !== 'fullscreen') disable(); setLoadingFrame(false); setFailed(true); showError(error); }
    finally { if (alive.current) setBusy(''); }
  }
  async function start() {
    say('message.starting');
    const state = await controller.current.start();
    if (!state.running) throw (state.blocker ? Error(state.blocker) : codedError('desktopNotStarted'));
    setRunning(true);
    setLease(state.lease?.holder || 'unknown');
    say('message.started');
  }
  async function watch() {
    dropViewer();
    const seq = viewerGeneration.current, c = controller.current;
    setLoadingFrame(true);
    say('message.viewerConnecting');
    let result;
    try { result = await c.observe(); }
    catch (error) { setLoadingFrame(false); throw error; }
    if (!alive.current || seq !== viewerGeneration.current) return;
    if (result.path !== '/api/display/ws') { setLoadingFrame(false); throw codedError('unexpectedEndpoint'); }
    const base = window.__HERMES_BASE_PATH__ || '';
    const viewer = new RFB(target.current, socketURL(location.origin, base + result.path, 'display_ticket', result.ticket));
    rfb.current = viewer;
    viewer.viewOnly = true;
    viewer.scaleViewport = true;
    viewer.resizeSession = false;
    const current = () => alive.current && seq === viewerGeneration.current;
    const timer = setTimeout(() => {
      if (!current()) return;
      dropViewer(); setFailed(true);
      say('message.viewerTimeout');
    }, 15000);
    viewer.addEventListener('connect', () => {
      clearTimeout(timer);
      if (!current()) return;
      setConnected(true); setLoadingFrame(false); setFailed(false);
      setLease(result.lease?.holder || 'unknown');
      say('message.watching');
    });
    viewer.addEventListener('disconnect', () => {
      clearTimeout(timer);
      if (!current()) return;
      disable(); setConnected(false); setLoadingFrame(false); setFailed(true);
      say('message.viewerDisconnected');
    });
    viewer.addEventListener('securityfailure', () => {
      clearTimeout(timer);
      if (!current()) return;
      disable(); setLoadingFrame(false); setFailed(true);
      say('message.viewerAuthFailed');
    });
  }
  const action = (name, label, symbol, fn, options = {}) => h('button', {
    type: 'button', 'data-action': name, className: `bs-button ${options.primary ? 'bs-button-primary' : ''} ${options.quiet ? 'bs-button-quiet' : ''} ${options.warning ? 'bs-button-warning' : ''}`,
    disabled: !!busy || options.disabled, onClick: () => act(name, fn), title: options.title,
    'aria-label': options.label || label,
  }, busy === name ? h('span', { className: 'bs-spinner', 'aria-hidden': true }) : icon(symbol), label);
  const otherHuman = lease === 'human' && !control;
  const emptyTitle = !ready ? failed ? t('empty.disconnected') : t('empty.connecting') : failed ? t('empty.reconnect') : running ? t('empty.ready') : t('empty.start');
  const emptyCopy = !ready ? t('empty.reconnectCopy') : otherHuman ? t('empty.retainedCopy') : running ? t('empty.readyCopy') : t('empty.startCopy');

  return h('section', {
    ref: shell, className: `bs-root ${control ? 'bs-controlling' : ''}`, 'data-testid': 'bot-screen',
    lang: locale, 'data-locale': locale, 'data-language-preference': preference, 'data-running': String(running), 'data-connected': String(connected),
    'data-connection': ready ? 'ready' : failed ? 'disconnected' : 'connecting', 'aria-busy': !!busy,
    style: { height: availableHeight },
  },
  h('style', null, styles),
  h('header', { className: 'bs-header' },
    h('div', { className: 'bs-title-group' },
      h('div', { className: 'bs-brand-mark' }, icon('screen')),
      h('div', null, h('h1', null, 'Bot Screen'), h('p', { className: 'bs-subtitle' }, t('subtitle'), h('span', null, ' / '), 'bot-screen-lab'))),
    h('div', { className: 'bs-header-actions' },
      h('span', { className: `bs-connection ${ready ? 'is-online' : ''}` }, h('i'), ready ? t('connection.online') : failed ? t('connection.offline') : t('connection.connecting')),
      action('fullscreen', fullscreen ? t('button.exitFullscreen') : t('button.fullscreen'), 'expand', () => document.fullscreenElement ? document.exitFullscreen() : shell.current.requestFullscreen(), { quiet: true }),
      h('div', { className: 'bs-more', ref: menuRef },
        h('button', { type: 'button', className: 'bs-more-button', 'aria-label': t('button.more'), 'aria-expanded': menu, onClick: () => setMenu(!menu) }, '•••'),
        menu && h('div', { className: 'bs-menu' },
          h('label', { className: 'bs-language', htmlFor: 'bs-language-select' }, t('language.label'),
            h('select', { id: 'bs-language-select', 'data-testid': 'language-select', value: preference, onChange: event => changeLanguage(event.target.value) },
              h('option', { value: 'auto' }, t('language.auto')),
              ...SUPPORTED_LANGUAGES.map(language => h('option', { key: language.value, value: language.value }, language.label)))),
          action('reconnect', t('button.reconnect'), 'refresh', connect, { disabled: control, title: control ? t('hint.reconnectBlocked') : t('hint.reconnect') }),
          action('status', t('button.refresh'), 'refresh', async () => { const s = await controller.current.call('display.status'); setRunning(!!s.running); setLease(s.lease?.holder || 'unknown'); say(s.running ? 'message.running' : 'message.stopped'); }, { disabled: !ready }),
          action('start', t('button.start'), 'screen', start, { disabled: !ready || running }))))),
  h('div', { className: 'bs-toolbar' },
    h('div', { className: 'bs-mode' },
      icon(control ? 'hand' : 'eye'),
      h('div', null, h('strong', { 'data-testid': 'control-state' }, control ? t('mode.control') : connected ? t('mode.watch') : t('mode.disconnected')),
        h('span', null, control ? t('mode.controlHint') : otherHuman ? t('mode.retainedHint') : t('mode.watchHint')))),
    h('div', { className: 'bs-toolbar-actions' },
      connected && action('watch', t('button.watch'), 'refresh', watch, { quiet: true, disabled: !ready || control, title: t('hint.watch') }),
      connected && (control
        ? action('handback', t('button.handback'), 'arrow', async () => { disable(); await controller.current.handBack(); setLease('agent'); say('message.handedBack'); }, { primary: true, warning: true })
        : action('takeover', t('button.takeover'), 'hand', async () => { const c = controller.current; await c.takeOver(); if (!rfb.current || !connected) throw codedError('viewerGone'); rfb.current.viewOnly = false; rfb.current.focus(); setControl(true); setLease('human'); say('message.controlAcquired'); }, { primary: true, disabled: !ready })))),
  h('div', { className: `bs-notice ${failed || otherHuman ? 'is-warning' : ''}`, role: 'status', 'aria-live': 'polite' },
    icon(failed || otherHuman ? 'alert' : 'check'), h('span', null, t(message.key, message.params))),
  h('div', { className: 'bs-frame' },
    h('div', { className: 'bs-frame-bar' },
      h('span', null, h('i', { className: connected ? 'is-live' : '' }), connected ? t('frame.live') : t('frame.preview')),
      h('span', null, control ? t('frame.inputEnabled') : t('frame.watchOnly'))),
    h('div', { className: 'bs-view-wrap' },
      h('div', { ref: target, 'data-testid': 'screen-viewer', className: 'bs-viewer', role: 'region', 'aria-label': t('frame.label') }),
      !connected && h('div', { className: 'bs-empty' },
        h('div', { className: 'bs-empty-content' },
          h('div', { className: 'bs-empty-icon' }, loadingFrame || busy ? h('span', { className: 'bs-spinner' }) : icon('screen')),
          h('h2', null, loadingFrame ? t('empty.loading') : busy === 'begin' ? t('empty.starting') : emptyTitle),
          h('p', null, loadingFrame ? t('empty.loadingCopy') : emptyCopy),
          !loadingFrame && (!ready
            ? action('reconnect', failed ? t('button.reconnect') : t('button.connecting'), 'refresh', connect, { primary: true, disabled: !failed })
            : running
              ? action('watch', t('button.watch'), 'eye', watch, { primary: true })
              : action('begin', t('button.begin'), 'arrow', async () => { await start(); await watch(); }, { primary: true })),
          h('div', { className: 'bs-empty-points' }, h('span', null, icon('shield'), t('empty.isolated')), h('span', null, icon('eye'), t('empty.viewOnly'))))))),
  h('footer', { className: 'bs-footer' },
    h('span', { 'data-testid': 'lease-state' }, h('i', { className: control || otherHuman ? 'is-human' : '' }), t('lease.label', { holder: t(control ? 'lease.you' : lease === 'human' ? 'lease.human' : lease === 'agent' ? 'lease.agent' : 'lease.unknown') })),
    h('span', null, icon('shield'), t('footer.ticket'), h('span', { className: 'bs-footer-separator' }, '·'), t('footer.retained'))));
}

window.__HERMES_PLUGINS__.register('bot-screen-lab', Page);
