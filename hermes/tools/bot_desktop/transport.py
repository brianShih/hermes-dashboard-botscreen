"""Reconnect to the exact recorded Docker desktop without the terminal registry."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import PurePosixPath
import re
import shlex
import subprocess


@dataclass(frozen=True)
class DockerDesktop:
    docker: str
    container: str
    directory: str
    user: str | None

    def command(self, argv: list[str], *, interactive: bool = False) -> list[str]:
        user = ["-u", self.user] if self.user else []
        return [self.docker, "exec", *(["-i"] if interactive else []), *user, self.container, *argv]

    def published(self) -> dict[str, str]:
        directory = shlex.quote(self.directory)
        command = (f"kill -0 $(cat {directory}/launcher.pid 2>/dev/null) 2>/dev/null "
                   f"&& test -S {directory}/rfb.sock && cat {directory}/env")
        result = subprocess.run(self.command(["bash", "-c", command]),
                                capture_output=True, text=True, timeout=15, check=False)
        if result.returncode:
            return {}
        return dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)


def recorded_docker_owner(marker: dict, profile: str) -> DockerDesktop:
    from tools.environments.docker import find_docker, _sanitize_label_value

    container = str(marker.get("container") or "")
    directory = str(marker.get("dir") or "")
    path = PurePosixPath(directory)
    if (marker.get("backend") != "DockerEnvironment" or marker.get("profile") != profile
            or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", container)
            or not path.is_absolute() or ".." in path.parts
            or path.parts[-2:] != ("hermes-bot-desktop", profile)):
        raise OSError("Invalid recorded desktop owner")
    docker = find_docker()
    if not docker:
        raise OSError("Docker executable is unavailable")
    result = subprocess.run(
        [docker, "inspect", "--format", '{{json .State.Running}}|{{json .Id}}|{{json .Config.Labels}}', container],
        capture_output=True, text=True, timeout=15, check=False)
    if result.returncode:
        raise OSError("The recorded desktop container is unavailable")
    try:
        running, identity, labels = (json.loads(item) for item in result.stdout.strip().split("|", 2))
    except (ValueError, TypeError) as exc:
        raise OSError("Invalid desktop container inspection") from exc
    if (running is not True or not re.fullmatch(r"[a-f0-9]{64}", str(identity))
            or not isinstance(labels, dict) or labels.get("hermes-agent") != "1"
            or labels.get("hermes-profile") != _sanitize_label_value(profile)):
        raise OSError("Desktop container does not belong to this profile")
    probe = subprocess.run([docker, "exec", identity, "id", "-u", "pn"],
                           capture_output=True, timeout=10, check=False)
    return DockerDesktop(docker, identity, str(path), "pn" if probe.returncode == 0 else None)


def recorded_docker_command(marker: dict, profile: str) -> list[str]:
    from tools.bot_desktop.sandbox_host import _RELAY
    owner = recorded_docker_owner(marker, profile)
    return owner.command(["python3", "-c", _RELAY, owner.directory + "/rfb.sock"], interactive=True)


def open_recorded_docker(marker: dict, profile: str) -> subprocess.Popen:
    return subprocess.Popen(recorded_docker_command(marker, profile), stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, close_fds=True)
