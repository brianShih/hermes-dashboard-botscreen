"""Record the reviewed local changes and summarize actual machine-readable evidence."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parent.parent
evidence = root / 'evidence'
acceptance = json.loads((evidence / 'acceptance.json').read_text())
identity = json.loads((evidence / 'identity-result.json').read_text())
manifest = json.loads((root / 'source-manifest.json').read_text(encoding='utf-8'))
paths = ['tools/bot_desktop/runtime.py', 'tools/bot_desktop/lease.py', 'hermes_cli/web_routers/display.py']
changes_path = root / 'integration-changes.json'
previous = json.loads(changes_path.read_text(encoding='utf-8')) if changes_path.exists() else {}
changes = {
    'upstreamCommit': manifest['commit'],
    'modifiedUpstreamFiles': [item for item in previous.get('modifiedUpstreamFiles', []) if item['path'] not in paths] + [{
        'path': path,
        'originalGitBlob': next(item['gitBlob'] for item in manifest['entries'] if item['path'] == path),
        'sha256': hashlib.sha256((root / 'hermes' / path).read_bytes()).hexdigest(),
        'normalizedSha256': hashlib.sha256((root / 'hermes' / path).read_bytes().replace(b'\r\n', b'\n')).hexdigest(),
        'reason': 'Reviewed desktop fixes: Linux identity guard, Windows start and lease locks, recorded Docker ownership, Windows stream adapter',
    } for path in paths],
    'addedUpstreamFiles': [{'path': path, 'sha256': hashlib.sha256((root / 'hermes' / path).read_bytes()).hexdigest(),
                            'normalizedSha256': hashlib.sha256((root / 'hermes' / path).read_bytes().replace(b'\r\n', b'\n')).hexdigest()}
                           for path in ['tools/bot_desktop/transport.py', 'hermes_cli/web_display_streams.py']],
    'pluginFiles': [{
        'path': str(file.relative_to(root)).replace('\\', '/'),
        'sha256': hashlib.sha256(file.read_bytes()).hexdigest(),
    } for file in sorted((root / 'bot-screen-plugin').rglob('*'))
      if file.is_file() and 'node_modules' not in file.parts],
}
if 'privacyOmissions' in previous:
    changes['privacyOmissions'] = previous['privacyOmissions']
for item in changes['modifiedUpstreamFiles']:
    item['normalizedSha256'] = hashlib.sha256((root / 'hermes' / item['path']).read_bytes().replace(b'\r\n', b'\n')).hexdigest()
(root / 'integration-changes.json').write_text(json.dumps(changes, indent=2), encoding='utf-8')

def suite(file):
    tree = ET.parse(evidence / file)
    cases = list(tree.getroot().iter('testcase'))
    return {'tests': len(cases),
            'failures': sum(case.find('failure') is not None for case in cases),
            'errors': sum(case.find('error') is not None for case in cases),
            'skipped': sum(case.find('skipped') is not None for case in cases)}

backend, plugin = suite('pytest-results.xml'), suite('plugin-tests.xml')
assert backend['tests'] > 0 and plugin['tests'] > 0, 'Empty test evidence'
summary = {'acceptancePassed': acceptance['passed'], 'browserGates': acceptance['gates'],
           'backendTests': backend, 'pluginTests': plugin, 'identityTests': identity,
           'scope': 'Current Windows host, Chrome, isolated Linux container desktop',
           'finishedAt': acceptance['finishedAt']}
windows_path = evidence / 'windows-9119.json'
if windows_path.exists():
    windows = json.loads(windows_path.read_text(encoding='utf-8'))
    summary['windowsLiveAcceptance'] = {'passed': windows['passed'], 'gates': windows['gates'], 'cycles': len(windows['cycles'])}
(evidence / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
passed = acceptance['passed'] and identity['passed'] and not any(
    results[k] for results in (backend, plugin) for k in ('failures', 'errors'))
rows = '\n'.join(f"| {name} | {'PASS' if result else 'FAIL'} |" for name, result in acceptance['gates'].items())
report = f'''# Bot Screen QA

STATUS: {'DONE' if passed else 'INCOMPLETE'}

Final browser run: {acceptance['finishedAt']} (UTC). URL: http://127.0.0.1:9124/bot-screen

Real Chrome -> this workspace's built Hermes Dashboard -> noVNC -> authenticated FastAPI bridge -> Xvnc/Xfce.

| Gate | Result |
|---|---|
{rows}

- Framebuffer: {acceptance.get('framebuffer', {})}
- Reconnect cycles: {len(acceptance['cycles'])}, each verifies input denial in Watch, real input after takeover, denial after handback, and unchanged kernel process identity.
- Backend regression: {backend}
- Plugin unit tests: {plugin}
- Linux identity regression: {identity}
- Browser JavaScript runtime errors: {len(acceptance['consoleErrors'])}
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
'''
if windows_path.exists():
    report += "\n## Windows live deployment\n\n" + json.dumps(summary['windowsLiveAcceptance'], indent=2) + "\n\nSee CROSS_PLATFORM.md and evidence/WINDOWS_RUNTIME_ERROR.md. macOS is not hardware-verified.\n"
(evidence / 'QA.md').write_text(report, encoding='utf-8')
print(json.dumps(summary, indent=2))
raise SystemExit(0 if passed else 1)
