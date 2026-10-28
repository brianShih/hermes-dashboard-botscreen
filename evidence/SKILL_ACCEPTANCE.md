# Linux skill acceptance / Linux 操作技能驗收

Skill 1.1.0 is included in installer 0.6.0 and installed into the existing Windows Hermes `bot-screen-lab` profile. Other personal profiles were not modified.
Skill 1.1.0 已整合至安裝器 0.6.0，並安裝到現有 Windows Hermes 的 bot-screen-lab profile，未安裝到其他個人 profile。

## Passed / 通過項目

- Extracted installer archive verified against every CONTENTS.json hash; real installation created a transactional backup. A repeat check reported no planned changes.
  解壓後逐項核對雜湊，實際安裝產生備份；重複檢查沒有待修改檔案。
- Real Hermes `skill_view` read the installed entry point, three references, and the probe script. Windows host filtering accepts the skill.
  真實 skill_view 可讀取入口、三份參考與腳本，Windows 主機篩選通過。
- Real backend ownership inspection and canonical Docker IDs confirmed that the Hermes terminal tool and viewed desktop share the same target under a routed profile/session context.
  以真實後端擁有者檢查與完整容器 ID，確認正確 profile/session 上下文中的 terminal 與觀看桌面一致。
- The actual terminal tool ran the read-only probe and created/read/renamed/verified a synthetic UTF-8 Chinese/English text file in a unique temporary directory.
  實際 terminal 工具完成唯讀探查，以及獨立暫存目錄中的中英文字檔寫入、讀回、改名與核對。
- On Dashboard 9119, the actual viewer rendered 1440×900 frames. View-only input was blocked; simulated human takeover accepted real keyboard input.
  9119 顯示真實畫面，觀看模式阻擋輸入，模擬人工接管後接受實際鍵盤輸入。
- During human control, actual `computer_use` capture returned `human_has_control`. After explicit handback, actual capture succeeded.
  人工控制期間真實 computer_use 截圖遭拒，交回後恢復截圖。
- Three abnormal viewer-disconnect cycles retained the human lease, reconnected in view mode, and permitted explicit takeover/handback without duplicate fixture input.
  三輪異常斷線保留人工 lease，重連為觀看模式，可重新接管並交回，測試輸入未重複。
- Installer tests: 22 cases, 20 passed and 2 host symlink-permission skips. Plugin tests: all 12 passed. Skill install coverage includes non-mutating planning, repeat installation, rejection of unknown local edits, and rollback.
  安裝測試 22 項中 20 通過、2 項因主機符號連結權限略過；外掛 12 項全過，包含 skill 規劃不寫入、重複安裝、當地修改保護與回復。

## Limits and follow-up / 限制與後續

These are real tool/backend/browser acceptance tests driven by a deterministic harness. They are not a model-driven autonomous Agent evaluation or a real person entering credentials. GUI acceptance uses a synthetic test window; it does not prove every editor/browser workflow. File data stayed inside Linux; host download/shared-mount transfer was not tested. Container recreation, persistence across recreation, clean-machine installation, and macOS were not tested.
本次為確定性腳本驅動的真實工具、後端與瀏覽器驗收，不是模型自主 Agent 或真人登入測試。GUI 使用測試視窗，未驗收所有編輯器／瀏覽器流程；檔案留在 Linux，未測主機傳輸、重建持久性、乾淨新機或 macOS。

The installer reported `installed-needs-attention`: it could not prove a safe managed restart owner for the existing 9119 process and did not force-stop it. Files and skill were installed and the RFB handshake passed. Browser/tool acceptance subsequently passed on 9119, but this does not prove that the existing server reloaded every changed Python function. The service owner should restart Dashboard through its original launch mechanism. New Agent conversations can discover the installed skill.
安裝器回報 installed-needs-attention：無法證明現有 9119 程序可安全由它重啟，因此未強制停止。檔案及 skill 已安裝，RFB 握手通過；後續 9119 瀏覽器與工具驗收通過，但不代表現有程序已重新載入每個 Python 修改。請由原管理方式重啟 Dashboard；新 Agent 對話可發現已安裝 skill。

An early harness invocation omitted normal Hermes bootstrap/profile/session initialization and therefore could not prove the terminal target. The corrected harness uses normal configuration and routed session context, then compares canonical container identity before writing. This is why tool success alone is insufficient routing evidence.
初版驗收呼叫未完整初始化 Hermes bootstrap/profile/session，無法證明 terminal 目標；修正後使用正常設定與路由上下文，寫入前比對實際容器身分。工具成功本身不足以證明路由正確。
