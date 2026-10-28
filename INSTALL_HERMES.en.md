# Installing Bot Screen into Hermes

[繁體中文](INSTALL_HERMES.md) | **English**

For full frontend/backend integration, isolated profile setup, backups, rollback, and readiness checks, use [the one-click installer](ONE_CLICK.en.md). The manual procedure below is for maintainers; `scripts/install-plugin.py` handles the frontend only.

## Compatibility and frontend

The target Hermes must provide the Dashboard plugin SDK including `buildWsUrl`, display RPC endpoints, and `/api/display/ws` ticket/lease/input filtering. A usable Linux desktop backend is required. This project records a specific source snapshot; compatibility with arbitrary Hermes versions is not assumed.

The plugin includes prebuilt assets. To rebuild, run `npm ci` then `node build.mjs` in `bot-screen-plugin/`.

Create a dedicated profile without cloning personal secrets:

```bash
hermes profile create bot-screen-lab --no-alias --no-skills
python scripts/install-plugin.py --hermes-root /opt/hermes-agent --profile-home /path/to/bot-screen-lab --check-only
python scripts/install-plugin.py --hermes-root /opt/hermes-agent --profile-home /path/to/bot-screen-lab
```

Use actual paths. For a Dashboard owned by a shared data home, supply `--dashboard-home` as described by the script help. `--replace` is an explicit frontend replacement path with backups. Passing frontend checks does not establish backend runtime readiness.

## Desktop and backend

Docker mode needs a running Docker installation and the desktop image. Native Linux mode needs Xvnc/Xfce and the runtime's desktop dependencies. Do not change an existing remote or sandbox backend merely to make the UI start. Windows Dashboard support uses the cross-platform Docker adapter; Windows does not provide the Linux desktop natively.

Apply only compatible core fixes, preserving unrelated local changes. See [cross-platform patching](CROSS_PLATFORM.en.md) and `patches/runtime-linux-identity.patch`. Restart the Dashboard backend after Python changes.

For an isolated profile-specific test instance:

```bash
hermes -p bot-screen-lab dashboard --isolated --no-open --host 127.0.0.1 --port 9124
```

Keep the listener on loopback; use a controlled SSH tunnel when remote access is needed.

## Verify, customize, remove

Check live rendering, view-only input blocking, takeover, handback, reconnection, and fullscreen. The repository's browser acceptance scripts target their dedicated lab and should not be pointed casually at personal sessions.

Languages are Traditional Chinese, Simplified Chinese, and English. The preference key is `bot-screen:language:v1`; dictionary files live under `bot-screen-plugin/src/locales/`. Following Hermes uses recognized host locales with an English fallback. Language changes do not reset the connection or lease.

Removing the plugin directory disables its frontend without deleting profile data. Core patches have a separate lifecycle. Prefer the one-click installer's recorded rollback for installations made by that installer; it refuses to overwrite subsequent edits.
