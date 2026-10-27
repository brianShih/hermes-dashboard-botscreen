"""Standard-library-only guarded edits, atomic writes and reversible snapshots."""
from __future__ import annotations
import ast
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile

RELEASE = '0.5.0'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def node_hash(node):
    # Ignore empty fields added by newer Python AST versions (for example
    # FunctionDef.type_params), while retaining actual syntax and constants.
    def canonical(value):
        if isinstance(value, ast.AST):
            return {'type': type(value).__name__, **{key: canonical(item) for key, item in ast.iter_fields(value) if item is not None and item != []}}
        if isinstance(value, list): return [canonical(item) for item in value]
        return [type(value).__name__, repr(value)]
    return sha(json.dumps(canonical(node), sort_keys=True, ensure_ascii=True).encode())

def regular_target(anchor, relative):
    anchor = Path(anchor).resolve()
    part = Path(relative)
    if part.is_absolute() or '..' in part.parts:
        raise ValueError('Unsafe relative installation path')
    target = anchor / part
    cursor = target
    while cursor != anchor:
        if cursor.is_symlink() or getattr(cursor, 'is_junction', lambda: False)():
            raise ValueError('Symlink/junction installation targets are refused: ' + relative)
        cursor = cursor.parent
    if not target.resolve().is_relative_to(anchor):
        raise ValueError('Installation path escaped its selected root')
    return target

def runtime_plan(root, payload):
    changes = {}
    for relative, spec in payload['modules'].items():
        target = regular_target(root, relative)
        before = target.read_bytes()
        text = before.decode('utf-8-sig')
        tree = ast.parse(text)
        replacements = []
        for name, definition in spec['nodes'].items():
            matches = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.name == name]
            if len(matches) != 1 or node_hash(matches[0]) not in definition['accepted']:
                raise ValueError(f'Incompatible Hermes code: {relative}:{name}. Nothing was overwritten.')
            current = matches[0]
            wanted = ast.parse(definition['code']).body[0]
            if node_hash(current) != node_hash(wanted):
                start = min([current.lineno] + [d.lineno for d in getattr(current, 'decorator_list', [])])
                replacements.append((start - 1, current.end_lineno, definition['code']))
        lines = text.splitlines(keepends=True)
        for start, end, code in sorted(replacements, reverse=True):
            lines[start:end] = [code]
        updated = ''.join(lines)
        added_node = False
        for name, code in spec.get('newNodes', {}).items():
            existing = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name]
            if existing and (len(existing) != 1 or node_hash(existing[0]) != node_hash(ast.parse(code).body[0])):
                raise ValueError('Existing helper differs from this release: ' + relative + ':' + name)
            if not existing:
                updated += '\n\n' + code
                added_node = True
        imports = {alias.name for n in tree.body if isinstance(n, ast.Import) for alias in n.names}
        missing = [name for name in spec['imports'] if name not in imports]
        if missing:
            # Keep the module docstring and __future__ imports at the beginning.
            parsed = ast.parse(updated)
            start = 0
            for n in parsed.body:
                if isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str):
                    start = n.end_lineno
                elif isinstance(n, ast.ImportFrom) and n.module == '__future__':
                    start = n.end_lineno
                else:
                    break
            rows = updated.splitlines(keepends=True)
            rows[start:start] = ['\n' + '\n'.join('import ' + name for name in missing) + '\n']
            updated = ''.join(rows)
        ast.parse(updated)
        if replacements or missing or added_node:
            changes[relative] = (before, updated.encode('utf-8'))
    for relative, code in payload['added'].items():
        target = regular_target(root, relative)
        expected = code.encode('utf-8')
        before = target.read_bytes() if target.exists() else None
        if before is not None and before.replace(b'\r\n', b'\n') != expected.replace(b'\r\n', b'\n'):
            raise ValueError('Existing adapter differs from this release: ' + relative)
        if before is None:
            ast.parse(code)
            changes[relative] = (None, expected)
    return changes

def atomic_write(path, data, mode=0o600):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix='.bot-screen-', dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)

@contextmanager
def installation_lock(home):
    path = home / '.bot-screen-installer.lock'
    home.mkdir(parents=True, exist_ok=True)
    with path.open('a+b') as stream:
        stream.seek(0, 2)
        if stream.tell() == 0:
            stream.write(b'\n'); stream.flush()
        stream.seek(0)
        if os.name == 'nt':
            import msvcrt
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == 'nt':
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)

def commit(anchors, edits, backup_root):
    """Each edit has scope/path/before/after; validate the whole plan before writing."""
    edits = [e for e in edits if e['before'] != e['after']]
    if not edits:
        return None
    for edit in edits:
        path = regular_target(anchors[edit['scope']], edit['path'])
        actual = path.read_bytes() if path.exists() else None
        if actual != edit['before']:
            raise ValueError('A target changed after preflight; rerun the installer')
    identifier = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    backup = backup_root / identifier
    backup.mkdir(parents=True, mode=0o700)
    os.chmod(backup, 0o700)
    record = {'schema': 1, 'release': RELEASE, 'anchors': {k: str(v.resolve()) for k, v in anchors.items()},
              'status': 'prepared', 'files': []}
    for index, edit in enumerate(edits):
        path = regular_target(anchors[edit['scope']], edit['path'])
        before = edit['before']
        row = {'scope': edit['scope'], 'path': edit['path'], 'beforeSha': sha(before) if before is not None else None,
               'afterSha': sha(edit['after']), 'backup': str(index),
               'mode': path.stat().st_mode & 0o777 if path.exists() else (0o644 if edit['scope'] == 'core' else 0o600)}
        if before is not None:
            atomic_write(backup / str(index), before)
        record['files'].append(row)
    atomic_write(backup / 'receipt.json', json.dumps(record, indent=2).encode())
    written = []
    try:
        # Added support modules must exist before a running service can import
        # patched functions; the plan places them first.
        for edit, row in zip(edits, record['files']):
            path = regular_target(anchors[edit['scope']], edit['path'])
            atomic_write(path, edit['after'], row['mode'])
            written.append((edit, row))
        record['status'] = 'installed'
        atomic_write(backup / 'receipt.json', json.dumps(record, indent=2).encode())
    except BaseException:
        for edit, row in reversed(written):
            path = regular_target(anchors[edit['scope']], edit['path'])
            if edit['before'] is None:
                path.unlink()
            else:
                atomic_write(path, edit['before'], row['mode'])
        record['status'] = 'rolled-back-on-error'
        atomic_write(backup / 'receipt.json', json.dumps(record, indent=2).encode())
        raise
    return identifier

def rollback(anchors, backup_root, identifier):
    candidates = sorted(p for p in backup_root.glob('*/receipt.json') if p.is_file())
    if identifier == 'latest':
        candidates = [p for p in candidates if json.loads(p.read_text())['status'] == 'installed']
        if not candidates: raise ValueError('No installed snapshot to restore')
        receipt = candidates[-1]
    else:
        if not identifier or any(c not in '0123456789TZ' for c in identifier):
            raise ValueError('Invalid backup identifier')
        receipt = backup_root / identifier / 'receipt.json'
    record = json.loads(receipt.read_text())
    if record['anchors'] != {k: str(v.resolve()) for k, v in anchors.items()} or record['status'] != 'installed':
        raise ValueError('Snapshot belongs to another installation or was already restored')
    targets = []
    for row in record['files']:
        path = regular_target(anchors[row['scope']], row['path'])
        if not path.is_file() or sha(path.read_bytes()) != row['afterSha']:
            raise ValueError('Refusing to overwrite files edited after installation: ' + row['path'])
        data = None
        if row['beforeSha'] is not None:
            if not str(row['backup']).isdigit(): raise ValueError('Invalid backup entry')
            data = (receipt.parent / row['backup']).read_bytes()
            if sha(data) != row['beforeSha']: raise ValueError('Backup integrity check failed')
        targets.append((path, data, row['mode'], path.read_bytes()))
    restored = []
    try:
        for path, data, mode, current in reversed(targets):
            if data is None: path.unlink()
            else: atomic_write(path, data, mode)
            restored.append((path, current, mode))
    except BaseException:
        for path, current, mode in reversed(restored): atomic_write(path, current, mode)
        raise
    record['status'] = 'restored'
    atomic_write(receipt, json.dumps(record, indent=2).encode())
    return receipt.parent.name
