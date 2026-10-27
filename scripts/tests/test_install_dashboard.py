import ast
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'installer'))
import engine

class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.payload = json.loads((ROOT / 'installer/runtime-payload.json').read_text(encoding='utf-8'))
        # This fixture is the current compatible source, with unrelated code
        # deliberately retained. Tests never write to the installed Hermes.
        for relative in list(self.payload['modules']) + list(self.payload['added']):
            path = self.root / relative; path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((ROOT / 'hermes' / relative).read_bytes())

    def tearDown(self): self.temp.cleanup()

    def test_current_runtime_is_a_noop_and_decorators_remain(self):
        self.assertEqual(engine.runtime_plan(self.root, self.payload), {})
        path = self.root / 'tools/bot_desktop/runtime.py'
        self.assertIn('@contextlib.contextmanager\ndef _flocked', path.read_text(encoding='utf-8'))

    def test_unrelated_code_is_preserved_when_support_modules_are_added(self):
        path = self.root / 'tools/bot_desktop/runtime.py'
        path.write_text(path.read_text(encoding='utf-8') + '\nUSER_EXTENSION = "preserve-me"\n', encoding='utf-8')
        (self.root / 'tools/bot_desktop/transport.py').unlink()
        plan = engine.runtime_plan(self.root, self.payload)
        self.assertNotIn('tools/bot_desktop/runtime.py', plan)
        self.assertIn('tools/bot_desktop/transport.py', plan)

    def test_unknown_function_refuses_the_whole_plan(self):
        path = self.root / 'tools/bot_desktop/runtime.py'
        text = path.read_text(encoding='utf-8').replace('def _flocked(path: Path):', 'def _flocked(path: Path, unknown=False):')
        path.write_text(text, encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Incompatible'): engine.runtime_plan(self.root, self.payload)
        self.assertEqual(path.read_text(encoding='utf-8'), text)

    def test_unknown_existing_adapter_is_not_overwritten(self):
        path = self.root / 'tools/bot_desktop/transport.py'; path.write_text('# user adapter\n')
        with self.assertRaisesRegex(ValueError, 'differs'): engine.runtime_plan(self.root, self.payload)
        self.assertEqual(path.read_text(encoding='utf-8'), '# user adapter\n')

    def test_ast_hash_ignores_python_version_empty_fields(self):
        node = ast.parse('def sample(): return 1').body[0]
        before = engine.node_hash(node)
        node.type_params = []
        self.assertEqual(before, engine.node_hash(node))

class TransactionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.core = self.root / 'core'; self.home = self.root / 'home'
        self.core.mkdir(); self.home.mkdir()
        self.anchors = {'core': self.core, 'home': self.home}
        self.backups = self.home / 'backups'
        (self.core / 'a.py').write_bytes(b'original')
        (self.home / 'config.yaml').write_bytes(b'private: keep-secret\n')
        self.edits = [dict(scope='core', path='a.py', before=b'original', after=b'patched'),
                      dict(scope='core', path='helper.py', before=None, after=b'helper')]

    def tearDown(self): self.temp.cleanup()

    def test_backup_repeat_and_restore(self):
        identifier = engine.commit(self.anchors, self.edits, self.backups)
        self.assertEqual((self.core / 'helper.py').read_bytes(), b'helper')
        self.assertEqual((self.home / 'config.yaml').read_bytes(), b'private: keep-secret\n')
        self.assertIsNone(engine.commit(self.anchors, [], self.backups))
        engine.rollback(self.anchors, self.backups, identifier)
        self.assertEqual((self.core / 'a.py').read_bytes(), b'original')
        self.assertFalse((self.core / 'helper.py').exists())

    def test_write_failure_rolls_back_prior_writes(self):
        actual = engine.atomic_write
        def fail(path, data, mode=0o600):
            # Windows runner TEMP can resolve through a junction/short-name
            # alias; compare the same resolved identity used by the installer.
            if path.resolve() == (self.core / 'helper.py').resolve(): raise OSError('injected write failure')
            return actual(path, data, mode)
        with patch.object(engine, 'atomic_write', side_effect=fail):
            with self.assertRaises(OSError): engine.commit(self.anchors, self.edits, self.backups)
        self.assertEqual((self.core / 'a.py').read_bytes(), b'original')
        self.assertFalse((self.core / 'helper.py').exists())

    def test_preflight_detects_concurrent_edit(self):
        (self.core / 'a.py').write_bytes(b'changed after planning')
        with self.assertRaises(ValueError): engine.commit(self.anchors, self.edits, self.backups)
        self.assertFalse(self.backups.exists())

    def test_restore_refuses_later_user_edits_before_any_mutation(self):
        identifier = engine.commit(self.anchors, self.edits, self.backups)
        (self.core / 'a.py').write_bytes(b'new user edit')
        with self.assertRaises(ValueError): engine.rollback(self.anchors, self.backups, identifier)
        self.assertEqual((self.core / 'helper.py').read_bytes(), b'helper')
        self.assertEqual((self.core / 'a.py').read_bytes(), b'new user edit')

    def test_corrupt_backup_and_path_escape_are_rejected(self):
        identifier = engine.commit(self.anchors, self.edits, self.backups)
        (self.backups / identifier / '0').write_bytes(b'corrupt')
        with self.assertRaises(ValueError): engine.rollback(self.anchors, self.backups, identifier)
        with self.assertRaises(ValueError): engine.regular_target(self.home, '../outside')

    def test_symlink_target_is_rejected(self):
        try: (self.home / 'link').symlink_to(self.core, target_is_directory=True)
        except OSError: self.skipTest('Host does not permit creating test symlinks')
        with self.assertRaises(ValueError): engine.regular_target(self.home, 'link/a.py')

    def test_venv_python_symlink_is_not_resolved_to_base_python(self):
        from types import SimpleNamespace
        module_spec = importlib.util.spec_from_file_location('install_dashboard', ROOT / 'scripts/install-dashboard.py')
        module = importlib.util.module_from_spec(module_spec); module_spec.loader.exec_module(module)
        (self.core / 'hermes_cli').mkdir()
        (self.core / 'hermes_cli/main.py').write_text('# fixture\n')
        link = self.root / 'venv-python'
        try: link.symlink_to(sys.executable)
        except OSError: self.skipTest('Host does not permit creating test symlinks')
        _, selected = module.discover(SimpleNamespace(launcher=None, hermes_root=self.core, python=link))
        self.assertEqual(selected, link.absolute())

    def test_unverified_listener_is_never_stopped(self):
        from types import SimpleNamespace
        spec = importlib.util.spec_from_file_location('install_dashboard_safe', ROOT / 'scripts/install-dashboard.py')
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        with patch.object(module, 'listening', return_value=True), patch.object(module, 'helper', return_value={'safe': False, 'reason': 'unverified owner'}) as helper, patch.object(module.subprocess, 'Popen') as launch:
            result = module.activate(self.core, self.home, Path(sys.executable), SimpleNamespace(port=9127, restart='auto'), True)
        self.assertFalse(result['ready'])
        self.assertEqual(helper.call_count, 1)
        launch.assert_not_called()

    def test_other_home_listener_is_not_reported_ready_even_with_no_core_changes(self):
        from types import SimpleNamespace
        spec = importlib.util.spec_from_file_location('install_dashboard_identity', ROOT / 'scripts/install-dashboard.py')
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        with patch.object(module, 'listening', return_value=True), patch.object(module, 'helper', return_value={'safe': False, 'reason': 'different home'}), patch.object(module, 'verify_dashboard', return_value=True) as verify:
            result = module.activate(self.core, self.home, Path(sys.executable), SimpleNamespace(port=9127, restart='auto'), False)
        self.assertFalse(result['ready'])
        verify.assert_not_called()

if __name__ == '__main__': unittest.main()
