"""Run a temporary Windows acceptance listener without replacing the daily listener."""
import argparse
import os
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--port', type=int, default=9125)
args = parser.parse_args()
assert os.name == 'nt'
assert os.environ.get('HERMES_HOME')
assert args.port == 9125, 'Acceptance listener is pinned to 9125'
os.chdir(Path(__file__).resolve().parent.parent / 'hermes')
from hermes_cli.plugins import discover_plugins
discover_plugins()
from hermes_cli.web_server import start_server
start_server(host='127.0.0.1', port=args.port, open_browser=False, isolated=True)
