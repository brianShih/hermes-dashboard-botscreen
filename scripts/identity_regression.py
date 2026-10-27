"""Run inside task-owned Linux with real runtime import; never production."""
import json, os, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from tools.bot_desktop import runtime as r

class IdentityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir='/lab')
        self.sd = Path(self.tmp.name)
        self.scope = patch.object(r, 'state_dir', return_value=self.sd)
        self.scope.start()
        self.pid = os.getpid()
    def tearDown(self):
        self.scope.stop()
        self.tmp.cleanup()
    def record(self, identity):
        (self.sd/'launcher.pid').write_text(f'{self.pid} {identity}')
    def identity(self):
        # Expected stable identity comes directly from kernel, not epoch time.
        ticks = Path(f'/proc/{self.pid}/stat').read_text().rsplit(')', 1)[1].split()[19]
        boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
        ns = Path(f'/proc/{self.pid}/ns/pid').stat().st_ino
        return f'linux-v1:{boot}:{ns}:{ticks}'
    def test_clock_drift_preserves_same_process(self):
        self.record(self.identity())
        for drift in (0, 3, 6, 44, -6):
            with patch.object(r, '_create_time', return_value=123456+drift):
                self.assertEqual(r._launcher_pid(), self.pid)
    def test_reused_pid_rejected(self):
        token = self.identity().split(':'); token[-1] = str(int(token[-1])+1)
        self.record(':'.join(token)); self.assertIsNone(r._launcher_pid())
    def test_previous_boot_rejected(self):
        token = self.identity().split(':'); token[1] = '00000000-0000-0000-0000-000000000000'
        self.record(':'.join(token)); self.assertIsNone(r._launcher_pid())
    def test_other_namespace_rejected(self):
        token = self.identity().split(':'); token[2] = str(int(token[2])+1)
        self.record(':'.join(token)); self.assertIsNone(r._launcher_pid())
    def test_dead_or_zombie_rejected(self):
        self.record(self.identity())
        with patch.object(r, '_pid_alive', return_value=False): self.assertIsNone(r._launcher_pid())
    def test_malformed_fail_closed(self):
        for token in ('', 'linux-v1:', 'nan', 'inf', '0', 'linux-v2:unknown'):
            self.record(token); self.assertIsNone(r._launcher_pid())
    def test_unreadable_identity_fails_closed(self):
        token=self.identity(); self.record(token)
        original=Path.read_text
        def read(path, *args, **kwargs):
            if str(path).startswith('/proc/'):
                raise PermissionError('procfs unavailable')
            return original(path,*args,**kwargs)
        with patch.object(Path,'read_text',read): self.assertIsNone(r._launcher_pid())
    def test_proc_stat_comm_with_parentheses(self):
        expected=self.identity()
        original=Path.read_text
        def read(path,*args,**kwargs):
            text=original(path,*args,**kwargs)
            if str(path)==f'/proc/{self.pid}/stat':
                text=f'{self.pid} (name with ) parentheses)'+text.rsplit(')',1)[1]
            return text
        with patch.object(Path,'read_text',read): self.assertEqual(r._linux_process_identity(self.pid),expected)
    def test_legacy_guard_not_relaxed(self):
        self.record('100.0')
        with patch.object(r, '_create_time', return_value=103.0): self.assertIsNone(r._launcher_pid())
        with patch.object(r, '_create_time', return_value=100.0): self.assertEqual(r._launcher_pid(),self.pid)

if __name__ == '__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(IdentityTests))
    Path('/lab/identity-result.json').write_text(json.dumps({'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'passed':result.wasSuccessful()}))
    raise SystemExit(not result.wasSuccessful())
