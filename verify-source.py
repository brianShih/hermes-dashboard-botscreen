"""Verify retained source against the portable manifest; no original machine path needed."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', type=Path, help='Optional upstream Git checkout for an independent baseline')
args = parser.parse_args()
manifest = json.loads((ROOT / 'source-manifest.json').read_text(encoding='utf-8'))
changes = json.loads((ROOT / 'integration-changes.json').read_text(encoding='utf-8'))
approved = {item['path']: item for item in changes.get('modifiedUpstreamFiles', [])}
omissions = manifest.get('privacyOmissions', {})

def omitted(name):
    return name in omissions.get('files', []) or any(name.startswith(p) for p in omissions.get('prefixes', []))

if args.source:
    tree = subprocess.check_output(['git', '-C', str(args.source), 'ls-tree', '-rz', manifest['commit']])
    entries = []
    for record in tree.split(b'\0'):
        if not record:
            continue
        metadata, raw_path = record.split(b'\t', 1)
        mode, kind, oid = metadata.decode().split()
        name = raw_path.decode('utf-8')
        if not omitted(name):
            entries.append({'path': name, 'mode': mode, 'gitBlob': oid})
else:
    entries = manifest['entries']

def check(entry):
    name = entry['path']
    target = ROOT / 'hermes' / name
    if not target.is_file():
        return {'path': name, 'reason': 'missing entry'}
    data = target.read_bytes()
    if name in approved:
        change = approved[name]
        exact = hashlib.sha256(data).hexdigest() == change['sha256']
        normalized = hashlib.sha256(data.replace(b'\r\n', b'\n')).hexdigest() == change.get('normalizedSha256')
        if entry['gitBlob'] == change['originalGitBlob'] and (exact or normalized):
            return None
        return {'path': name, 'reason': 'reviewed local file changed'}
    blob = lambda raw: hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
    if blob(data) == entry['gitBlob']:
        return None
    # Git may apply platform line endings to source/text extensions that the
    # upstream attributes do not enumerate. Accept only an exact LF-equivalent
    # blob for valid UTF-8 text; do not normalize binary assets.
    if b'\0' not in data:
        try:
            data.decode('utf-8')
            if blob(data.replace(b'\r\n', b'\n')) == entry['gitBlob']:
                return None
        except UnicodeDecodeError:
            pass
    return {'path': name, 'reason': 'blob mismatch'}

with ThreadPoolExecutor(max_workers=16) as pool:
    errors = [error for error in pool.map(check, entries) if error]
added = changes.get('addedUpstreamFiles', [])
for entry in added:
    target = ROOT / 'hermes' / entry['path']
    data = target.read_bytes() if target.is_file() else b''
    if not target.is_file() or (hashlib.sha256(data).hexdigest() != entry['sha256'] and hashlib.sha256(data.replace(b'\r\n', b'\n')).hexdigest() != entry.get('normalizedSha256')):
        errors.append({'path': entry['path'], 'reason': 'reviewed added file changed or missing'})
result = {'commit': manifest['commit'], 'filesChecked': len(entries), 'passed': not errors,
          'errors': errors, 'approvedLocalChanges': len(approved), 'privacyOmissions': omissions,
          'verificationScope': 'retained source integrity; runtime evidence is separate',
          'baseline': 'upstream Git checkout' if args.source else 'bundled sanitized manifest'}
result['addedFilesChecked'] = len(added)
(ROOT / 'source-verification-current.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
raise SystemExit(0 if not errors else 1)
