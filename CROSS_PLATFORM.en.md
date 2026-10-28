# Cross-platform Bot Screen backend

[繁體中文](CROSS_PLATFORM.md) | **English**

For normal installation, use [the one-click guide](ONE_CLICK.en.md). Dashboard may run on Windows or Linux; its desktop environment remains Linux. macOS has not been accepted on real hardware.

## Transport and ownership

`tools/bot_desktop/transport.py` reconnects to the exact Docker container recorded for the profile without relying on an in-process terminal registry. It checks the profile marker, desktop directory, complete container ID, running state, and `hermes-agent`/`hermes-profile` labels. Mismatches fail closed. The Docker executable comes from the existing trusted resolver, not an arbitrary marker command.

Windows uses worker-thread pipe reads/writes with bounded write backpressure. Closing the connection terminates this Docker exec client and closes its pipes, leaving the container desktop running. Linux retains its asyncio pipe path. Ticket checks, origin checks, RFB filtering, and control ownership remain shared.

Windows startup and lease locks use real inter-process locking; Linux retains flock. No platform bypasses the lock because `fcntl` is unavailable.

## Manual patching

`scripts/install-plugin.py` installs the frontend only. The one-click installer also applies recognized backend fixes. For manual core patching, back up `tools/bot_desktop/runtime.py`, `tools/bot_desktop/lease.py`, and `hermes_cli/web_routers/display.py`.

```powershell
git -C <HermesRoot> apply --ignore-space-change --check <PackageRoot>/patches/runtime-windows-lock.patch
git -C <HermesRoot> apply --ignore-space-change <PackageRoot>/patches/runtime-windows-lock.patch
git -C <HermesRoot> apply --ignore-space-change --check <PackageRoot>/patches/desktop-cross-platform.patch
git -C <HermesRoot> apply --ignore-space-change <PackageRoot>/patches/desktop-cross-platform.patch
```

Skip the first patch if that fix is already installed. The second adds `tools/bot_desktop/transport.py` and `hermes_cli/web_display_streams.py`. A failed check requires comparison with local code; do not force replacement. These patches target the recorded source shape, not arbitrary Hermes releases. Linux identity has its own patch.

Restart the Python process serving Dashboard after applying core changes. Refreshing a page or restarting Messaging Gateway does not reload that process.

## Verification and limits

Tests cover real process locks (`test-runtime-lock.py`, `test-lease-processes.py`), transport ownership/backpressure/cleanup (`test-transport.py`), real RFB on Windows (`test-live-rfb.py`), and browser takeover/handback/reconnection (`windows-acceptance.mjs`, `acceptance.mjs`) under `scripts/`.

See `evidence/windows-9119.json` and `evidence/acceptance.json`. SSH, Singularity, shared-container keys, high concurrency, prolonged load, and macOS acceptance are outside this work. Existing start/stop lifecycle remains managed by the terminal backend.
