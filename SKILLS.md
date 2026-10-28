# Agent skills / Agent 操作技能

本專案提供 Hermes skill：[bot-screen-linux](skills/bot-screen-linux/SKILL.md)。這是 Agent 操作規則，不是 VM 建置器，也不會增加工具或作業系統權限。
This project provides the Hermes `bot-screen-linux` skill. It guides Agent behavior; it does not provision a VM, add tools, or grant operating-system privileges.

## 安裝到指定 profile / Install into a selected profile

先確認要操作桌面的 Hermes profile 資料目錄。將整個 `skills/bot-screen-linux/` 資料夾複製到該目錄的 `skills/`，保留 references 子目錄。不要只複製 SKILL.md。
Locate the data directory of the Hermes profile that operates the desktop. Copy the entire `skills/bot-screen-linux/` folder into its `skills/` directory, retaining references.

目的地結構 / Destination layout:

```text
<profile-home>/skills/bot-screen-linux/
  SKILL.md
  references/
    linux-tasks.md
    environment.md
```

此目錄位於執行 Hermes Agent 的資料環境，不一定在被觀看的 Linux 容器內。不要把 Windows 主機的安裝路徑直接當作 Linux profile 路徑。
This is the data environment of the running Hermes Agent, which is not necessarily inside the viewed Linux container. A Windows installation path is not automatically a Linux profile path.

若目的地已有同名 skill，先比對與備份當地修改。開啟該 profile 的新對話，要求 Agent 列出 skills 並讀取 `bot-screen-linux`；確認可讀取兩份 references。接著以建立測試文字檔、確認內容的低風險工作驗證路由至正確桌面。
If a skill of the same name exists, compare and back up local edits first. Start a new conversation in that profile, ask the Agent to list skills and read `bot-screen-linux`, and verify both references are accessible. Use a low-impact task such as creating and checking a test text file to verify target routing.

範例要求 / Example request:

> 使用 bot-screen-linux skill，在目前 Bot Screen 的 Linux 桌面建立一份測試文字檔並確認內容；我接管時請暫停。
>
> Use the bot-screen-linux skill to create and verify a test text file in the Linux desktop shown by Bot Screen. Pause while I take control.

## 一鍵安裝 / One-click installation

0.6.0 安裝器自動將 skill 及 references/scripts 安裝到專用 bot-screen-lab profile，納入備份與回復。已被自行修改的同名檔案會停止更新，避免覆蓋。這不會把 skill 安裝到其他個人 profile；在其他 profile 使用請按上方手動安裝。
Installer 0.6.0 installs the skill and references/scripts into the dedicated bot-screen-lab profile with backup and rollback. Unknown local edits stop the update. Other personal profiles remain separate; use the manual procedure above for them.

Skill 的 platforms 包含 Windows 與 Linux，因為這是 Agent 主機篩選，不是被操作桌面的 OS。實際操作目標仍必須是 Linux。
The platforms metadata covers Windows and Linux Agent hosts; the operated desktop must still be Linux.


## 驗收 / Acceptance

[中英驗收紀錄 / Bilingual acceptance record](https://github.com/brianShih/hermes-dashboard-botscreen/blob/main/evidence/SKILL_ACCEPTANCE.md)：真實工具與桌面流程通過；尚非模型自主 Agent 驗收。
Real tools and desktop flows passed; autonomous model-driven Agent evaluation remains separate.
