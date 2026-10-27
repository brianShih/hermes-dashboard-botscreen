"""Behavior tests for desktop ownership and real subprocess stream lifetime."""
import asyncio
from io import BytesIO
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(sys.argv.pop(1)).resolve()))
from tools.bot_desktop.transport import recorded_docker_command
from hermes_cli.web_display_streams import pipe_stream, close_pipe_relay


class OwnerTests(unittest.TestCase):
    def marker(self):
        return {'backend': 'DockerEnvironment', 'profile': 'alpha', 'container': 'desktop-alpha',
                'dir': '/tmp/hermes-bot-desktop/alpha'}

    def test_wrong_marker_is_rejected_before_docker(self):
        for changes in [{'profile': 'beta'}, {'container': '--privileged'},
                        {'dir': '/tmp/../hermes-bot-desktop/alpha'}, {'dir': '/tmp/hermes-bot-desktop/beta'}]:
            with self.subTest(changes=changes), patch('subprocess.run') as run:
                with self.assertRaises(OSError):
                    recorded_docker_command({**self.marker(), **changes}, 'alpha')
                run.assert_not_called()

    def test_inspected_identity_and_owner_are_required(self):
        for profile in ['alpha', 'beta']:
            inspected = 'true|' + json.dumps('a' * 64) + '|' + json.dumps({'hermes-agent': '1', 'hermes-profile': profile})
            with patch('tools.environments.docker.find_docker', return_value='docker'), patch('subprocess.run', side_effect=[
                    subprocess.CompletedProcess([], 0, inspected, ''), subprocess.CompletedProcess([], 0, b'1000', b'')]):
                if profile == 'beta':
                    with self.assertRaises(OSError): recorded_docker_command(self.marker(), 'alpha')
                else:
                    command = recorded_docker_command(self.marker(), 'alpha')
                    self.assertEqual(command[:6], ['docker', 'exec', '-i', '-u', 'pn', 'a' * 64])
                    self.assertEqual(command[-1], '/tmp/hermes-bot-desktop/alpha/rfb.sock')


class PipeTests(unittest.IsolatedAsyncioTestCase):
    async def test_binary_roundtrip_and_cancelled_read_cleanup(self):
        relay = subprocess.Popen([sys.executable, '-u', '-c',
            'import os;os.write(1,b"ready");\nwhile True:\n d=os.read(0,65536)\n if not d: break\n os.write(1,d)'],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        reader, writer, _ = pipe_stream(relay)
        try:
            self.assertEqual(await asyncio.wait_for(reader.read(64), 5), b'ready')
            payload = bytes(range(256)) * 256
            writer.write(payload)
            drain = asyncio.create_task(writer.drain())
            received = bytearray()
            while len(received) < len(payload):
                received.extend(await asyncio.wait_for(reader.read(65536), 5))
            await drain
            self.assertEqual(received, payload)
            pending = asyncio.create_task(reader.read(64))
            await asyncio.sleep(0.05)
            pending.cancel()
            await asyncio.gather(pending, return_exceptions=True)
        finally:
            await asyncio.wait_for(close_pipe_relay(relay), 5)
            writer.close()
            await writer.wait_closed()
        self.assertIsNotNone(relay.poll())

    async def test_write_buffer_is_bounded(self):
        from hermes_cli.web_display_streams import PipeWriter
        writer = PipeWriter(BytesIO())
        with self.assertRaises(ConnectionError): writer.write(b'x' * (16 * 1024 * 1024 + 1))


if __name__ == '__main__': unittest.main()
