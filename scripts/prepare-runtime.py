"""Build a reusable local dependency image without copying lab state or credentials."""
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parent.parent
cache = root / '.runtime'
cache.mkdir(exist_ok=True)
with (cache / 'dependencies.tar').open('wb') as archive:
    subprocess.run(['docker', 'exec', 'hermes-bot-screen-lab', 'tar', 'cf', '-',
                    '/opt/hermes-venv', '/root/.local/share/uv/python'],
                   stdout=archive, stderr=subprocess.DEVNULL, check=True)
subprocess.run(['docker', 'build', '-t', 'bot-screen-integration-runtime:local',
                '-f', str(root / 'scripts' / 'Dockerfile.runtime'), str(cache)], check=True)
