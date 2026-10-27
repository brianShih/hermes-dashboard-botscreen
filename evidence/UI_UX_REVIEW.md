# Bot Screen v0.3.0 UI / UX 優化

狀態：DONE。範圍為 Bot Screen Dashboard plugin；沒有修改 Hermes 核心、認證、控制權規則或遙測選擇。

## 改了什麼

| 原本的問題 | 現在的設計 | 驗證 |
|---|---|---|
| 多個同樣權重的按鈕並列 | 依狀態集中成觀看、接管、交回三個主要動作；維護工具移入更多操作 | 主要流程 E2E 通過 |
| 未觀看時只有大塊空白 | 加入引導標題、下一步操作、預設觀看與隔離環境說明 | 真實已啟動桌面的空白狀態通過 |
| 人工控制與觀看差異不明顯 | 模式文字、圖示、琥珀色控制提示及桌面外框 | 真實接管輸入、交回阻擋通過 |
| 斷線後不知道下一步 | Hermes 斷線提供重新連線，只有畫面斷線則重新觀看 | 異常關閉與恢復通過 |
| 畫面連接可能一直等待 | 15 秒期限、逾時提示與可用重試按鈕 | 測試頁抑制 RFB 握手畫面後確認期限與重試 |
| 小字與手機操作目標偏小 | 文字至少 12px、手機按鈕至少 44px、窄螢幕減少重複訊息 | 四個視窗尺寸檢查通過 |
| 鍵盤操作不明確 | 可見焦點，選單支援 Enter、Tab、Escape，Escape 後回到觸發按鈕 | 真實瀏覽器鍵盤檢查通過 |

保留滿版桌面與全螢幕。畫面保持比例，沒有透過變更遠端解析度或裁切來填滿；重連仍先回到觀看模式。

## 測試證據

- `ui-review.json`：7 項 UI 檢查通過，沒有瀏覽器執行期錯誤。
- `ui-deployment.json`：服務端顯示 0.3.0，實際提供的 bundle 與本機建置雜湊相符。
- `acceptance.json`：12 個主要流程 gates 通過，包含真實 framebuffer、接管／交回、3 輪斷線重連、票證重播及未登入拒絕。
- plugin 邏輯測試 8 項通過；installer 5 項回歸通過。先前 Python backend 38 項與 identity 9 項結果保留，此次未聲稱重跑完整上游測試。
- UI 尺寸：1920×1080、1280×720、768×1024、390×844；無水平溢出。
- 全螢幕進入及返回通過。

截圖：`ui-before.png`、`ui-empty.png`、`ui-after.png`、`ui-390.png`、`ui-disconnected.png`、`ui-fullscreen.png`、`ui-timeout.png`。過程中的 `*-failure.png` 屬歷史診斷，不是最終結果。

## 交付

- 外掛版本 0.3.0。
- `src/styles.css` 以文字嵌入既有單一 JS bundle，因此仍只需部署 manifest、bundle 與 noVNC 授權檔。
- 安裝包：`dist/bot-screen-hermes-plugin.zip`，只含白名單程式與文件，不含 profiles、登入資料、測試證據或 node_modules。
- 操作文件、browser launcher 與驗收腳本已配合新介面更新；測試改用連線狀態屬性，不再依賴按鈕排列位置。

## 範圍與限制

目前為 Windows 主機、專用 Chrome 與隔離 Linux 容器驗證。沒有 Git repository，未自行初始化版本庫或提交。

小螢幕首次使用時，宿主 Hermes 的 metrics 選擇提示可能佔用較多高度；plugin 提供有文字的全螢幕入口，不隱藏提示或替使用者做隱私選擇。本輪沒有驗證所有 Hermes 主題、螢幕閱讀器、觸控鍵盤或完整多使用者併發。

逾時檢查只在獨立測試頁抑制入站 RFB 握手，保留原生 WebSocket；正常流程測試使用真實桌面及輸入。沒有更改正式串流來讓測試通過。
