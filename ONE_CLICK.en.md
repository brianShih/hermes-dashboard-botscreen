# Bot Screen one-click installation (0.6.0)

[繁體中文](ONE_CLICK.md) | **English**

Requires an existing compatible Hermes installation. This bundle installs Bot Screen, its backend fixes, and a dedicated profile; it does not install Hermes itself.

## Install

1. Start Docker Desktop in Linux-container mode on Windows, or Docker Engine on Linux. Native Linux mode requires its desktop dependencies already installed.
2. Fully extract `bot-screen-hermes-one-click-0.6.0.zip`.
3. Windows: double-click `Install.cmd`. Linux: run `bash install.sh`.

Hermes Python is reused; Node.js, npm, and Git are unnecessary. Missing desktop images are downloaded from `nousresearch/hermes-sandbox:desktop`. The installer does not install Docker, run sudo, or reboot. Install missing prerequisites and rerun.

Default URL: `http://127.0.0.1:9119/bot-screen`. The more menu offers Traditional Chinese, Simplified Chinese, English, and follow-Hermes language choices.

## Changes and restart

The installer checks supported display APIs, SDK features, and recognized Python functions before changing files. It backs up affected files, patches recognized functions, and adds two support modules. Unknown or independently modified functions are rejected.

It creates or reuses `profiles/bot-screen-lab`. New profiles receive an empty `.env`; default-profile credentials and chat history are not copied. Existing settings, other plugins, and YAML comments are preserved. A real bidirectional RFB handshake checks desktop readiness.

New Dashboard processes bind to loopback. Existing processes restart automatically only when ownership and inactivity can be verified. Administrator-owned processes or services managed by systemd, Docker, or another supervisor may require their owner to restart them. Refreshing the page does not reload Python modules. Messaging Gateway is separate.

`installed-needs-attention` means files may be installed but readiness is incomplete. Inspect `dashboard.reason` or `desktop.error`.

## Custom paths

`--hermes-root` contains `hermes_cli/` and `tools/`; `--hermes-home` contains `config.yaml` and `profiles/`.

```powershell
.\Install.ps1 --hermes-root "D:\Apps\hermes-agent" --hermes-home "D:\HermesData"
```

```bash
bash install.sh --hermes-root /opt/hermes-agent --hermes-home "$HOME/.hermes" --python /opt/hermes-agent/.venv/bin/python
```

| Option | Purpose |
|---|---|
| `--check-only` | Check compatibility without writing targets, downloading images, or starting desktops |
| `--backend docker` | Use Docker for the dedicated profile |
| `--backend native` | Use a prepared Linux desktop; profile isolation is not container isolation |
| `--restart never` | Leave Dashboard startup/restart to its owner |
| `--port 9128` | Override default port 9119 |
| `--no-open` | Do not open the browser |
| `--skip-smoke` | Skip real-desktop validation; does not establish full readiness |

New profiles default to Docker. Existing supported native profiles can retain native mode. SSH, Singularity, and explicit shared-container keys are unsupported. Unsupported profiles are rejected without silently switching to a local desktop.

## Rollback and results

Backups: `profiles/bot-screen-lab/plugin-backups/one-click/<timestamp>/` under Hermes home. They may contain private existing settings; keep them private.

Windows: `.\Install.ps1 --rollback latest`. Linux: `bash install.sh --rollback latest`. Pass the same custom root/home options. Rollback refuses to overwrite later edits and preserves desktop data, containers, and chat history. Restart Dashboard afterward. Write failures restore files already written by the transaction.

Results: `runtime/bot-screen-installer/result.json` under Hermes home. Exit codes: `0` ready/check/rollback succeeded; `2` installed with attention required; `1` stopped or failed.

## Validation scope

Install/reinstall/rollback passed in fresh directories on the current Windows/Docker host and inside a Linux container with a native desktop. Clean VMs, other physical machines, all Linux distributions, Linux-host Docker daemons, and macOS are not certified. The image-download branch was not exercised because the image was cached.

The archive excludes user profiles, credentials, backups, test reports, Docker images, and node_modules. `CONTENTS.json` checks integrity; it is not a digital signature.


## Agent skill / Agent 操作技能

Installer 0.6.0 includes bot-screen-linux 1.1.0 in the dedicated profile, with guarded updates and rollback. See [SKILLS.md](SKILLS.md).
安裝器包含 Linux 操作 skill 1.1.0，安裝至專用 profile，提供更新保護與回復；詳見 SKILLS.md。
