"""Provision only the disposable integration container, never a host Hermes home."""
import json
import os
from pathlib import Path
import secrets

assert Path('/integration/bootstrap.py').is_file() and Path('/plugin/dashboard/manifest.json').is_file()
assert os.environ.get('HERMES_HOME') == '/lab/profiles/bot-screen-lab'
import hermes_yaml as yaml
from plugins.dashboard_auth.basic import hash_password

root = Path('/lab')
home = root / 'profiles' / 'bot-screen-lab'
home.mkdir(parents=True, exist_ok=True)
credential = root / 'test-login.json'
if not credential.exists():
    password = secrets.token_urlsafe(32)
    config = {
        'terminal': {'backend': 'local'},
        'bot_desktop': {'placement': 'gateway'},
        'plugins': {'enabled': ['bot-screen-lab']},
        'dashboard': {'basic_auth': {
            'username': 'integration', 'password_hash': hash_password(password),
            'secret': secrets.token_urlsafe(32),
        }},
    }
    (home / 'config.yaml').write_text(yaml.safe_dump(config))
    credential.write_text(json.dumps({'username': 'integration', 'password': password}))
    credential.chmod(0o600)
plugins = home / 'plugins'
plugins.mkdir(exist_ok=True)
link = plugins / 'bot-screen-lab'
if not link.exists():
    link.symlink_to('/plugin', target_is_directory=True)
Path('/tmp/hermes-runtime').mkdir(mode=0o700, exist_ok=True)
print('Isolated profile provisioned; credentials stay inside the container.')
from hermes_state import SessionDB
db = SessionDB()
db.close()
