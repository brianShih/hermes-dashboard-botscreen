"""Start one task-owned input fixture on the isolated profile's real desktop."""
import os
from pathlib import Path
import subprocess
import time
import psutil

os.environ['HERMES_HOME'] = '/lab/profiles/bot-screen-lab'
from tools.bot_desktop.runtime import desktop_env

for process in psutil.process_iter(['cmdline']):
    if process.info['cmdline'] == ['wish', '/integration/input-fixture.tcl']:
        process.terminate()
        for attempt in range(100):
            if not process.is_running() or process.status() == psutil.STATUS_ZOMBIE:
                break
            time.sleep(0.05)
        else:
            raise RuntimeError('Previous fixture did not stop')
Path('/lab/input-proof.txt').write_text('')
with Path('/lab/input-fixture.log').open('a') as log:
    subprocess.Popen(['wish', '/integration/input-fixture.tcl'],
                     env={**os.environ, **desktop_env()}, stdin=subprocess.DEVNULL,
                     stdout=log, stderr=log, start_new_session=True)
