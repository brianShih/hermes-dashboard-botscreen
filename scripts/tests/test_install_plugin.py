import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('install_plugin', ROOT / 'scripts' / 'install-plugin.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class InstallTests(unittest.TestCase):
    def setUp(self):
        cache = ROOT / '.runtime'
        cache.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=cache)
        self.profile = Path(self.temp.name) / 'profiles' / 'bot-screen-lab'
        self.profile.mkdir(parents=True)
        (self.profile / 'config.yaml').write_text('terminal:\n  backend: local\n')
        self.backend = ROOT / 'hermes'

    def tearDown(self):
        self.temp.cleanup()

    def test_check_only_does_not_install(self):
        self.assertEqual(module.install(self.backend, self.profile, check_only=True)['status'], 'compatible')
        self.assertFalse((self.profile / 'plugins').exists())

    def test_install_is_repeatable_and_preserves_config(self):
        config = (self.profile / 'config.yaml').read_bytes()
        self.assertEqual(module.install(self.backend, self.profile)['status'], 'installed')
        self.assertEqual(module.install(self.backend, self.profile)['status'], 'already-installed')
        self.assertEqual((self.profile / 'config.yaml').read_bytes(), config)
        installed = self.profile / 'plugins' / 'bot-screen-lab' / 'dashboard' / 'dist' / 'index.js'
        self.assertEqual(installed.read_bytes(), (module.ARTIFACT / 'dist' / 'index.js').read_bytes())

    def test_default_profile_is_refused(self):
        with self.assertRaisesRegex(ValueError, 'isolated'):
            module.install(self.backend, self.profile.parent / 'default')

    def test_machine_dashboard_assets_keep_the_isolated_profile(self):
        home = self.profile.parent.parent
        before = (self.profile / 'config.yaml').read_bytes()
        result = module.install(self.backend, self.profile, dashboard_home=home)
        self.assertEqual(result['status'], 'installed')
        self.assertTrue((home / 'plugins/bot-screen-lab/dashboard/manifest.json').is_file())
        self.assertFalse((self.profile / 'plugins').exists())
        self.assertEqual((self.profile / 'config.yaml').read_bytes(), before)

    def test_unrelated_dashboard_home_is_refused(self):
        with self.assertRaisesRegex(ValueError, 'exact isolated'):
            module.install(self.backend, self.profile, dashboard_home=self.profile)

    def test_incompatible_backend_is_refused(self):
        with self.assertRaisesRegex(ValueError, 'incompatible'):
            module.install(Path(self.temp.name), self.profile)

    def test_replace_keeps_backup_outside_discovery_root(self):
        module.install(self.backend, self.profile)
        asset = self.profile / 'plugins' / 'bot-screen-lab' / 'dashboard' / 'dist' / 'index.js'
        asset.write_text('previous plugin')
        with self.assertRaisesRegex(ValueError, 'already exists'):
            module.install(self.backend, self.profile)
        module.install(self.backend, self.profile, replace=True)
        backups = list((self.profile / 'plugin-backups').glob('bot-screen-lab-*'))
        self.assertEqual(len(backups), 1)
        self.assertEqual((backups[0] / 'dashboard' / 'dist' / 'index.js').read_text(), 'previous plugin')
        self.assertEqual(len(list((self.profile / 'plugins').iterdir())), 1)

if __name__ == '__main__':
    unittest.main()
