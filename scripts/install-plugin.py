"""Install only the Bot Screen dashboard assets into an existing isolated Hermes profile."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent.parent
ARTIFACT = ROOT / 'bot-screen-plugin' / 'dashboard'

def install(hermes_root, profile_home, check_only=False, replace=False, dashboard_home=None):
    hermes_root = hermes_root.resolve()
    profile_home = profile_home.resolve()
    if profile_home.name != 'bot-screen-lab' or profile_home.parent.name != 'profiles':
        raise ValueError('Choose the named isolated profiles/bot-screen-lab home; default profiles are refused')
    if not (profile_home / 'config.yaml').is_file():
        raise ValueError('Create the bot-screen-lab profile with Hermes first; no configuration or secrets are copied')
    asset_home = profile_home
    if dashboard_home is not None:
        dashboard_home = dashboard_home.resolve()
        if (dashboard_home / 'profiles' / 'bot-screen-lab').resolve() != profile_home:
            raise ValueError('Dashboard home must own this exact isolated bot-screen-lab profile')
        asset_home = dashboard_home
    required = {
        'hermes_cli/web_routers/display.py': ['/api/display/ws'],
        'tui_gateway/methods_display.py': ['display.status','display.start','display.observe','display.lease.acquire','display.lease.release'],
        'web/src/plugins/registry.ts': ['buildWsUrl'],
    }
    for relative, capabilities in required.items():
        file = hermes_root / relative
        if not file.is_file() or any(value not in file.read_text(encoding='utf-8') for value in capabilities):
            raise ValueError(f'Backend or Dashboard SDK is incompatible: {relative}; see INSTALL_HERMES.md')
    manifest = json.loads((ARTIFACT / 'manifest.json').read_text(encoding='utf-8'))
    if manifest['name'] != 'bot-screen-lab' or manifest['entry'] != 'dist/index.js':
        raise ValueError('Unexpected plugin manifest')
    files = ['manifest.json', 'dist/index.js', 'LICENSE.novnc.txt']
    if any(not (ARTIFACT / file).is_file() for file in files):
        raise ValueError('Build the plugin first: cd bot-screen-plugin; npm ci; npm run build')
    target = asset_home / 'plugins' / 'bot-screen-lab'
    if (asset_home / 'plugins').is_symlink() or not target.resolve().is_relative_to(asset_home):
        raise ValueError('Plugin destination must stay inside the selected asset home')
    if target.is_symlink():
        raise ValueError('Existing plugin is a symlink; inspect it before installing')
    if target.exists() and any(item.is_symlink() for item in target.rglob('*')):
        raise ValueError('Existing plugin contains symlinks; inspect it before installing')
    same = all((target / 'dashboard' / file).is_file() and (target / 'dashboard' / file).read_bytes() == (ARTIFACT / file).read_bytes() for file in files)
    if check_only:
        return {'status': 'compatible', 'profile': 'bot-screen-lab', 'assetScope': 'dashboard-home' if dashboard_home else 'profile-home', 'assets': files, 'alreadyInstalled': same}
    if same:
        return {'status': 'already-installed', 'profile': 'bot-screen-lab'}
    if target.exists():
        if not replace:
            raise ValueError('A different plugin already exists; --replace explicitly backs it up before installation')
        backup = profile_home / 'plugin-backups' / (target.name + '-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
        backup.parent.mkdir(parents=True, exist_ok=True)
        # Exact sibling rename, no recursive deletion and no profile configuration changes.
        target.rename(backup)
    for file in files:
        destination = target / 'dashboard' / file
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ARTIFACT / file, destination)
    return {'status': 'installed', 'profile': 'bot-screen-lab', 'route': '/bot-screen', 'coreFilesModified': False, 'configurationModified': False}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--hermes-root', required=True, type=Path)
    parser.add_argument('--profile-home', required=True, type=Path)
    parser.add_argument('--dashboard-home', type=Path, help='Optional machine Dashboard home that owns the isolated profile; installs shared assets only')
    parser.add_argument('--check-only', action='store_true')
    parser.add_argument('--replace', action='store_true')
    args = parser.parse_args()
    try:
        result = install(args.hermes_root, args.profile_home, args.check_only, args.replace, args.dashboard_home)
    except (ValueError, OSError) as error:
        parser.exit(1, str(error) + '\n')
    print(json.dumps(result, indent=2))
