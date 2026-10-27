"""Exercise the real runtime lock across processes without touching a user profile."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

root = Path(sys.argv[1]).resolve()
with tempfile.TemporaryDirectory() as temporary:
    work = Path(temporary)
    env = {**os.environ, 'PYTHONPATH': str(root), 'HERMES_HOME': str(work / 'profile')}
    child = '''
from pathlib import Path
import sys
from tools.bot_desktop.runtime import _flocked
with _flocked(Path(sys.argv[1])):
    print('acquired', flush=True)
'''
    sys.path.insert(0, str(root))
    from tools.bot_desktop.runtime import _flocked
    lock = work / 'start.lock'
    with _flocked(lock):
        process = subprocess.Popen([sys.executable, '-c', child, str(lock)], env=env,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        time.sleep(0.5)
        assert process.poll() is None, 'A competing process bypassed the held lock or crashed'
    out, err = process.communicate(timeout=10)
    assert process.returncode == 0, err
    assert out.strip() == 'acquired'
    try:
        with _flocked(lock):
            raise RuntimeError('test release after exception')
    except RuntimeError:
        pass
    result = subprocess.run([sys.executable, '-c', child, str(lock)], env=env,
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == 'acquired'
print('PASS: real cross-process exclusion, wait, release and exception cleanup')
