"""Read-only, bounded Linux capability probe; never reads credentials or environment dumps."""
import json
import platform
import shutil
import sys
from pathlib import Path

def probe():
    if sys.platform != 'linux':
        raise SystemExit('Run through the confirmed Linux desktop terminal, not the Dashboard host')
    release = {}
    path = Path('/etc/os-release')
    if path.is_file():
        for line in path.read_text(encoding='utf-8').splitlines():
            key, _, value = line.partition('=')
            if key in {'ID', 'VERSION_ID'}:
                release[key] = value.strip('"')
    return {'platform': 'linux', 'architecture': platform.machine(), 'distribution': release,
            'tools': {name: shutil.which(name) is not None for name in
                      ['python3', 'xfce4-session', 'Xvnc', 'chromium', 'chromium-browser',
                       'firefox', 'apt-get', 'dnf']},
            'routingConfirmedByProbe': False, 'sharedMountConfirmedByProbe': False}

if __name__ == '__main__':
    print(json.dumps(probe(), indent=2))
