"""Bounded async access to Windows subprocess pipes, including selector loops."""
from __future__ import annotations

import asyncio
import subprocess


class PipeReader:
    def __init__(self, pipe):
        self.pipe = pipe

    async def read(self, size: int) -> bytes:
        return await asyncio.to_thread(self.pipe.read1, size)


class PipeWriter:
    def __init__(self, pipe):
        self.pipe = pipe
        self.pending = bytearray()

    def write(self, data: bytes) -> None:
        if len(self.pending) + len(data) > 16 * 1024 * 1024:
            raise ConnectionError("Desktop stream write buffer exceeded")
        self.pending.extend(data)

    async def drain(self) -> None:
        data = bytes(self.pending)
        self.pending.clear()
        await asyncio.to_thread(self._flush, data)

    def _flush(self, data: bytes) -> None:
        self.pipe.write(data)
        self.pipe.flush()

    def close(self) -> None:
        self.pipe.close()

    async def wait_closed(self) -> None:
        return


def pipe_stream(relay: subprocess.Popen):
    return PipeReader(relay.stdout), PipeWriter(relay.stdin), relay


async def close_pipe_relay(relay: subprocess.Popen) -> None:
    # Killing the exec client unblocks pending reads/writes before closing their
    # buffered handles. The desktop inside the container is left running.
    if relay.poll() is None:
        relay.kill()
    await asyncio.to_thread(relay.wait)
    relay.stdout.close()
