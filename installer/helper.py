"""Runs only inside the selected Hermes Python; never prints tokens or config values."""
from __future__ import annotations
from contextlib import redirect_stdout
from io import StringIO
import json
import os
from pathlib import Path
import subprocess
import sys

def configuration(request):
    from ruamel.yaml import YAML
    from ruamel.yaml.error import YAMLError
    yaml = YAML()
    yaml.preserve_quotes = True
    def load(text):
        try: value = yaml.load(text) if text else {}
        except YAMLError: raise ValueError('Invalid YAML configuration; no files were changed') from None
        if value is None: value = {}
        if not isinstance(value, dict): raise ValueError('Configuration must be a YAML mapping')
        return value
    def section(data, key):
        if key not in data: data[key] = {}
        if not isinstance(data[key], dict): raise ValueError('Expected configuration mapping: ' + key)
        return data[key]
    root = load(request['rootConfig'])
    profile = load(request['profileConfig'])
    plugins = section(root, 'plugins')
    for key in ['enabled', 'disabled']:
        if key not in plugins or plugins[key] is None: plugins[key] = []
        if not isinstance(plugins[key], list): raise ValueError('plugins.' + key + ' must be a list')
    if 'bot-screen-lab' not in plugins['enabled']: plugins['enabled'].append('bot-screen-lab')
    plugins['disabled'][:] = [v for v in plugins['disabled'] if v != 'bot-screen-lab']
    hidden = root.get('dashboard', {}).get('hidden_plugins', [])
    if 'bot-screen-lab' in hidden: hidden.remove('bot-screen-lab')
    terminal = section(profile, 'terminal')
    current = terminal.get('backend')
    requested = request['backend']
    if requested == 'auto':
        if current not in (None, 'docker', 'local'):
            raise ValueError('Existing isolated profile uses an unsupported backend; choose another profile installation')
        requested = 'native' if current == 'local' and sys.platform == 'linux' else 'docker'
        if current == 'local' and sys.platform != 'linux':
            raise ValueError('Existing local profile cannot host a Windows desktop. Rerun with --backend docker to configure this isolated profile')
    if requested == 'native' and sys.platform != 'linux': raise ValueError('Native desktop requires Linux')
    terminal['backend'] = 'local' if requested == 'native' else 'docker'
    desktop = section(profile, 'bot_desktop')
    desktop['placement'] = 'gateway' if requested == 'native' else 'terminal'
    if requested == 'docker':
        terminal.setdefault('docker_image', request['image'])
        terminal.setdefault('container_persistent', True)
    out = {}
    for name, value, original in [('rootConfig', root, request['rootConfig']), ('profileConfig', profile, request['profileConfig'])]:
        stream = StringIO(); yaml.dump(value, stream)
        # Preserve byte-for-byte formatting when the semantic configuration did not change.
        out[name] = original if load(original) == value and original else stream.getvalue()
    out['backend'] = requested
    out['image'] = terminal.get('docker_image', request['image'])
    if not isinstance(out['image'], str) or not out['image'] or out['image'].startswith('-') or '://' in out['image'] or '\n' in out['image']:
        raise ValueError('terminal.docker_image must be a valid image reference')
    return out

def prerequisites(request):
    if request['backend'] == 'native':
        from tools.bot_desktop import runtime
        missing = runtime.missing_binaries()
        if missing: raise ValueError('Native Linux desktop packages missing: ' + ', '.join(missing) + '. Use Docker or install the required packages first')
        return {'backend': 'native', 'imageMissing': False}
    from tools.environments.docker import find_docker
    docker = find_docker()
    if not docker: raise ValueError('Docker is required. Install Docker Desktop on Windows or Docker Engine on Linux, then rerun')
    result = subprocess.run([docker, 'version', '--format', '{{.Server.Os}}'], capture_output=True, text=True, timeout=20)
    if result.returncode or result.stdout.strip() != 'linux':
        raise ValueError('Docker must be running in Linux-container mode. Start Docker and rerun')
    result = subprocess.run([docker, 'image', 'inspect', request['image']], capture_output=True, timeout=20)
    return {'backend': 'docker', 'docker': docker, 'imageMissing': result.returncode != 0}

def default_home(_request):
    from hermes_constants import get_default_hermes_root
    # The helper's explicit temporary HERMES_HOME must not turn /opt/hermes-agent
    # into the default user-data directory on POSIX installations.
    return {'home': str(get_default_hermes_root(home=''))}

def child_environment(request):
    from tools.environments.local import served_profile_child_env
    target = Path(request['target'])
    if target.name != 'bot-screen-lab' or target.parent.name != 'profiles':
        raise ValueError('Desktop validation must use the isolated Bot Screen profile')
    return {'environment': served_profile_child_env(target_home=target, inherit_credentials=False)}

def smoke(_request):
    from hermes_cli.config import load_config
    load_config()
    from tools.bot_desktop import runtime
    status = runtime.start()
    if not status.running: raise ValueError('Desktop did not start')
    import concurrent.futures
    import socket
    if status.placement.startswith('terminal:'):
        relay = runtime.open_rfb_stream()
        pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        try:
            version = pool.submit(relay.stdout.read, 12).result(timeout=15)
            if version != b'RFB 003.008\n': raise ValueError('Unexpected RFB handshake')
            relay.stdin.write(version); relay.stdin.flush()
            security = pool.submit(relay.stdout.read, 2).result(timeout=15)
            if security != b'\x01\x01': raise ValueError('Unexpected isolated RFB security negotiation')
        finally:
            if relay.poll() is None: relay.kill()
            relay.wait(timeout=10)
            relay.stdout.close(); relay.stdin.close(); pool.shutdown(wait=True)
    else:
        with socket.socket(socket.AF_UNIX) as connection:
            connection.settimeout(15); connection.connect(str(runtime.rfb_socket_path()))
            version = connection.recv(12)
            if version != b'RFB 003.008\n': raise ValueError('Unexpected RFB handshake')
            connection.sendall(version)
            if connection.recv(2) != b'\x01\x01': raise ValueError('Unexpected RFB security negotiation')
    return {'desktopRunning': True, 'rfbHandshake': True, 'profile': 'bot-screen-lab'}

def dashboard_owner(request):
    """Prove a quiet, manually launched Dashboard before offering an automatic restart."""
    import psutil
    from gateway import host_rendezvous as rendezvous
    from hermes_cli.process_identity import _pid_alive_matches, install_id
    from hermes_cli.update_cmd_windows import _hermes_holder_subcommand
    from urllib.request import Request, urlopen
    home = Path(os.environ['HERMES_HOME']).resolve()
    record = rendezvous.read_record(rendezvous.ROLE_SERVE)
    def isolated_owner():
        ledger_file = home / 'spawn-ledger.json'
        if not ledger_file.exists(): return None
        for entry in reversed(json.loads(ledger_file.read_text(encoding='utf-8'))):
            if (entry.get('purpose') != 'dashboard' or not entry.get('isolated') or entry.get('port') != request['port']
                    or entry.get('install') != install_id(Path(request['root']))
                    or Path(entry.get('hermes_home', '')).resolve() != home
                    or _pid_alive_matches(entry['pid'], entry.get('create_time'), strict=True) is not True):
                continue
            process = psutil.Process(entry['pid'])
            if _hermes_holder_subcommand(subprocess.list2cmdline(process.cmdline())) != 'dashboard': continue
            if any(c.status == psutil.CONN_LISTEN and c.laddr.port == request['port']
                   and c.laddr.ip in ('127.0.0.1', '::1') for c in process.net_connections(kind='tcp')):
                return {'safe': False, 'verified': True, 'pid': entry['pid'], 'createTime': entry['create_time'],
                        'reason': 'Verified isolated Dashboard; use its owning process to restart it'}
        return None
    if record is None or record.port != request['port'] or Path(record.home).resolve() != home:
        return isolated_owner() or {'safe': False, 'reason': 'No verified manual Dashboard owner for this home and port'}
    if record.host not in ('127.0.0.1', 'localhost', '::1') or rendezvous.probe_owner(record) is None:
        return {'safe': False, 'reason': 'Dashboard ownership or loopback binding could not be verified'}
    ledger = json.loads((home / 'spawn-ledger.json').read_text(encoding='utf-8'))
    matches = [entry for entry in ledger if entry.get('pid') == record.pid and entry.get('purpose') == 'dashboard'
               and entry.get('install') == install_id(Path(request['root'])) and not entry.get('isolated')
               and entry.get('spawner_pid') is None]
    if not matches or _pid_alive_matches(record.pid, record.create_time, strict=True) is not True:
        return {'safe': False, 'reason': 'Dashboard process identity does not match this installation'}
    process = psutil.Process(record.pid)
    if _hermes_holder_subcommand(subprocess.list2cmdline(process.cmdline())) != 'dashboard':
        return {'safe': False, 'reason': 'The listener is not a manual Dashboard command'}
    token = rendezvous.read_token(record.role)
    req = Request(f'http://127.0.0.1:{record.port}/api/status', headers={'X-Hermes-Token': token, 'Authorization': 'Bearer ' + token})
    with urlopen(req, timeout=5) as response: status = json.load(response)
    if status.get('active_sessions') != 0:
        return {'safe': False, 'verified': True, 'reason': 'Active sessions or unknown activity; restart deferred'}
    lease_file = home / 'profiles/bot-screen-lab/bot-desktop/lease.json'
    if lease_file.exists() and json.loads(lease_file.read_text()).get('holder') == 'human':
        return {'safe': False, 'verified': True, 'reason': 'Human desktop control is active; restart deferred'}
    return {'safe': True, 'verified': True, 'pid': record.pid, 'createTime': record.create_time}

def stop_dashboard(request):
    import psutil
    current = dashboard_owner(request)
    if not current.get('safe') or current['pid'] != request['pid'] or current['createTime'] != request['createTime']:
        return {'stopped': False, 'reason': 'Dashboard state changed; restart deferred'}
    process = psutil.Process(current['pid'])
    try:
        process.terminate(); process.wait(timeout=20)
        return {'stopped': True}
    except psutil.AccessDenied:
        return {'stopped': False, 'reason': 'OS permission denied. Restart the Dashboard backend from its owning user or administrator terminal'}
    except psutil.TimeoutExpired:
        return {'stopped': False, 'reason': 'Dashboard did not exit gracefully. No forced kill was attempted'}

def launch_command(request):
    from hermes_cli._launchers import runtime_command
    return {'command': runtime_command(Path(request['root']), ['dashboard', '--host', '127.0.0.1', '--port', str(request['port']), '--no-open'])}

def main():
    request = json.load(sys.stdin)
    actions = {'configuration': configuration, 'prerequisites': prerequisites, 'default-home': default_home, 'child-environment': child_environment,
               'smoke': smoke, 'dashboard-owner': dashboard_owner, 'stop-dashboard': stop_dashboard, 'launch-command': launch_command}
    try:
        with redirect_stdout(sys.stderr): result = actions[request['action']](request)
        print('BOT_SCREEN_RESULT=' + json.dumps({'ok': True, 'result': result}))
    except Exception as error:
        # YAML input, auth tokens and provider state must never enter install logs.
        if isinstance(error, ModuleNotFoundError): message = 'Hermes runtime dependency/module missing: ' + str(error.name) + '. Repair the existing Hermes runtime with hermes pm repair, then rerun'
        else: message = str(error) if isinstance(error, ValueError) else type(error).__name__ + ': operation failed; see ONE_CLICK.md'
        print('BOT_SCREEN_RESULT=' + json.dumps({'ok': False, 'error': message}))
        raise SystemExit(1)

if __name__ == '__main__': main()
