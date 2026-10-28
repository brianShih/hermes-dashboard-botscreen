"""Create a small install bundle from an explicit allowlist, without profiles or local reports."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parent.parent
files = [
    'Install.cmd', 'Install.ps1', 'install.sh', 'ARCHITECTURE.md', 'ARCHITECTURE.en.md', 'INTEGRATION.md', 'INTEGRATION.en.md', 'ONE_CLICK.md', 'ONE_CLICK.en.md',
    'SKILLS.md', 'installer/skill-baselines.json',
    'skills/bot-screen-linux/SKILL.md', 'skills/bot-screen-linux/references/linux-tasks.md',
    'skills/bot-screen-linux/references/environment.md', 'skills/bot-screen-linux/references/workflows.md',
    'skills/bot-screen-linux/scripts/environment_probe.py',
    'scripts/install-dashboard.py', 'installer/engine.py', 'installer/helper.py', 'installer/runtime-payload.json',
    'INSTALL_HERMES.md', 'INSTALL_HERMES.en.md', 'scripts/install-plugin.py', 'patches/runtime-linux-identity.patch',
    'CROSS_PLATFORM.md', 'CROSS_PLATFORM.en.md', 'patches/runtime-windows-lock.patch', 'patches/desktop-cross-platform.patch',
    'bot-screen-plugin/package.json', 'bot-screen-plugin/package-lock.json',
    'bot-screen-plugin/build.mjs', 'bot-screen-plugin/src/plugin.mjs', 'bot-screen-plugin/src/screen.mjs',
    'bot-screen-plugin/src/styles.css', 'bot-screen-plugin/src/i18n.mjs',
    'bot-screen-plugin/src/locales/en.json', 'bot-screen-plugin/src/locales/zh-Hant.json', 'bot-screen-plugin/src/locales/zh-Hans.json',
    'bot-screen-plugin/DESIGN.md', 'bot-screen-plugin/DESIGN.en.md',
    'bot-screen-plugin/dashboard/manifest.json', 'bot-screen-plugin/dashboard/dist/index.js',
    'bot-screen-plugin/dashboard/LICENSE.novnc.txt',
]
readme = '''# Bot Screen one-click installer / 一鍵安裝

Windows: fully extract, then double-click Install.cmd. Linux: run bash install.sh.
Read ONE_CLICK.en.md (English) or ONE_CLICK.md (繁體中文).
Requires existing compatible Hermes and a running Docker installation for Docker mode.
Reuses Hermes Python; no Node.js, npm or Git required. Includes guarded backend fixes,
isolated profile setup, backups, rollback and real RFB readiness checks. A backend
restart may require the service owner. installed-needs-attention is not full readiness.
The archive excludes user profiles, credentials and backups. Keep installation backups private.
Preserve bundled upstream license notices. See the guide for validation limits.

# Bot Screen 一鍵安裝包 0.6.0

Windows：完整解壓縮後雙擊 Install.cmd。
Linux：在解壓縮的資料夾執行 bash install.sh。

請先讀 ONE_CLICK.md。需要已安裝、版本相容的 Hermes；Docker 模式需要已啟動的 Docker。
沿用 Hermes 的 Python，不需要 Node.js、npm 或 Git。

安裝器會檢查並備份受影響檔案，整合後端修正、多國語言外掛及 bot-screen-lab 隔離 profile，
下載缺少的官方桌面映像並檢查實際 RFB 握手；安全條件符合時啟動或重啟 Dashboard。
不相容版本不會強制覆寫。結果若顯示 installed-needs-attention，請依指示處理重啟或依賴問題。
再次執行可檢查既有安裝；使用 --rollback latest 回復最近一次變更，保留桌面與聊天資料。

不含 Hermes 完整核心、Docker image、使用者 profile、密碼、node_modules、備份或測試證據。
安裝器包含指定函式的後端修正內容，會修改已通過檢查的核心函式與相關設定，詳見 ONE_CLICK.md。
內附預先建置的外掛 bundle；noVNC 授權在 bot-screen-plugin/dashboard/LICENSE.novnc.txt。
'''
output = ROOT / 'dist' / 'bot-screen-hermes-one-click-0.6.0.zip'
output.parent.mkdir(exist_ok=True)
hashes = {}
with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
    archive.writestr('README.md', readme)
    hashes['README.md'] = hashlib.sha256(readme.encode('utf-8')).hexdigest()
    for name in files:
        data = (ROOT / name).read_bytes()
        archive.writestr(name, data)
        hashes[name] = hashlib.sha256(data).hexdigest()
    archive.writestr('CONTENTS.json', json.dumps({'files':hashes,'noUserStateIncluded':True},indent=2))
import shutil
shutil.copy2(output, output.parent / 'bot-screen-hermes-plugin.zip')
(output.parent / 'SHA256SUMS.txt').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest() + '  ' + p.name + '\n' for p in sorted(output.parent.glob('bot-screen-hermes-one-click-*.zip'))), encoding='ascii')
print(json.dumps({'artifact':'dist/' + output.name,'files':len(files)+2,
                  'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'bytes':output.stat().st_size},indent=2))
