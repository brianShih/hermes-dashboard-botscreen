"""Disposable install/reinstall/rollback acceptance; never changes the daily installation."""
import argparse
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time

parser = argparse.ArgumentParser()
parser.add_argument('--work', type=Path, required=True)
parser.add_argument('--baseline', type=Path, required=True)
parser.add_argument('--backend', choices=['docker', 'native'], required=True)
parser.add_argument('--entry', choices=['python', 'shell', 'powershell'], default='python')
parser.add_argument('--report', type=Path)
parser.add_argument('--package-root', type=Path)
parser.add_argument('--browser-review', action='store_true')
args = parser.parse_args()
project = Path(__file__).resolve().parent.parent
package = args.package_root.resolve() if args.package_root else project
work = args.work.resolve()
assert not work.exists(), 'Use a fresh acceptance directory'
work.mkdir(parents=True)
source = work / 'Hermes source with spaces'
home = work / 'Hermes isolated home'
source.mkdir(); home.mkdir()
prefixes = ('agent/', 'hermes_cli/', 'tools/', 'gateway/', 'tui_gateway/', 'plugins/', 'pm/', 'hermes_platform/', 'cron/', 'acp_adapter/')
manifest = json.loads((project / 'source-manifest.json').read_text(encoding='utf-8'))
for entry in manifest['entries']:
    name = entry['path']
    if '/' in name and not name.startswith(prefixes) and name != 'web/src/plugins/registry.ts': continue
    target = source / name; target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(project / 'hermes' / name, target)
for name in ['tools/bot_desktop/runtime.py', 'tools/bot_desktop/lease.py', 'hermes_cli/web_routers/display.py']:
    shutil.copy2(args.baseline / name, source / name)
if (project / 'hermes/hermes_cli/web_dist').is_dir():
    shutil.copytree(project / 'hermes/hermes_cli/web_dist', source / 'hermes_cli/web_dist', dirs_exist_ok=True)
(home / 'config.yaml').write_text('# acceptance user comment\nplugins:\n  enabled: [keep-existing]\ninstaller_acceptance: preserve\n', encoding='utf-8')
(home / '.env').write_text('INSTALLER_QA_SENTINEL=not-a-real-key-do-not-clone\n', encoding='utf-8')
before_secret = (home / '.env').read_bytes()
before_config = (home / 'config.yaml').read_bytes()
before_core = {name: (source / name).read_bytes() for name in ['tools/bot_desktop/runtime.py', 'tools/bot_desktop/lease.py', 'hermes_cli/web_routers/display.py']}
port = 9127
try:
    with socket.create_connection(('127.0.0.1', port), timeout=1): raise AssertionError('Acceptance port is already occupied')
except OSError: pass
entry = {'python': [sys.executable, str(package / 'scripts/install-dashboard.py')],
         'shell': ['bash', str(package / 'install.sh')],
         'powershell': ['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(package / 'Install.ps1')]}[args.entry]
base = entry + ['--hermes-root', str(source), '--hermes-home', str(home),
        '--python', sys.executable, '--backend', args.backend, '--isolated-dashboard', '--port', str(port), '--no-open']
result = {'platform': sys.platform, 'backend': args.backend, 'gates': {}, 'passed': False}
desktop_container = None
server_pid = None

def run(extra=(), expected=0):
    test_env = dict(os.environ); test_env['OPENAI_API_KEY'] = 'installer-qa-exported-credential-do-not-forward'
    completed = subprocess.run(base + list(extra), capture_output=True, text=True, encoding='utf-8', timeout=240, env=test_env)
    (work / 'last-command.log').write_text(completed.stdout + '\n' + completed.stderr, encoding='utf-8')
    if completed.returncode != expected:
        raise AssertionError('Installer returned ' + str(completed.returncode) + '; inspect disposable last-command.log')
    return completed

try:
    run(['--check-only'])
    assert (home / 'config.yaml').read_bytes() == before_config
    assert not (home / 'profiles').exists()
    result['gates']['preflightDoesNotMutateTargets'] = True
    print('Preflight passed; installing disposable fixture...', flush=True)
    run()
    report = json.loads((home / 'runtime/bot-screen-installer/result.json').read_text())
    assert report['status'] == 'ready' and report['desktop']['rfbHandshake']
    server_pid = report['dashboard'].get('pid')
    result['gates']['freshInstallDashboardAndRealDesktop'] = True
    if args.browser_review:
        subprocess.run(['node', str(project / 'scripts/installer-browser-review.mjs'), f'http://127.0.0.1:{port}'], check=True, timeout=120, cwd=project)
        result['gates']['installedBrowserFlow'] = True
    marker = home / 'profiles/bot-screen-lab/bot-desktop/sandbox.json'
    if marker.exists():
        desktop_container = json.loads(marker.read_text())['container']
        container_env = json.loads(subprocess.check_output(['docker', 'inspect', '--format', '{{json .Config.Env}}', desktop_container], text=True))
        assert not any('installer-qa-exported-credential' in item for item in container_env)
        result['gates']['exportedProviderCredentialNotForwarded'] = True
    assert (home / '.env').read_bytes() == before_secret
    assert b'INSTALLER_QA_SENTINEL' not in (home / 'profiles/bot-screen-lab/.env').read_bytes()
    assert 'keep-existing' in (home / 'config.yaml').read_text()
    assert '# acceptance user comment' in (home / 'config.yaml').read_text()
    result['gates']['existingSettingsCommentsAndSecretsPreserved'] = True
    installed_core = {name: (source / name).read_bytes() for name in before_core}
    run()
    second = json.loads((home / 'runtime/bot-screen-installer/result.json').read_text())
    assert second['filesToChange'] == [] and second['backup'] is None
    assert all((source / name).read_bytes() == data for name, data in installed_core.items())
    result['gates']['repeatInstallNoChanges'] = True
    run(['--rollback', 'latest'])
    assert all((source / name).read_bytes() == data for name, data in before_core.items())
    assert (home / 'config.yaml').read_bytes() == before_config
    assert (home / '.env').read_bytes() == before_secret
    assert not (source / 'tools/bot_desktop/transport.py').exists()
    result['gates']['rollbackRestoresOriginalBytes'] = True
    result['passed'] = True
except Exception as error:
    result['error'] = str(error)
    raise
finally:
    # Only the process this acceptance run launched may be stopped here.
    if server_pid:
        import psutil
        try: psutil.Process(server_pid).terminate()
        except psutil.NoSuchProcess: pass
    output = args.report or project / 'evidence' / ('installer-' + sys.platform + '.json')
    output.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
    # The disposable desktop/container is retained for inspection. No unrelated
    # container, browser or filesystem tree is deleted by this harness.
