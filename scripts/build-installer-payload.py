"""Build a portable, function-scoped compatibility payload; never ship machine state."""
import ast
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'installer'))
from engine import node_hash
targets = {
    'tools/bot_desktop/runtime.py': ['_flocked', '_start_in_sandbox', '_sandbox_status', '_sandbox_published_env', 'open_rfb_stream', '_launcher_pid', '_spawn_and_wait'],
    'tools/bot_desktop/lease.py': ['_locked'],
    'hermes_cli/web_routers/display.py': ['_open_rfb', '_bridge'],
}

def node(text, name):
    return next(n for n in ast.parse(text).body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.name == name)

def digest(item):
    return node_hash(item)

# Original snapshots are used only while authoring this release. Their paths and
# contents outside the named functions never enter the portable payload.
backups = Path(os.environ['LOCALAPPDATA']) / 'hermes/profiles/bot-screen-lab/backups'
baseline = sorted(backups.glob('cross-platform-*'))[-1]
original_lock = sorted(backups.glob('runtime-lock-*'))[0] / 'runtime.py'
payload = {'schema': 1, 'release': '0.5.0', 'modules': {}, 'added': {}}
for path, names in targets.items():
    current = (ROOT / 'hermes' / path).read_text(encoding='utf-8')
    before = (baseline / path).read_text(encoding='utf-8')
    methods = {}
    for name in names:
        latest = node(current, name)
        accepted = {digest(node(before, name)), digest(latest)}
        if name == '_flocked': accepted.add(digest(node(original_lock.read_text(encoding='utf-8'), name)))
        lines = current.splitlines(keepends=True)
        start = min([latest.lineno] + [d.lineno for d in getattr(latest, 'decorator_list', [])])
        methods[name] = {'accepted': sorted(accepted), 'code': ''.join(lines[start - 1:latest.end_lineno]) + '\n'}
    new_nodes = {}
    if path.endswith('/runtime.py'):
        name = '_linux_process_identity'; latest = node(current, name)
        new_nodes[name] = ''.join(current.splitlines(keepends=True)[latest.lineno - 1:latest.end_lineno]) + '\n'
    payload['modules'][path] = {'nodes': methods, 'newNodes': new_nodes, 'imports': ['os'] if path.endswith('/display.py') else []}
for path in ['tools/bot_desktop/transport.py', 'hermes_cli/web_display_streams.py']:
    payload['added'][path] = (ROOT / 'hermes' / path).read_text(encoding='utf-8')
destination = ROOT / 'installer/runtime-payload.json'
destination.parent.mkdir(exist_ok=True)
destination.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
print('Built portable runtime payload: 10 guarded nodes, Linux identity helper, 2 added modules')
