# Bot Screen 一鍵安裝（0.5.0）

把多國語言外掛、Windows／Linux 後端修正與隔離 profile 整合成同一個安裝入口。適用於**已安裝 Hermes、且程式版本通過相容性檢查**的電腦；不是 Hermes 本體的安裝器。

## 開始安裝

1. 電腦先安裝 Hermes。使用 Docker 桌面時，Windows 開啟 Docker Desktop 並切到 Linux containers；Linux 啟動 Docker Engine。
2. 將 `bot-screen-hermes-one-click-0.5.0.zip` **完整解壓縮**到一個資料夾，不要直接在壓縮檔內執行。
3. Windows 雙擊 **`Install.cmd`**。Linux 在解壓縮的資料夾執行：

   ```bash
   bash install.sh
   ```

安裝器會尋找 Hermes 的 Python，不需要另外安裝 Node.js、npm 或 Git。Docker 桌面映像不存在時會下載官方 `nousresearch/hermes-sandbox:desktop`；映像較大，時間取決於網路。安裝器不會自行安裝 Docker、要求系統重新開機、執行 sudo 或持續提升權限。

如果系統缺少 Docker 或 Hermes，畫面會指出缺少項目，完成前置安裝後重新執行即可。Docker 安裝來源：[Windows Docker Desktop](https://docs.docker.com/desktop/setup/install/windows-install/)／[Linux Docker Engine](https://docs.docker.com/engine/install/)。

成功後會開啟 `http://127.0.0.1:9119/bot-screen`。右上角「••• → 語言」支援繁體中文、簡體中文、英文與跟隨 Hermes。

## 安裝器會做什麼

- 檢查相容的 display API、Dashboard SDK，以及將修改的 Python 函式；陌生版本或已被另行修改的函式會停止安裝，不強制覆寫。
- 備份並套用 Windows 啟動／控制權鎖、Docker 擁有者重接、Windows 串流適配與 Linux 桌面程序識別修正。只替換已辨識的函式並加入兩個支援模組，保留檔案中的其他程式。
- 在選定 Hermes 資料目錄建立或使用 `profiles/bot-screen-lab`；新 profile 使用空白 `.env`，不複製預設 profile 的密碼、API key 或聊天資料。
- 在 Dashboard 資料目錄安裝外掛，將 `bot-screen-lab` 加入啟用清單，保留其他外掛、設定及 YAML 註解。
- 必要時下載 Docker 映像，啟動隔離桌面並驗證實際雙向 RFB 握手。這不是自動登入外部網站，也不會輸入個人資料。
- 新啟動的 Dashboard 僅綁定 `127.0.0.1`。若能證明原 Dashboard 屬於此安裝、目前沒有活躍 session／人工接管，才會嘗試自動重啟；不停止 Messaging Gateway、其他使用者程序或不明服務。

若 Dashboard 由管理員、systemd、Docker 或其他監督器啟動，或目前仍有人操作，可能需要由原擁有者重新啟動。**網頁重新整理不等於後端重啟。** 畫面顯示 `installed-needs-attention` 時，檔案可能已安裝完成，但不能當作已可用；請看結果中的 `dashboard.reason` 或 `desktop.error`。

## 指定安裝位置

自動尋找不適合多份 Hermes 共存的電腦時，明確指定位置。`--hermes-root` 是含 `hermes_cli/`、`tools/` 的程式目錄；`--hermes-home` 是含 `config.yaml`、`profiles/` 的資料目錄。

Windows PowerShell：

```powershell
.\Install.ps1 --hermes-root "D:\Apps\hermes-agent" --hermes-home "D:\HermesData"
```

Linux：

```bash
bash install.sh --hermes-root /opt/hermes-agent --hermes-home "$HOME/.hermes"
```

不在 PATH 的舊式安裝，可再指定 Hermes 現有的 Python：

```bash
bash install.sh --hermes-root /opt/hermes-agent --hermes-home "$HOME/.hermes" --python /opt/hermes-agent/.venv/bin/python
```

進階選項：

| 選項 | 用途 |
|---|---|
| `--check-only` | 相容性／依賴與修改清單；不套用檔案、不下載映像、不啟動桌面 |
| `--backend docker` | 明確使用 Docker；只調整專用 Bot Screen profile |
| `--backend native` | 已備齊 Xvnc／Xfce 等套件的 Linux 原生後端；仍使用隔離 profile，但不是容器隔離 |
| `--restart never` | 不啟動或重啟 Dashboard，由服務管理者自行處理 |
| `--port 9128` | 指定本機 Dashboard 埠；預設 9119 |
| `--no-open` | 不自動開啟瀏覽器 |
| `--skip-smoke` | 僅安裝檔案，略過真實桌面驗證；不會回報完整可用 |

預設新 profile 使用 Docker；已有可用 Linux 原生 profile 時會沿用原生模式。SSH、Singularity 與 explicit shared-container key 不在此安裝器支援範圍。現有不支援的 profile 設定會被拒絕，不會自動退回本機桌面。

## 備份與回復

每次實際變更的備份位於 Hermes 資料目錄：

```text
profiles/bot-screen-lab/plugin-backups/one-click/<時間戳>/
```

**備份可能包含你原有設定中的私人資料**，不應分享或放進公開安裝包。安裝包本身不包含使用者 profile、帳密、備份、測試報告、Docker 映像或 node_modules。

以相同入口回復最近一次安裝：

```powershell
.\Install.ps1 --rollback latest
```

```bash
bash install.sh --rollback latest
```

自訂路徑安裝時，回復也要傳入相同 `--hermes-root`／`--hermes-home`。安裝後若有人修改過目標檔案，回復會停止，避免覆蓋後續工作。回復不刪除桌面資料、容器或聊天紀錄；回復後須重啟 Dashboard 載入舊程式。

安裝結果保存在 Hermes 資料目錄的 `runtime/bot-screen-installer/result.json`。結束碼：`0`＝可用／檢查或回復成功，`2`＝檔案已安裝但仍有待處理項目，`1`＝安裝停止或失敗。寫入中失敗時會自動還原本次已寫入的檔案。

## 驗證範圍

本版以目前 Windows 主機的乾淨目錄、Docker 桌面，以及 Linux 容器內的乾淨目錄／原生桌面驗證安裝、重複執行及回復；不是不同實體電腦、全新 Windows VM、所有 Linux 發行版或 macOS 的全面認證。新機的 Docker／Hermes 前置安裝、系統權限與不同 Hermes 版本仍需通過現場檢查。

安裝包附 `CONTENTS.json` 供損毀檢查；這不是數位簽章。
