# One-click installer 0.5.0 acceptance

Status: DONE for the recorded Windows/Docker and Linux/native environments.

The actual release ZIP was extracted and used as the installation source, rather than invoking only the maintenance checkout. Targets were disposable Hermes source copies with the original, unpatched runtime functions and new data homes. The daily 9119 installation was inspected read-only; it was not used as the installation test target.

| Gate | Windows PowerShell entry + Docker | Linux shell entry + native desktop |
|---|---|---|
| Check-only leaves target config/core/profile unchanged | PASS | PASS |
| Guarded backend patches and frontend installed | PASS | PASS |
| New Dashboard listener serves the bundled assets | PASS | PASS |
| Real desktop starts and completes bidirectional RFB handshake | PASS | PASS |
| Existing settings, comments and dummy root secret preserved | PASS | PASS |
| New profile receives no copied root `.env` | PASS | PASS |
| Reinstall makes no file changes or new backup | PASS | PASS |
| Rollback restores original source/config bytes | PASS | PASS |

Windows additionally passed browser verification of profile discovery, a real canvas from the newly installed plugin, and Traditional/Simplified Chinese/English switching. An exported dummy provider key was not forwarded to the desktop container. The installer uses Hermes' existing profile-child environment builder for the desktop smoke test.

Windows unit checks: 21 cases, 19 passed and 2 symlink cases skipped because the host did not permit test symlink creation. All 14 new installer cases passed on Linux Python 3.13.5, including symlink refusal and venv-interpreter path preservation. Coverage includes failed-write rollback, corrupt backups, post-install user edits, unfamiliar Hermes functions, foreign Dashboard owners, and refusing false readiness for a listener belonging to another home. A deliberately corrupted extracted bundle was rejected before installation.

Machine-readable evidence:

- `one-click-release.json`: final archive hash, size and acceptance matrix.
- `installer-win32-release.json`, `installer-linux-release.json`: final extracted-release install/reinstall/rollback results.
- `installer-browser.json`, `one-click-installed-windows.png`: browser evidence for the fresh Windows installation.

The Linux test image initially had an incomplete Hermes dependency environment. The verified Linux runtime dependencies from the existing integration environment were copied into the separate test container before acceptance; no raw pip install or dependency change was made to the user's daily Hermes. Test desktop containers were stopped after acceptance; data was retained for inspection.

This proves current-host isolated acceptance, not a clean Windows VM, another physical computer, every Linux distribution, a Linux-host Docker daemon, macOS, or downloading an uncached desktop image. The installer requires an existing functional Hermes runtime and refuses incompatible function shapes. Docker/OS provisioning and signing are not included. See `ONE_CLICK.md` for prerequisites, deferred restart outcomes and rollback instructions.


## Bilingual documentation refresh / 中英文件更新

English guides and language links were added. Archive hashes and English-guide links passed; non-Markdown runtime files match the previously accepted bundle. Functional desktop acceptance was not rerun for this documentation-only refresh.
安裝包新增英文指南與語言切換；雜湊及英文指南連結檢查通過，程式內容與前次驗收包一致，本次未重跑真實桌面驗收。
