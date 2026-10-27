"""Dedicated Dashboard. Docker binds its published port to host loopback only."""
import os
from pathlib import Path
assert os.environ.get('HERMES_HOME') == '/lab/profiles/bot-screen-lab'
os.chdir('/opt/hermes')
with Path('/lab/dashboard.log').open('a') as log:
    os.dup2(log.fileno(), 1)
    os.dup2(log.fileno(), 2)
    from hermes_cli.plugins import discover_plugins
    discover_plugins()
    from hermes_cli.web_server import start_server
    start_server(host='0.0.0.0', port=9124, open_browser=False, isolated=True)
