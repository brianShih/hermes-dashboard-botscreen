# Bot Screen QA

STATUS: DONE

Final browser run: 2026-10-27T15:15:07.396Z (UTC). URL: http://127.0.0.1:9124/bot-screen

Real Chrome -> this workspace's built Hermes Dashboard -> noVNC -> authenticated FastAPI bridge -> Xvnc/Xfce.

| Gate | Result |
|---|---|
| isolatedReadOnlySourceMounts | PASS |
| pluginDiscovered | PASS |
| desktopStarted | PASS |
| realFramebuffer | PASS |
| watchInputBlocked | PASS |
| realHumanInput | PASS |
| handbackInputBlocked | PASS |
| abnormalDisconnectRetainsHumanLease | PASS |
| reconnectThreeCycles | PASS |
| singleUseTicketEnforced | PASS |
| unauthorizedRejected | PASS |
| noBrowserRuntimeErrors | PASS |

- Framebuffer: {'width': 1440, 'height': 900, 'colors': 256}
- Reconnect cycles: 3, each verifies input denial in Watch, real input after takeover, denial after handback, and unchanged kernel process identity.
- Backend regression: {'tests': 38, 'failures': 0, 'errors': 0, 'skipped': 0}
- Plugin unit tests: {'tests': 12, 'failures': 0, 'errors': 0, 'skipped': 0}
- Linux identity regression: {'tests': 9, 'failures': 0, 'errors': 0, 'passed': True}
- Browser JavaScript runtime errors: 0
- Initial baseline: required framebuffer workflow failed; final scoped gates passed. No whole-product health score is inferred.

## Fixes and investigation

1. Ported the lab's process identity repair into local runtime.py. A live launcher's psutil epoch drifted by 1 second; kernel boot/namespace/start-tick identity avoids the false dead-process verdict. Baseline and fixed regressions are retained.
2. Plugin uses the host SDK auth URL, explicit reconnection, generation checks, profile/viewer-scoped lease events, and fail-closed controls.
3. Test-only fixes: preserve native WebSocket prototype under instrumentation; normal managed Tk fixture with actual input coordinates; account for the documented public plugin-manifest endpoint and test protected /api/config instead. Temporary backend diagnostics were removed.

## Evidence

- acceptance.json: final run, not historical failures.
- takeover.png, handback.png, reconnected.png: screenshots of the real desktop.
- pytest-results.xml, plugin-tests.xml, identity-result.json: machine-readable regressions.
- acceptance-bootstrap-pass.json: initial container's earlier pass; latest acceptance.json supersedes it.
- integration-changes.json at project root: upstream patch and plugin content hashes.

## Limits

Current-host Linux container acceptance only. Not a full VM, native Windows desktop, clean-machine install, overnight stability, physical Wi-Fi failure, or concurrent multi-user acceptance. Disconnects were induced using abnormal WebSocket close code 4002. Test inputs wait 350 ms after takeover to allow the official bridge's bounded 250 ms lease refresh. No model/API inference calls or desktop external-account sign-in.

The existing upstream backend tests emitted one Starlette/httpx deprecation warning; all 38 tests passed. No PR or commit was created because this workspace is an archived source tree without a Git repository.

## Windows live deployment

{
  "passed": true,
  "gates": {
    "freshWindowsBackendReady": true,
    "startReusesExistingContainer": true,
    "realFramebufferAndInput": true,
    "threeDisconnectReconnectCycles": true,
    "handbackAndWatchGate": true
  },
  "cycles": 3
}

See CROSS_PLATFORM.md and evidence/WINDOWS_RUNTIME_ERROR.md. macOS is not hardware-verified.
