# Environment discovery / 環境資訊

This is a discovery checklist, not a record of the developer's machine. Determine facts in the active deployment; unknown values remain unknown.
此為探查清單，不是開發者電腦的設定；依目前部署確認，未知欄位保持未知。

| Fact / 項目 | What to establish / 確認內容 |
|---|---|
| Target / 目標 | Active Hermes profile and same desktop as the viewer / profile 與觀看桌面一致 |
| Runtime / 執行環境 | Container, VM, or native Linux; host OS separately / 區分容器、VM、原生與主機 OS |
| Tools / 工具 | Available Agent tool schemas and their target routing / 工具參數與實際操作位置 |
| Files / 檔案 | Working directory, writable destination, confirmed shared mount if any / 工作目錄、可寫位置與已確認共用路徑 |
| Desktop / 桌面 | Available apps, browser, resolution, current control owner / 應用、瀏覽器、解析度與控制權 |
| Persistence / 持久性 | Which directories survive container recreation / 重建後仍保留的目錄 |

Do not discover context by reading tokens, passwords, cookies, or unrelated chat records. Do not persist personal usernames, private URLs, container IDs, or host paths in this distributed skill. If the task needs an environment note, keep only necessary non-secret facts in that deployment's private workspace.
不透過權杖、密碼、cookies 或無關對話探查；發佈 skill 不含個人名稱、私有網址、容器 ID 或主機路徑。必要的環境筆記僅存最少非秘密資料於當地私人工作區。
