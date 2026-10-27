"""One-click Bot Screen installation into an existing Windows/Linux Hermes."""
from __future__ import annotations
import argparse
import ast
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
from urllib.request import urlopen
import webbrowser

PACKAGE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PACKAGE / 'installer'))
from engine import RELEASE, commit, installation_lock, regular_target, rollback, runtime_plan, sha

def runtime_description(launcher):
    result = subprocess.run([str(launcher), '--print-runtime-command'], capture_output=True, text=True, timeout=60)
    for line in reversed(result.stdout.splitlines()):
        try:
            command = json.loads(line)
            if isinstance(command, list) and len(command) >= 4 and command[1:3] == ['-I', '-c']:
                roots = []
                for item in ast.walk(ast.parse(command[3])):
                    if isinstance(item, ast.Call) and isinstance(item.func, ast.Attribute) and ast.unparse(item.func) == 'sys.path.insert' and len(item.args) == 2:
                        if isinstance(item.args[1], ast.Constant) and isinstance(item.args[1].value, str): roots.append(Path(item.args[1].value))
                return {'python': Path(command[0]), 'roots': roots}
        except (ValueError, SyntaxError): pass
    raise ValueError('This Hermes launcher does not expose its runtime. Pass --hermes-root and --python explicitly')

def discover(options):
    launcher = options.launcher
    if not launcher and options.hermes_root:
        for relative in ['.hermes/bin/hermes.exe', '.hermes/bin/hermes', '.venv/bin/hermes', '.venv/Scripts/hermes.exe']:
            if (options.hermes_root / relative).is_file(): launcher = str(options.hermes_root / relative); break
    if not launcher and not options.hermes_root: launcher = shutil.which('hermes')
    known = []
    if os.environ.get('HERMES_HOME'): known += [Path(os.environ['HERMES_HOME']) / 'hermes-agent']
    if os.name == 'nt' and os.environ.get('LOCALAPPDATA'): known += [Path(os.environ['LOCALAPPDATA']) / 'hermes/hermes-agent']
    known += [Path.home() / '.hermes/hermes-agent', Path.home() / '.hermes']
    if not launcher:
        for root in ([options.hermes_root] if options.hermes_root else known):
            for relative in ['.hermes/bin/hermes.exe', '.hermes/bin/hermes', '.venv/bin/hermes', '.venv/Scripts/hermes.exe']:
                if (Path(root) / relative).is_file(): launcher = str(Path(root) / relative); break
            if launcher: break
    description = None
    if launcher:
        try: description = runtime_description(launcher)
        except ValueError:
            if not options.python or not options.hermes_root: raise
    if options.hermes_root:
        root = options.hermes_root.resolve()
        if description and description['roots'] and root not in {p.resolve() for p in description['roots']}:
            raise ValueError('The selected launcher belongs to another Hermes installation')
    else:
        roots = description['roots'] if description else known
        valid = {p.resolve() for p in roots if (p / 'hermes_cli/main.py').is_file()}
        if len(valid) != 1: raise ValueError('Cannot select one Hermes installation. Pass --hermes-root explicitly')
        root = valid.pop()
    if not (root / 'hermes_cli/main.py').is_file(): raise ValueError('Not a Hermes source installation: --hermes-root')
    python = options.python or (description['python'] if description else None)
    if python is None:
        for relative in ['.venv/bin/python', '.venv/Scripts/python.exe']:
            if (root / relative).is_file(): python = root / relative; break
    if python is None or not Path(python).is_file(): raise ValueError('Hermes Python was not found. Pass --python')
    # Resolving a POSIX venv's python symlink selects the base interpreter and
    # silently drops its dependencies. Preserve the installation's executable.
    return root, Path(python).absolute()

def helper(root, python, home, action, **values):
    code = ('import sys,runpy;sys.path.insert(0,' + repr(str(root)) + ');'
            + ('import hermes_bootstrap;' if (root / 'hermes_bootstrap.py').exists() else '')
            + 'runpy.run_path(' + repr(str(PACKAGE / 'installer/helper.py')) + ',run_name="__main__")')
    if action == 'smoke':
        env = helper(root, python, home.parent.parent, 'child-environment', target=str(home))['environment']
    else:
        env = dict(os.environ)
    env.pop('PYTHONPATH', None); env.pop('PYTHONHOME', None)
    env['HERMES_HOME'] = str(home)
    env['PYTHONIOENCODING'] = 'utf-8'
    env['HERMES_DISABLE_LAZY_INSTALLS'] = '1'
    process = subprocess.run([str(python), '-I', '-c', code], input=json.dumps({'action': action, 'root': str(root), **values}),
                             capture_output=True, text=True, encoding='utf-8', timeout=180, env=env)
    for line in reversed(process.stdout.splitlines()):
        if line.startswith('BOT_SCREEN_RESULT='):
            result = json.loads(line.partition('=')[2])
            if not result['ok']: raise ValueError(result['error'])
            return result['result']
    raise ValueError('Hermes runtime helper failed (' + str(process.returncode) + '); no credentials were printed')

def read(path):
    return path.read_bytes() if path.exists() else None

def prepare(root, home, python, options):
    payload = json.loads((PACKAGE / 'installer/runtime-payload.json').read_text(encoding='utf-8'))
    core = runtime_plan(root, payload)
    # Capability checks supplement the guarded function shapes for old releases.
    for relative, terms in {
        'tui_gateway/methods_display.py': ['display.status', 'display.start', 'display.observe', 'display.lease.acquire', 'display.lease.release'],
        'web/src/plugins/registry.ts': ['buildWsUrl'],
    }.items():
        text = regular_target(root, relative).read_text(encoding='utf-8')
        if any(term not in text for term in terms): raise ValueError('Hermes display API/SDK is incompatible: ' + relative)
    profile = regular_target(home, 'profiles/bot-screen-lab')
    root_file = regular_target(home, 'config.yaml')
    profile_file = regular_target(home, 'profiles/bot-screen-lab/config.yaml')
    config = helper(root, python, home, 'configuration', rootConfig=(read(root_file) or b'').decode('utf-8-sig'),
                    profileConfig=(read(profile_file) or b'').decode('utf-8-sig'), backend=options.backend, image=options.image)
    dependencies = helper(root, python, home, 'prerequisites', backend=config['backend'], image=config['image'])
    edits = []
    # Dependencies before importers, then profile/config/frontend assets.
    for relative in list(payload['added']) + list(payload['modules']):
        if relative in core:
            before, after = core[relative]
            edits.append({'scope': 'core', 'path': relative, 'before': before, 'after': after})
    def home_edit(relative, after, only_missing=False):
        target = regular_target(home, relative)
        before = read(target)
        if not only_missing or before is None:
            if before != after: edits.append({'scope': 'home', 'path': relative, 'before': before, 'after': after})
    home_edit('config.yaml', config['rootConfig'].encode('utf-8'))
    home_edit('profiles/bot-screen-lab/config.yaml', config['profileConfig'].encode('utf-8'))
    home_edit('profiles/bot-screen-lab/.env', b'# Isolated Bot Screen profile; no credentials copied.\n', True)
    home_edit('profiles/bot-screen-lab/.no-bundled-skills', b'', True)
    home_edit('profiles/bot-screen-lab/profile.yaml', b'name: bot-screen-lab\ndescription: Isolated Bot Screen desktop\n', True)
    for relative in ['manifest.json', 'dist/index.js', 'LICENSE.novnc.txt']:
        home_edit('plugins/bot-screen-lab/dashboard/' + relative, (PACKAGE / 'bot-screen-plugin/dashboard' / relative).read_bytes())
    return edits, dependencies, config

def listening(port):
    try:
        with socket.create_connection(('127.0.0.1', port), timeout=1): return True
    except OSError: return False

def verify_dashboard(port):
    origin = f'http://127.0.0.1:{port}'
    for relative in ['manifest.json', 'dist/index.js']:
        with urlopen(origin + '/dashboard-plugins/bot-screen-lab/' + relative, timeout=5) as response:
            if response.read() != (PACKAGE / 'bot-screen-plugin/dashboard' / relative).read_bytes(): return False
    return True

def activate(root, home, python, options, core_changed):
    port = options.port
    if options.restart == 'never': return {'ready': False, 'reason': 'Dashboard restart/start skipped by --restart never'}
    if listening(port):
        try: owner = helper(root, python, home, 'dashboard-owner', port=port)
        except ValueError as error: return {'ready': False, 'reason': str(error)}
        if core_changed:
            if not owner.get('safe'): return {'ready': False, 'reason': owner.get('reason', 'Restart ownership was not verified')}
            stopped = helper(root, python, home, 'stop-dashboard', port=port, pid=owner['pid'], createTime=owner['createTime'])
            if not stopped['stopped']: return {'ready': False, 'reason': stopped['reason']}
        else:
            if not owner.get('verified'):
                return {'ready': False, 'reason': owner.get('reason', 'Dashboard belongs to an unverified installation')}
            try:
                if verify_dashboard(port): return {'ready': True, 'alreadyRunning': True}
            except OSError: pass
            return {'ready': False, 'reason': 'Reload plugin discovery or restart the existing Dashboard'}
    command = helper(root, python, home, 'launch-command', port=port)['command']
    if options.isolated_dashboard: command.append('--isolated')
    log_dir = regular_target(home, 'runtime/bot-screen-installer')
    log_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    env = dict(os.environ); env['HERMES_HOME'] = str(home); env['PYTHONIOENCODING'] = 'utf-8'
    env.pop('PYTHONPATH', None); env.pop('PYTHONHOME', None)
    flags = {'creationflags': subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS} if os.name == 'nt' else {'start_new_session': True}
    with (log_dir / 'dashboard.log').open('ab') as log:
        process = subprocess.Popen(command, cwd=root, env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=log, **flags)
    for _ in range(60):
        try:
            if verify_dashboard(port): return {'ready': True, 'started': True, 'pid': process.pid}
        except OSError: pass
        if process.poll() is not None: break
        time.sleep(1)
    return {'ready': False, 'reason': 'Dashboard did not become ready; inspect runtime/bot-screen-installer/dashboard.log in the selected Hermes home'}

def verify_bundle():
    manifest = PACKAGE / 'CONTENTS.json'
    if not manifest.exists(): return
    for relative, expected in json.loads(manifest.read_text())['files'].items():
        target = regular_target(PACKAGE, relative)
        if not target.is_file() or sha(target.read_bytes()) != expected: raise ValueError('Package integrity check failed: ' + relative)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--hermes-root', type=Path)
    parser.add_argument('--hermes-home', type=Path)
    parser.add_argument('--python', type=Path)
    parser.add_argument('--launcher')
    parser.add_argument('--backend', choices=['auto', 'docker', 'native'], default='auto')
    parser.add_argument('--image', default='nousresearch/hermes-sandbox:desktop')
    parser.add_argument('--port', type=int, default=9119)
    parser.add_argument('--check-only', action='store_true')
    parser.add_argument('--restart', choices=['auto', 'never'], default='auto')
    parser.add_argument('--no-open', action='store_true')
    parser.add_argument('--skip-smoke', action='store_true', help='Install files only; desktop acceptance remains incomplete')
    parser.add_argument('--rollback', metavar='latest|BACKUP_ID')
    parser.add_argument('--isolated-dashboard', action='store_true', help='Separate listener, for a deliberate isolated installation')
    options = parser.parse_args()
    if not 1024 <= options.port <= 65535: parser.error('--port must be between 1024 and 65535')
    verify_bundle()
    root, python = discover(options)
    home = (options.hermes_home or (Path(os.environ['HERMES_HOME']) if os.environ.get('HERMES_HOME') else Path(helper(root, python, root, 'default-home')['home']))).resolve()
    anchors = {'core': root, 'home': home}
    backup_root = home / 'profiles/bot-screen-lab/plugin-backups/one-click'
    if options.rollback:
        with installation_lock(home): identifier = rollback(anchors, backup_root, options.rollback)
        print(json.dumps({'status': 'restored', 'backup': identifier, 'restartRequired': True}, indent=2)); return 0
    print('Checking Hermes compatibility and desktop prerequisites...', flush=True)
    edits, dependencies, config = prepare(root, home, python, options)
    plan = {'release': RELEASE, 'profile': 'bot-screen-lab', 'backend': config['backend'],
            'filesToChange': [e['scope'] + ':' + e['path'] for e in edits], 'imageWillDownload': dependencies['imageMissing']}
    if options.check_only:
        print(json.dumps({'status': 'compatible', **plan}, indent=2)); return 0
    if dependencies['imageMissing']:
        print('Downloading the Linux desktop image (Hermes and Docker are not reinstalled)...', flush=True)
        subprocess.run([dependencies['docker'], 'pull', config['image']], check=True)
    with installation_lock(home): identifier = commit(anchors, edits, backup_root)
    print('Files installed' + ('; backup ' + identifier if identifier else '; this release was already installed'), flush=True)
    core_changed = any(e['scope'] == 'core' for e in edits)
    activation = activate(root, home, python, options, core_changed)
    smoke_result = {'desktopRunning': False, 'rfbHandshake': False, 'skipped': True}
    if not options.skip_smoke:
        print('Checking the isolated desktop and real RFB handshake...', flush=True)
        try: smoke_result = helper(root, python, home / 'profiles/bot-screen-lab', 'smoke')
        except ValueError as error: smoke_result = {'desktopRunning': False, 'rfbHandshake': False, 'error': str(error)}
    result = {'status': 'ready' if activation['ready'] and smoke_result.get('rfbHandshake') else 'installed-needs-attention',
              **plan, 'backup': identifier, 'dashboard': activation, 'desktop': smoke_result,
              'url': f'http://127.0.0.1:{options.port}/bot-screen', 'restartRequired': not activation['ready']}
    report = home / 'runtime/bot-screen-installer/result.json'
    from engine import atomic_write
    atomic_write(report, json.dumps(result, indent=2).encode())
    print(json.dumps(result, indent=2))
    if result['status'] == 'ready' and not options.no_open: webbrowser.open(result['url'])
    return 0 if result['status'] == 'ready' else 2

if __name__ == '__main__':
    try: raise SystemExit(main())
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        print('INSTALLATION STOPPED: ' + str(error), file=sys.stderr)
        raise SystemExit(1)
