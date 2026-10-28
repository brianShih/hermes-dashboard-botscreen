# Bot Screen UI/UX and localization

[繁體中文](DESIGN.md) | **English**

Plugin UI version: 0.4.0. Installer version: 0.5.0. This contract covers the Dashboard plugin, not the Electron application.

## Interaction

| State | Primary action |
|---|---|
| Stopped | Start and watch |
| Watching | Take control |
| Controlling | Hand back control |
| Hermes disconnected | Reconnect |
| Viewer timeout | Retry viewing |

Secondary actions belong in the more menu. Reconnect is disabled while controlling. Input becomes active only after confirmed acquisition; reconnection begins in view mode. A fullscreen request failure does not revoke otherwise valid control. Server-side leases and input filtering enforce ownership.

## Layout and accessibility

Use dark green surfaces, warm white text, and amber control emphasis. Pair status colors with text/icons. Fill available viewport space while preserving desktop aspect ratio. Keep text readable, mobile targets at least 44px, native button semantics, and visible keyboard focus. Support Enter/Tab/Escape, outside dismissal, reduced motion, and polite status announcements; hide decorative icons from assistive technology.

Scope CSS to the plugin. Do not change host authentication, telemetry consent, or global styles. A viewer connection times out after 15 seconds and offers recovery.

## Languages

Provide `en`, `zh-Hant`, and `zh-Hans` dictionaries with matching keys and interpolation placeholders. Users can follow Hermes or save a choice at `bot-screen:language:v1`. Recognized host aliases map to supported languages; unknown host locales fall back to English. Browser detection applies when host locale is missing.

Changing language updates existing interface messages without reconnecting, resetting the lease, or modifying server configuration. Raw backend diagnostics remain available. Adding a locale requires updating locale registration/aliases, parity tests, and the built bundle. Localization adds no runtime framework dependency.

Current-host acceptance is documented in evidence; it does not mean this plugin is already installed on every destination machine.
