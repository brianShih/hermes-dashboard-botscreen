# 9119 Windows runtime repair

Status: DONE for the tested Windows + Docker path. The former BLOCKED diagnosis is superseded by the final live acceptance.

The original Windows start failed because `_flocked` imported Unix-only `fcntl`. After startup was fixed, reconnecting depended on process-local terminal registry state and ordinary subprocess pipes failed on Windows event loops.

Retained repairs:

- Real Windows byte-range locks for starts and lease transitions; POSIX retains flock.
- Recorded Docker owner adapter verifies exact container identity, running state, profile label and desktop directory before opening the stream. No fallback to another profile or a local terminal.
- Windows pipe adapter supports the Dashboard Selector loop, limits pending writes and terminates only its relay client on disconnect. Linux keeps its prior asyncio pipe path.
- Starting an already-running recorded desktop reuses that desktop instead of allowing the terminal planner to allocate a replacement container.

The installed files were backed up. Configuration and credentials were not edited. The old elevated Dashboard process initially prevented replacement; after it was stopped, the installed Dashboard launcher started a fresh backend and final acceptance ran against 9119.

Final evidence:

- `windows-9119.json`: start reuses the same container, actual 1440x900 framebuffer, real input after takeover, input blocked while watching and after handback, three abnormal-disconnect/reconnect cycles retaining human control, no browser runtime errors.
- `windows-9125.json`: initial Windows temporary-backend acceptance; 9119 is the final deployment result.
- `acceptance.json`: Linux 9124 full regression passed, including one-use tickets and unauthenticated rejection.
- Windows and Linux: cross-process start lock, four pipe/owner behavior tests, and exact 100-transition lease concurrency check passed.
- Portable Windows patches were checked and applied against saved original files, including CRLF input using `--ignore-space-change`.

Only fixture text was typed into the task-owned test window. Test windows auto-expire. Original containers were preserved; no unrelated container or user browser was removed. The temporary Windows 9125 listener is stopped after verification.

Limits: macOS hardware, Docker on a native Linux gateway, explicit shared-container keys, SSH/Singularity reconnect, long-duration load and clean-machine install are not claimed as tested. See `CROSS_PLATFORM.md`.
