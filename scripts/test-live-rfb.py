"""Verify the existing isolated desktop's real RFB handshake from a fresh Windows process."""
import asyncio
import json
import os
from pathlib import Path

from hermes_constants import get_hermes_home
from hermes_cli.web_routers.display import _open_rfb


async def main():
    reader, writer, relay = await _open_rfb(get_hermes_home())
    try:
        version = await asyncio.wait_for(reader.read(12), 15)
        assert version == b'RFB 003.008\n', version
        writer.write(version)
        await asyncio.wait_for(writer.drain(), 10)
        security = await asyncio.wait_for(reader.read(2), 10)
        assert security == b'\x01\x01', security
        print(json.dumps({'passed': True, 'freshProcessReattached': True,
                          'realRfbVersion': version.decode().strip(),
                          'bidirectionalHandshake': True,
                          'loop': type(asyncio.get_running_loop()).__name__}))
    finally:
        relay.kill()
        if os.name == 'nt':
            await asyncio.to_thread(relay.wait)
            relay.stdout.close()
        else:
            await relay.wait()
        writer.close()
        await writer.wait_closed()


with asyncio.Runner(loop_factory=asyncio.SelectorEventLoop if os.name == 'nt' else None) as runner:
    runner.run(main())
