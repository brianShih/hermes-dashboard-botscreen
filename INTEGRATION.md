**繁體中文** | [English](INTEGRATION.en.md)

# Bot Screen Webapp 整合

要將外掛裝進另一份既有 `hermes-agent`，請依 [INSTALL_HERMES.md](INSTALL_HERMES.md) 操作。下文是本專案自己的隔離容器環境，不會自動安裝到日常 Hermes。

本機 Windows 主機上的 Hermes Webapp，透過 localhost:9124 連到專用 Linux 容器桌面。不是原生 Windows 桌面或完整 VM 驗收。狀態與逐項證據見 `evidence/QA.md`、`evidence/acceptance.json`。

## 程式如何接起來

```text
hermes/web                          本目錄建置的 React Dashboard
  -> dashboard plugin loader
bot-screen-plugin/dashboard        manifest + noVNC bundle
  -> /api/ws                       display.* JSON-RPC
  -> /api/display/ws               單次票證 + RFB binary stream
hermes/hermes_cli/web_routers/display.py
  -> RfbClientFilter + profile lease
hermes/tools/bot_desktop            程序管理 / Unix socket
  -> TigerVNC Xvnc + Xfce           真實 Linux framebuffer
```

plugin 位於 Hermes 核心之外，沒有改 Dashboard 的 App.tsx 或新增另一個認證機制。啟動時在隔離 profile 的 plugins 目錄建立到 `/plugin` 的連結，使用既有 plugin discovery 載入 `/bot-screen`。

`src/screen.mjs` 與原有測試來自 `<USER_HOME>\Projects\hermes-bot-screen-lab`；此版本改用 Dashboard SDK 的 `buildWsUrl`，加入明確重連、連線世代檢查、lease 事件的 profile/viewer 篩選與接管失敗檢查。每次重新觀看均取得新票證，重新連線不自動取得輸入權。

## 隔離邊界

- 容器：`bot-screen-integration`，標籤 `com.sigensys.bot-screen=integration`。
- profile：容器內 `/lab/profiles/bot-screen-lab`。
- 宿主只發布 `127.0.0.1:9124`；容器內 FastAPI 綁定 0.0.0.0 並啟用密碼認證 gate。
- `hermes/`、plugin 和 scripts 都以唯讀 bind mount 掛入；沒有掛入宿主 Hermes home、Docker socket、金鑰或日常 Chrome profile。
- 測試密碼隨機產生，僅留在容器的 `/lab/test-login.json`，開啟瀏覽器時在程序記憶體中使用，不印出。
- 沒有啟動 messaging Gateway、呼叫模型或登入桌面內的外部帳號。
- 原本 `hermes-bot-screen-lab` 容器與 profiles 保留。整合過程的初始測試容器以停止狀態保存在 `bot-screen-integration-bootstrap-backup`。

## 啟動、操作與停止

在專案根目錄：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start-isolated.ps1
node scripts/open-browser.mjs
```

瀏覽器會自動登入專用 Dashboard。首次按「啟動並觀看」；已有桌面時按「觀看畫面」。需要輸入時按「接管操作」，結束後按「交回控制權」。斷線後按「重新連線」再觀看，預設為觀看模式。若異常斷線保留了人工控制權，請明確接管，再交回。「更多操作」提供更新狀態、重新連線與單獨啟動桌面。

專用 Chrome 預設最大化，桌面區會隨視窗大小填滿剩餘空間。按「全螢幕」可隱藏 Dashboard 外框，按 Esc 或「離開全螢幕」返回。遠端畫面保持比例，不裁切或拉伸；1280×720、1600×900、1920×1080 與全螢幕的版面驗證見 `evidence/layout-check.json`。

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/stop-isolated.ps1
```

停止會保留容器內的 profile。刪除容器會失去這份測試資料。本專案腳本不自動刪除容器，也不接管或停止其他 Hermes 服務。

## 建置前提與重建

這是目前主機已驗證的本機開發環境，不是乾淨機器安裝包。需 Docker Desktop、Node 24.14.0 或符合上游 engines 的版本、Chrome，以及本機 image `bot-screen-integration-runtime:local`。

該 image 以既有 `hermes-bot-screen-lab-runtime:local` 為基底，只額外加入原 lab 的 Python interpreter 與 venv 套件，不含其 profile／登入資料。需要重建 image 時：

```powershell
python scripts/prepare-runtime.py
```

此重建命令依賴現有原 lab 容器；目前 image 建好後，日常 start 不再依賴原 lab 容器運作。沒有遠端 image 發布或乾淨主機驗收。

重建 Webapp：

```powershell
Set-Location hermes
npx.cmd --yes npm@11.17.0 ci --workspace web --workspace @hermes/shared --ignore-scripts --no-audit --no-fund
node scripts/build/web.mjs
Set-Location ../bot-screen-plugin
npm.cmd ci --ignore-scripts --no-audit --no-fund
npm.cmd run build
```

系統 npm 11.12.1 不符合 Hermes 上游 engines；上述命令使用相容 npm，不更改全域安裝。

## 可重跑驗證

```powershell
# plugin 邏輯
Set-Location bot-screen-plugin
npm.cmd test
Set-Location ..
# 真實瀏覽器、桌面與輸入
node scripts/acceptance.mjs
# 程序識別回歸
docker exec --workdir /opt/hermes --env PYTHONPATH=/opt/hermes --env HERMES_HOME=/lab/profiles/bot-screen-lab bot-screen-integration /opt/hermes-venv/bin/python /integration/identity_regression.py
```

E2E 會建立專用 Tk 測試視窗並替換同一路徑的舊 fixture，只輸入合成文字。使用真的 noVNC、FastAPI、Xvnc、Xfce 與檔案回讀；沒有 mock framebuffer 或 mock lease。以 WebSocket code 4002 誘發異常關閉，驗證後端保留人工 lease，再重新建立連線。這不是實際拔網路或長時間網路穩定性測試。

接管後測試等待 350ms，涵蓋官方 bridge 最多 250ms 的跨程序 lease 刷新；沒有評估即時輸入延遲。連續三輪都驗證同一桌面程序的 kernel identity，不以重新啟動桌面代替重連。

## 本地後端修復

只修改 `hermes/tools/bot_desktop/runtime.py`，移植 lab 的 Linux identity 修復。原始碼版本用 psutil 的 epoch create_time 識別 launcher；實測同一活程序的值漂移 1 秒，超過原本嚴格容差。新啟動改用 boot ID、PID namespace inode 與 `/proc/PID/stat` start ticks，舊格式仍保留嚴格檢查，不放寬 PID 重用保護。基線與修復後證據在 `evidence/identity-*.txt`。

冷啟動驗收另修正測試 fixture 的視窗管理與座標讀取；診斷確認輸入已被後端放行，問題是繞過視窗管理器的測試視窗未取得焦點。此修正沒有改動正式串流或認證後端。
