"""Explicit acceptance harness: real Hermes tools, not a model-driven Agent session.

Run in the selected Hermes Python with HERMES_HOME set to the intended profile.
Writes only synthetic test files in its verified Docker desktop.
"""
import argparse
import json
from pathlib import Path
import subprocess
import uuid
import shlex

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['discover', 'human-gate', 'capture', 'files'])
    parser.add_argument('--probe', type=Path)
    args = parser.parse_args()
    from hermes_constants import get_hermes_home
    home = get_hermes_home()
    assert home.name == 'bot-screen-lab', 'Requires the dedicated profile'
    # Normal Hermes entry points load profile configuration before importing tools.
    from hermes_cli.config import load_config
    load_config()
    if args.mode == 'discover':
        from tools.skills_tool import skill_view
        paths = [None, 'references/environment.md', 'references/linux-tasks.md',
                 'references/workflows.md', 'scripts/environment_probe.py']
        for path in paths:
            result = json.loads(skill_view('bot-screen-linux', file_path=path, preprocess=False))
            assert result.get('success') is True, 'Installed skill is not readable'
        from agent.skill_utils import skill_matches_platform_list
        assert skill_matches_platform_list(['windows', 'linux'])
        print(json.dumps({'skillReadable': True, 'allReferencesReadable': True, 'hostPlatformAccepted': True}))
    elif args.mode in {'human-gate', 'capture'}:
        from tools.computer_use_tool import handle_computer_use
        result = handle_computer_use({'action': 'capture', 'mode': 'vision'}, session_id='bot-screen-skill-acceptance')
        value = json.loads(result) if isinstance(result, str) else result
        if args.mode == 'human-gate':
            assert value.get('code') == 'human_has_control', 'Capture was not refused during human control'
            print(json.dumps({'humanCaptureRefused': True}))
        else:
            ok = bool(value.get('_multimodal'))
            print(json.dumps({'actualComputerUseCapture': ok, 'error': value.get('error')}))
            if not ok: raise SystemExit(2)
    else:
        from tools.bot_desktop import lease
        lease.assert_agent_may_act()
        from tools.bot_desktop.transport import recorded_docker_owner
        marker = json.loads((home / 'bot-desktop/sandbox.json').read_text())
        owner = recorded_docker_owner(marker, 'bot-screen-lab')
        from tools.bot_desktop import runtime
        environment = runtime._sandbox_env(create=True)
        assert environment is not None, 'No terminal environment'
        actual_id = subprocess.run([owner.docker, 'inspect', '--format', '{{.Id}}', environment._container_id],
                                   capture_output=True, text=True, check=True, timeout=15).stdout.strip()
        assert actual_id == owner.container, 'Terminal and viewer target mismatch'
        from tools.terminal_tool import terminal_tool
        def run(code):
            value = json.loads(terminal_tool('python3 -c ' + shlex.quote(code), timeout=20))
            output = value.get('output', value.get('stdout', ''))
            assert value.get('exit_code', 0) == 0 and not value.get('error'), 'Terminal tool failed'
            return json.loads(output)
        probe = args.probe.read_text(encoding='utf-8')
        capabilities = run(probe)
        token = uuid.uuid4().hex
        code = '''import pathlib,tempfile,json
p=pathlib.Path(tempfile.mkdtemp(prefix='bot-screen-skill-'))
f=p/'before.txt';text='Synthetic skill check: '+TOKEN+' — 中文測試'
f.write_text(text,encoding='utf-8');assert f.read_text(encoding='utf-8')==text
g=p/'after.txt';f.rename(g);assert not f.exists() and g.read_text(encoding='utf-8')==text
print(json.dumps({'utf8WriteReadRename':True,'testDirectory':str(p)}))
'''.replace('TOKEN', repr(token))
        result = run(code)
        print(json.dumps({'verifiedDockerOwner': True, 'terminalMatchesViewer': True, 'environmentProbe': capabilities, **result,
                          'executionPath': 'actual Hermes terminal tool'}))

if __name__ == '__main__':
    main()
