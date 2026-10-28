import importlib.util
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'installer'))
import engine
spec = importlib.util.spec_from_file_location('skill_installer', ROOT / 'scripts/install-dashboard.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)

class SkillInstallTests(unittest.TestCase):
    def test_install_repeat_local_edit_guard_and_rollback(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'core'; home = Path(directory) / 'home'
            root.mkdir(); home.mkdir()
            for name, text in [('tui_gateway/methods_display.py', 'display.status display.start display.observe display.lease.acquire display.lease.release'), ('web/src/plugins/registry.ts', 'buildWsUrl')]:
                p = root / name; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text)
            config = {'rootConfig': '{}\n', 'profileConfig': '{}\n', 'backend': 'docker', 'image': 'test'}
            with patch.object(installer, 'runtime_plan', return_value={}), patch.object(installer, 'helper', side_effect=lambda *a, **kw: config if a[3] == 'configuration' else {'imageMissing': False}):
                args = SimpleNamespace(backend='auto', image='test')
                edits, _, _ = installer.prepare(root, home, Path(sys.executable), args)
                skills = [e for e in edits if '/skills/' in e['path']]
                self.assertEqual(len(skills), 5)
                self.assertFalse((home / skills[0]['path']).exists(), 'Planning must not write')
                backup = home / 'backups'
                identifier = engine.commit({'core': root, 'home': home}, edits, backup)
                repeat, _, _ = installer.prepare(root, home, Path(sys.executable), args)
                self.assertEqual(repeat, [])
                target = home / skills[0]['path']; installed = target.read_bytes()
                target.write_bytes(b'private local edit')
                with self.assertRaisesRegex(ValueError, 'Locally modified'):
                    installer.prepare(root, home, Path(sys.executable), args)
                target.write_bytes(installed)
                engine.rollback({'core': root, 'home': home}, backup, identifier)
                self.assertFalse(target.exists())

if __name__ == '__main__':
    unittest.main()
