**繁體中文** | [English](INSTALL_HERMES.en.md)

> **一鍵安裝 0.5.0：** Windows 完整解壓縮後雙擊 `Install.cmd`；Linux 執行 `bash install.sh`。前後端修正、隔離 profile、備份與回復已整合，請先看 [ONE_CLICK.md](ONE_CLICK.md)。下文保留架構與手動／舊版安裝說明。

# 將 Bot Screen 安裝到 hermes-agent

有兩種方式：

| 方式 | 適合情況 | 做法 |
|---|---|---|
| 安裝到既有 Hermes | 已有相容的 Linux／WSL Hermes backend，想在原 Dashboard 加入 Bot Screen | 安裝這份外掛到專用 profile |
| 本專案隔離容器 | Windows 主機，想沿用這裡已驗證的桌面環境 | 使用 `scripts/start-isolated.ps1` |

本文件不會將外掛安裝到日常使用的 default profile，也不會複製個人模型 key 或 Telegram 設定。新增的 installer 只部署前端 assets，不會啟動服務、修改 backend、變更 profile 設定或升級 Hermes。

若使用 `dist/bot-screen-hermes-plugin.zip`，先解壓再從該目錄執行下列步驟。小包只含外掛、安裝器、授權與可選修復 patch，內附已建置 bundle；不需要複製整個專案。`CONTENTS.json` 記錄封裝內容雜湊。

## 一、既有 Hermes 的必要條件

這不是只有一個網頁就能運作的 VNC 外掛。既有 Hermes 必須具備：

1. Dashboard plugin loader 與 SDK 的 `buildWsUrl`。
2. JSON-RPC 方法 `display.status`、`display.start`、`display.observe`、`display.lease.acquire`、`display.lease.release`。
3. `/api/display/ws` 畫面橋接、單次 ticket、控制權 lease 與後端 RFB input filter。
4. 能執行 Xvnc/Xfce 的 Linux 桌面環境。

此專案驗證的 Hermes 基底 commit 是 `62629e285614db8cdcc9c48b6732b89d584def68`。其他版本應先做能力檢查，不以版本名稱推定相容。只有舊版設定管理 Dashboard、沒有 display API 的 Hermes，單獨複製外掛不會增加後端功能。

原生 Windows 可以開瀏覽器觀看；這裡的桌面 backend 需在 Linux、WSL 或相容的容器／遠端 Linux 環境執行。這不會直接控制 Windows 桌面。

## 二、建置或準備外掛

在本專案根目錄開啟終端，進入外掛目錄：

```sh
cd bot-screen-plugin
npm ci --ignore-scripts --no-audit --no-fund
npm run build
cd ..
```

Windows PowerShell 可用 `npm.cmd`。若已有本專案交付的 `dashboard/dist/index.js`，可直接使用該產物。

要部署的內容只有：

```text
bot-screen-lab/
└─ dashboard/
   ├─ manifest.json
   ├─ dist/index.js
   └─ LICENSE.novnc.txt
```

不需要把整份 `hermes/`、`node_modules/`、`.runtime/` 或測試證據複製進既有 Hermes 的 plugins 目錄。

## 三、建立隔離 profile

在目標 Hermes 的執行環境中：

```sh
hermes profile create bot-screen-lab --no-alias --no-skills
hermes profile list
```

不要加 `--clone`、`--clone-all` 或 `--clone-channels`，避免帶入日常帳密與 Bot 設定。如果 profile 已存在，先用 `profile list` 確認它就是專用測試環境，不要重建或刪除。

這版外掛固定使用 **`bot-screen-lab`**，不是任意 profile 切換器。安裝器也會拒絕 default 或其他名稱。

下文需要兩個實際路徑：

- `HERMES_ROOT`：目標 Hermes 原始碼根目錄，內有 `hermes_cli/`、`tui_gateway/`、`web/`。
- `PROFILE_HOME`：剛建立的 `profiles/bot-screen-lab` 目錄，內有 `config.yaml`。

請依目標安裝的實際位置設定。自訂 `HERMES_HOME`、Windows 受管理安裝與不同 Linux 帳號可能有不同位置，不要套用別人的使用者目錄。

## 四、先檢查，再安裝

在本專案根目錄，用目標環境可用的 Python 3.10 以上版本執行。以下路徑是示意，需改成上一節查到的位置：

```sh
python scripts/install-plugin.py --hermes-root /path/to/hermes-agent --profile-home /path/to/hermes-home/profiles/bot-screen-lab --check-only

python scripts/install-plugin.py --hermes-root /path/to/hermes-agent --profile-home /path/to/hermes-home/profiles/bot-screen-lab
```

Windows 可使用引號包住路徑，例如 `--hermes-root "X:\path\hermes-agent"`；若 Python 在該環境名為 `python3`，改用 `python3`。安裝器為標準函式庫腳本，不需讀取 Hermes secrets。

安裝結果為：

```text
<PROFILE_HOME>/plugins/bot-screen-lab/dashboard/
```

若目標是「機器共用 Dashboard」（例如已運作的 9119，而非用 `--isolated` 啟動的專用 Dashboard），可額外指定它的 Hermes home，將共用 assets 裝到該 home 的 plugins 目錄：

```sh
python scripts/install-plugin.py --hermes-root /path/to/hermes-agent --profile-home /path/to/hermes-home/profiles/bot-screen-lab --dashboard-home /path/to/hermes-home --check-only
python scripts/install-plugin.py --hermes-root /path/to/hermes-agent --profile-home /path/to/hermes-home/profiles/bot-screen-lab --dashboard-home /path/to/hermes-home
```

`--dashboard-home` 必須確實擁有指定的 `profiles/bot-screen-lab`，不能指向無關 home。它只改變外掛 assets 的搜尋位置，操作目標仍固定是隔離 profile，並不讓外掛控制 default。已有不同版本時加 `--replace` 才會備份並換版。安裝後可使用現有 Dashboard 的外掛 rescan API 重新 discovery，不需直接停止整台機器的服務。

安裝器會檢查隔離 profile、來源能力與 bundle。相同內容可重複執行；已有不同版本時預設停止。確定要換版才加 `--replace`，舊 plugin 會移到該 profile 的 `plugin-backups/`，不放在會被 plugin loader 掃描的目錄中。

**相容性檢查只確認原始碼能力存在，不能代替目標環境的實際操作驗收。**

## 五、準備 Linux 桌面

若桌面放在 Hermes 所在的 Linux 主機，Debian／Ubuntu 可先安裝對應套件：

```sh
sudo apt-get update
sudo apt-get install tigervnc-standalone-server xfwm4 xfce4-panel xfdesktop4 xfce4-settings xfce4-terminal dbus-x11 x11-xserver-utils x11-utils x11-xkb-utils xauth fonts-dejavu-core
```

此清單來自本份 Hermes 的 `tools/bot_desktop/runtime.py`；不同發行版套件名稱不同。Python／Hermes 本身的依賴請使用該版本的正式安裝與 PM 流程，不要將此專案的 Windows Python 環境整份覆蓋進去。

專用 profile 的 `config.yaml` 可使用本機 Linux 桌面設定：

```yaml
terminal:
  backend: local
bot_desktop:
  placement: gateway
```

只合併上述設定，保留其他必要欄位。如果原 profile 已選擇 Docker／SSH sandbox，請先確認桌面應放在哪裡；不要為了顯示畫面而直接把既有 sandbox 改成 gateway 主機。

## 六、開啟 Dashboard

在目標 Hermes 的執行環境執行：

```sh
hermes -p bot-screen-lab dashboard --isolated --no-open --host 127.0.0.1 --port 9124
```

瀏覽器開啟 [http://127.0.0.1:9124/bot-screen](http://127.0.0.1:9124/bot-screen)。如果 9124 被其他服務占用，選擇未使用的埠，不要直接停止不明服務。

正式新增或更新外掛後，重新啟動這份專用 Dashboard 並重新整理頁面，讓後端重新 discovery。這是 Webapp plugin，不會自動新增 Electron Desktop 面板。

遠端主機應經 SSH tunnel 或既有已配置認證的部署入口存取，不要只把上述綁定位址改成公開介面。例：

```sh
ssh -L 9124:127.0.0.1:9124 user@your-hermes-host
```

## 七、操作驗收

1. 確認左側出現 **Bot Screen**，且標示 `bot-screen-lab`。
2. 首次按「啟動並觀看」；桌面已運作時直接按「觀看畫面」。維護工具在「更多操作」。
3. 在觀看模式嘗試滑鼠鍵盤，確認桌面不接收輸入。
4. 按「接管操作」，確認可輸入測試文字。
5. 按「交回控制權」，確認再次禁止輸入。
6. 異常斷線後重新連線，應預設觀看；必要時重新接管並明確交回。
7. 檢查全螢幕、Esc 返回，以及視窗縮放。

目前附帶的 `scripts/acceptance.mjs` 是針對本專案專用容器、9124 埠與合成測試視窗設計，不是可對任意生產 Hermes 直接執行的通用測試器。不要為了跑它而複製生產登入資料到專案。

## 八、Linux 程序識別修復

外掛 installer 不會修改 Hermes backend。此專案另附 `patches/runtime-linux-identity.patch`，修復本份基底版本在 Docker 時鐘漂移時可能誤判桌面已停止的問題。

若目標 Hermes 已有等效修復，不需重複套用。只有在目標版本、差異與問題符合時，在目標 Git checkout 先檢查：

```sh
git status --short
git apply --check /path/to/bot-screen/patches/runtime-linux-identity.patch
```

確認目標檔案沒有自己的未提交修改，並保留可回復的版本後，才套用：

```sh
git apply /path/to/bot-screen/patches/runtime-linux-identity.patch
```

`--check` 失敗時不要覆寫整份 `runtime.py`，不同版本需另外移植。受管理或 bundled Hermes 安裝應使用它的更新方式，不直接修改打包 payload。這項修復在本專案的隔離 Linux 容器驗證過，尚未在你的其他安裝上執行。

## 九、Windows 隔離容器替代方案

若沒有可用的 Linux Hermes backend，可沿用本專案已驗證的本機 image：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-isolated.ps1
node scripts/open-browser.mjs
```

這個入口啟動本專案自己的 Hermes 副本，不會把外掛安裝進另一份正在使用的 Hermes。Docker image 不在專案夾內；移轉或重建限制見 [INTEGRATION.md](INTEGRATION.md)。

## 移除外掛

先關閉這份專用 Dashboard，將 `<PROFILE_HOME>/plugins/bot-screen-lab` 移出 plugins 目錄，再啟動確認。只移除這個外掛，不刪除整個 profile 或其資料。若曾套用 runtime patch，需依該 Git checkout 的實際差異另行處理；移除外掛不會自動還原 backend。


## 多國語言（v0.4.0）

Bot Screen 支援繁體中文、簡體中文與 English。進入 Bot Screen，開啟右上角「更多操作（•••）」→「語言」，選擇語言或「跟隨 Hermes」。預設跟隨 Dashboard 的語言設定；不支援的語言回退英文。沒有宿主語言時才參考瀏覽器語言。

語言偏好只儲存在目前網站的瀏覽器 localStorage（`bot-screen:language:v1`），不修改 Hermes 的語言、帳號或隔離 profile。切換語言會立即更新按鈕、輔助標籤、狀態與已顯示的訊息，保留現有桌面連線及控制權。已知前端錯誤有翻譯；後端原始錯誤保留在本地化提示中，方便排查。

翻譯檔位於 `bot-screen-plugin/src/locales/`，語言解析及回退邏輯位於 `src/i18n.mjs`。新增語言時補齊相同訊息鍵與參數，再加入語言清單及別名解析，執行單元測試與建置。沒有新增執行期套件。

多國語言前端與 Windows／Docker 後端修正已安裝到日常 Dashboard（9119），並通過真實畫面、接管／交回與三輪異常斷線重連驗收。隔離 Linux Dashboard（9124）回歸通過；跨平台範圍與安裝方式見 CROSS_PLATFORM.md。


Windows／Docker 後端的跨平台適配、補丁與驗收範圍，見 [CROSS_PLATFORM.md](CROSS_PLATFORM.md)。前端外掛更新與後端核心補丁是兩個步驟；後端變更必須重啟實際監聽 Dashboard 連接埠的程序。
