# Isolated integration lab

[繁體中文](INTEGRATION.md) | **English**

This is the development lab on port 9124. Installing into an existing Dashboard, normally port 9119, uses [the one-click installer](ONE_CLICK.en.md).

The `bot-screen-integration` container serves an isolated Hermes home and `bot-screen-lab` profile. Host access binds to `127.0.0.1:9124`; the container server binds internally and remains authentication protected. Source/plugin/integration mounts are read-only. User home, personal browser profiles, and the host Docker socket are not mounted.

Lab credentials are generated inside the container at `/lab/test-login.json` and must not be published. The dedicated browser launcher uses an isolated browser profile. Tests do not require model calls, external account logins, or Messaging Gateway.

The lab runtime image and preparation scripts depend on the recorded lab setup; they are not substitutes for the portable installer on a clean machine. Follow the Chinese lab guide for the setup-specific commands and start/stop scripts.

## Build and acceptance

Build the Hermes web workspace with its pinned dependency setup, then build `bot-screen-plugin` using `npm ci` and `node build.mjs`. Frontend changes do not automatically install core Python fixes.

`node scripts/acceptance.mjs` exercises the isolated Linux lab. It uses a real desktop test window with synthetic input, verifies view-only blocking, takeover, handback, fullscreen, and abnormal WebSocket disconnection/reconnection. Ticket replay and unauthenticated access are checked. Run it against its intended lab configuration, not an arbitrary personal Dashboard.

Linux process identity uses boot identity, PID namespace, and process start ticks to avoid treating a recycled PID as the original process. Subsequent Windows locking and transport fixes are documented in [the cross-platform guide](CROSS_PLATFORM.en.md); the first lab runtime fix is only part of the final integration.

Acceptance records describe completed tests, not a promise that lab containers are currently running. Use the recorded evidence and current service checks to distinguish source, lab, and daily Dashboard state.
