# Linux task guidance / Linux 工作指引

## Files and sharing / 檔案與交換

Inspect the intended directory before writing. Quote paths, preserve existing work, and verify a copied or saved file by reading its relevant content or metadata. A download path inside Linux is not automatically accessible on Windows. Establish a configured shared mount or supported transfer path before promising host access.
寫入前查看目標，路徑加引號並保留既有工作；以內容或資訊確認存檔。Linux 下載目錄不等於 Windows 可存取位置，先確認共用掛載或傳輸機制。

For deletion or recursive moves, resolve and inspect the exact target and confirm it lies within the task's intended directory. Avoid broad wildcards. Use reversible moves when suitable. Never clean unrelated home directories, profile state, or containers.
遞迴刪除或搬移前確認實際目標與範圍，避免廣泛萬用字元；適合時先移至可回復位置，不清理無關家目錄、profile 或容器。

## Applications and browser / 應用程式與瀏覽器

Use available apps rather than assuming Xfce shortcuts or a particular browser. Inspect window titles and current state. Verify focus before typing. File chooser and browser dialogs can change the coordinate space. After opening a document, verify its title/content, not merely that an application launched.
不假設固定快捷鍵或瀏覽器；輸入前確認視窗與焦點，檔案選擇視窗可能改變座標。開啟文件後核對標題或內容。

For logins, ask the user to take control and enter secrets; resume after handback and verify only the resulting signed-in state. Do not retrieve browser credential databases or copy personal host browser profiles.
登入時由使用者接管輸入秘密；交回後只確認登入結果，不讀取密碼資料庫或複製主機瀏覽器 profile。

## Terminal and packages / 終端機與套件

Use non-secret discovery such as `pwd`, `id -un`, and selected fields from `/etc/os-release` in the confirmed Linux terminal. Do not dump `env`, `.env`, process environments, or complete configuration files to discover context.
確認 Linux 終端機後可用 pwd、id -un 與 os-release 的必要欄位判斷環境；不傾印環境變數、.env、程序環境或完整設定檔。

Choose apt/dnf/etc. only after identifying the distribution and tool availability. Installing packages requires task authorization and suitable permissions; do not automatically invoke sudo, disable security controls, or use curl-pipe-shell installers. A package in an ephemeral container may disappear when it is recreated; explain persistence rather than changing host packages.
確認發行版後選套件管理器；安裝需符合任務授權及權限，不自行 sudo、關閉防護或執行 curl-pipe-shell。暫存容器重建可能遺失套件，先說明持久性，不改裝主機套件。

## Troubleshooting / 排錯

Separate missing dependency, permission error, resource exhaustion, process failure, and viewer transport failure. Inspect bounded relevant logs with secrets redacted. Do not kill every similarly named process or clear lock files without identifying their owner. A native dependency such as fcntl belongs to the Linux/POSIX implementation; a Windows host requires the project's adapter, not a fabricated pip package.
分辨缺少依賴、權限、資源、程序與觀看串流問題；只讀必要且去敏感的日誌。不批次殺同名程序或任意移除鎖。Windows 缺 fcntl 應使用平台適配，不安裝虛構 pip 套件。
