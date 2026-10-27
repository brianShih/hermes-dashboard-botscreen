#!/usr/bin/env bash
set -euo pipefail
package_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
installer_python=""
installer_launcher="$(command -v hermes || true)"
explicit_root=""
explicit_launcher=""
arguments=("$@")
for ((index=0; index<${#arguments[@]}; index++)); do
  if [[ "${arguments[$index]}" == --python && $((index+1)) -lt ${#arguments[@]} ]]; then installer_python="${arguments[$((index+1))]}"; fi
  if [[ "${arguments[$index]}" == --launcher && $((index+1)) -lt ${#arguments[@]} ]]; then installer_launcher="${arguments[$((index+1))]}"; explicit_launcher=1; fi
  if [[ "${arguments[$index]}" == --hermes-root && $((index+1)) -lt ${#arguments[@]} ]]; then explicit_root="${arguments[$((index+1))]}"; fi
done
if [[ -n "$explicit_root" && -z "$explicit_launcher" ]]; then
  installer_launcher=""
  for candidate in "$explicit_root/.hermes/bin/hermes" "$explicit_root/.venv/bin/hermes"; do
    if [[ -x "$candidate" ]]; then installer_launcher="$candidate"; break; fi
  done
fi
if [[ -z "$installer_python" ]] && command -v python3 >/dev/null 2>&1; then installer_python="$(command -v python3)"; fi
if [[ -z "$installer_launcher" && -z "$explicit_root" ]]; then
  for candidate in "${HERMES_HOME:-$HOME/.hermes}/hermes-agent/.hermes/bin/hermes" "$HOME/.hermes/.hermes/bin/hermes" "$HOME/.hermes/hermes-agent/.venv/bin/hermes"; do
    if [[ -x "$candidate" ]]; then installer_launcher="$candidate"; break; fi
  done
fi
if [[ -z "$installer_python" && -n "$installer_launcher" ]]; then
  # Minimal systems may have only Hermes' bundled Python. Reject JSON escapes
  # here rather than interpreting a shell-built command or guessing a path.
  runtime_json="$("$installer_launcher" --print-runtime-command)"
  installer_python="$(printf '%s\n' "$runtime_json" | sed -n 's/^\["\([^"\\]*\)".*$/\1/p')"
fi
if [[ -z "$installer_python" || ! -x "$installer_python" ]]; then
  printf '%s\n' 'Hermes Python was not found. Install Hermes first or pass --hermes-root and --python. See ONE_CLICK.md.' >&2
  exit 1
fi
if [[ -n "$installer_launcher" && " ${arguments[*]} " != *' --launcher '* ]]; then arguments+=(--launcher "$installer_launcher"); fi
exec "$installer_python" "$package_dir/scripts/install-dashboard.py" "${arguments[@]}"
