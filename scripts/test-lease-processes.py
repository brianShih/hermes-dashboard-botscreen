"""Real concurrent lease transitions must never lose epochs or tear the state file."""
from pathlib import Path
import os
import subprocess
import sys
import tempfile

root = Path(sys.argv[1]).resolve()
with tempfile.TemporaryDirectory() as temporary:
    env = {**os.environ, 'PYTHONPATH': str(root), 'HERMES_HOME': temporary}
    code = '''
import sys
from tools.bot_desktop import lease
for i in range(25): lease.acquire(sys.argv[1] + str(i))
'''
    processes = [subprocess.Popen([sys.executable, '-c', code, str(index) + '-'], env=env,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for index in range(4)]
    for process in processes:
        out, err = process.communicate(timeout=30)
        assert process.returncode == 0, err
    import json
    state = json.loads((Path(temporary) / 'bot-desktop/lease.json').read_text())
    assert state['epoch'] == 100, state['epoch']
    assert state['holder'] == 'human'
print('PASS: 100 concurrent lease transitions, exact epoch count, intact state')
