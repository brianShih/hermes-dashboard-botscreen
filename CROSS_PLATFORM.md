> **一鍵安裝 0.5.0：** Windows 完整解壓縮後雙擊 `Install.cmd`；Linux 執行 `bash install.sh`。前後端修正、隔離 profile、備份與回復已整合，請先看 [ONE_CLICK.md](ONE_CLICK.md)。下文保留架構與手動／舊版安裝說明。

# Bot Screen 跨平台後端

Dashboard 可位於 Windows 或 Linux；隔離桌面仍由 Linux 提供。macOS 使用相同適配介面，但本次沒有 macOS 真機驗收。

## 本次實作

- `tools/bot_desktop/transport.py`：從 profile 的 `sandbox.json` 重接確切 Docker 容器，不依賴 terminal 的程序內登記表。檢查 marker profile、桌面目錄、完整容器 ID、執行狀態與 `hermes-agent`／`hermes-profile` 標籤；找不到或不相符時拒絕連線。Docker 執行檔由既有 resolver 取得，不執行 marker 指定的任意程式。
- Windows 串流使用有背壓的管線讀寫適配器，避免把一般 subprocess 管線接進 Windows Selector／Proactor transport。讀寫使用工作執行緒；寫入緩衝有上限，關閉時先結束本次 Docker exec client，再關閉管線，使等待中的讀寫能結束。容器內桌面保持運作。
- Linux 保留既有 asyncio 管線路徑。WebSocket 的票證、來源檢查、RFB 輸入過濾與控制權規則維持共用。
- Windows 的桌面啟動鎖與控制權檔案鎖使用實際的跨行程鎖，不略過鎖定。Linux 保留 flock。

本輪主要補齊 Docker 桌面的狀態查詢、重接與串流。SSH、Singularity、共享容器 key、多使用者高併發和長時間壓力測試不在本輪驗收範圍；既有啟動／停止生命週期仍由 terminal backend 管理。不要宣稱所有 backend 或 macOS 已驗收。

## 安裝到既有 Hermes

一般外掛安裝器只更新前端，不修改 Hermes 核心。Windows 後端修正屬額外的核心補丁，需先備份下列檔案：

```text
tools/bot_desktop/runtime.py
tools/bot_desktop/lease.py
hermes_cli/web_routers/display.py
```

對相容版本先檢查兩個補丁，再依序套用：

```powershell
git -C <HermesRoot> apply --ignore-space-change --check <PackageRoot>/patches/runtime-windows-lock.patch
git -C <HermesRoot> apply --ignore-space-change <PackageRoot>/patches/runtime-windows-lock.patch
git -C <HermesRoot> apply --ignore-space-change --check <PackageRoot>/patches/desktop-cross-platform.patch
git -C <HermesRoot> apply --ignore-space-change <PackageRoot>/patches/desktop-cross-platform.patch
```

已安裝 Windows 啟動鎖的環境應略過第一個補丁。補丁會新增 `tools/bot_desktop/transport.py` 與 `hermes_cli/web_display_streams.py`。如果檢查失敗，表示版本或本地修改不同，先比對，勿強制覆蓋。補丁目標為本專案記錄的 Hermes 程式形狀，不承諾任意版本可直接套用。

**套用後必須重新啟動提供 Dashboard 的 Python 後端。** 網頁重新整理、重新開分頁，或重啟另一個 Messaging Gateway，都不會重新載入該程序中的 Python 模組。

## 驗證

- `scripts/test-runtime-lock.py`：真實跨行程啟動鎖與例外釋放。
- `scripts/test-lease-processes.py`：四個程序執行 100 次控制權更新，核對精確 epoch。
- `scripts/test-transport.py`：擁有者拒絕、二進位串流、背壓上限、取消讀取後程序清理。
- `scripts/test-live-rfb.py`：Windows Selector loop 從新程序重接真實桌面並完成雙向 RFB 握手。
- `scripts/windows-acceptance.mjs`：真實畫面／輸入、觀看阻擋、接管／交回及三輪異常斷線重連。
- `scripts/acceptance.mjs`：Linux 9124 完整回歸，包括票證重播與未登入拒絕。

實際結果以 `evidence/windows-9119.json`、`evidence/windows-9125.json` 和 `evidence/acceptance.json` 為準。
