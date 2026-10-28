# Verified workflows / 可驗證工作流程

## 1. Environment / 環境

Read active-profile configuration through supported tools without dumping secrets. Confirm that desktop and terminal placement refer to the same environment. If this cannot be established, stop before modifying files. Then run the bundled `scripts/environment_probe.py` using Python 3 inside that terminal. Copy its content through the supported terminal/file mechanism if the skill is installed on the host; do not assume its host path exists inside Linux.
透過支援工具確認 profile、桌面與終端機指向相同環境，無法確認則停止修改。再在 Linux 終端機執行唯讀 probe；skill 在主機時需經支援機制傳入腳本內容，不假設主機路徑在 Linux 存在。

The probe reports capabilities, not container identity or mounts. Do not infer Docker/VM/native placement from its output. Ask the backend's recorded ownership checks to establish Docker identity. Avoid inspecting arbitrary containers.
probe 只回報能力，不證明容器身分或掛載。Docker 身分由後端擁有者檢查確認，不查看任意容器。

## 2. File round trip / 檔案往返

Use a task-specific new directory, preferably created with `tempfile.mkdtemp(prefix='bot-screen-check-')` for acceptance. Create a UTF-8 text file with synthetic content, read it back, rename it within that directory, and verify content again. Do not use personal documents as fixtures. For GUI requirements, open the file using an available application and inspect actual title/content; terminal success alone does not prove GUI behavior.
驗收使用全新測試目錄與假資料：寫入 UTF-8、讀回、目錄內重新命名、再核對內容。需要 GUI 證據時以實際應用開啟並查看，不把終端機成功當成 GUI 驗收。

Record the Linux output path. Promise a host-accessible download only after verifying the configured transfer mechanism. Never assume `/tmp` or the container writable layer is persistent.
記錄 Linux 產物路徑；確認傳輸機制後才能宣稱主機可下載，不假設暫存目錄與容器可寫層持久保存。

## 3. Human takeover and handback / 人工接管交回

Prepare a synthetic test document and let the viewer acquire control. The normal computer-use capture/action path should refuse while human control is held. Stop interaction; do not use a terminal to change the displayed document. After explicit handback and backend confirmation, capture fresh state, identify the user's edit, and continue from that edit rather than replacing it with stale content.
以測試文件進行接管；人工持有期間正常 computer-use 路徑應拒絕截圖／操作，也不可改用終端機修改該文件。明確交回並確認控制權後重新查看，辨識人工修改再繼續，不覆蓋成舊內容。

Automated acceptance may simulate viewer input against a dedicated fixture. Label this as simulated human interaction, not an actual person or model-driven Agent test.
自動驗收可模擬人工輸入，但須標示為模擬互動，不宣稱真人或模型 Agent 已操作。

## 4. Disconnect recovery / 斷線恢復

Use a dedicated fixture and a known completed edit. If viewer transport disconnects, reconnect in view mode and check both the document and current lease. An abnormal disconnect may retain the human lease. Reacquire through the supported UI if needed and explicitly hand back; never force-clear lease files. Resume Agent work only after confirmation.
異常斷線後以觀看重連，核對文件與 lease；人工 lease 可能保留。必要時由支援 UI 重新接管並交回，不手動刪鎖。確認後才繼續 Agent 工作。

Do not repeat the previous submission merely because the response was lost. Use a unique test marker or readback to distinguish completed work from pending work. If state is ambiguous, report it and seek task-specific guidance.
回應遺失不等於失敗；以唯一測試標記或讀回判斷，不盲目重送。無法判定時回報不確定狀態。
