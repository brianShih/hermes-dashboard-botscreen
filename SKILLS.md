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

## 狀態 / Status

本次建立可攜 skill 與文件，尚未自動安裝到每日使用的 profile，也尚未納入 0.5.0 一鍵安裝 ZIP。格式與文件連結檢查不代表真實 Agent 已完成桌面驗收。
The portable skill and documentation are provided in the repository. They have not been automatically installed into a daily profile or added to the 0.5.0 installer ZIP. Format and link checks are separate from real Agent desktop acceptance.
