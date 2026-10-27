#!/usr/bin/env python3
"""Exercise extracted AutoPkg scripts in temporary trees; never install or reboot."""
import json
import os
from pathlib import Path
import plistlib
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET


def check_autopkg(expanded, policy):
    final = expanded / 'AutoRestart.pkg'
    info = ET.parse(final / 'PackageInfo').getroot()
    assert info.attrib['identifier'] == 'org.b00t0x.WhateverXe.AutoRestart'
    assert info.attrib['version'] == policy['package_version']
    payload = info.find('payload')
    assert payload is None or int(payload.attrib['numberOfFiles']) == 0
    assert not any(p.is_file() for p in (final / 'Payload').rglob('*'))
    assert {p.name for p in (final / 'Scripts').iterdir()} == {'preinstall', 'postinstall'}
    for p in (final / 'Scripts').iterdir():
        subprocess.run(['bash', '-n', str(p)], check=True)

    cases = [(s, 'success') for s in policy['systems']]
    cases += [(policy['systems'][-1], failure) for failure in (
        'configured', 'other-volume', 'no-target', 'old-system-patch', 'aux-failed',
        'missing-receipt', 'wrong-version', 'missing-kc', 'sync-failed', 'unsupported-os')]
    for system, failure in cases:
        with tempfile.TemporaryDirectory(prefix='xe-autopkg-test-') as tmp:
            root = Path(tmp)
            library = root / 'Library'
            kc = library / 'KernelCollections/AuxiliaryKernelExtensions.kc'
            kc.parent.mkdir(parents=True)
            kc.write_bytes(b'previous-kc')
            (library / 'Extensions/Other.kext').mkdir(parents=True)
            setup = root / 'AppleSetupDone'
            if failure == 'configured':
                setup.touch()
            system_library = root / 'System/Library'
            if failure == 'old-system-patch':
                (system_library / 'Extensions/AppleIntelTGLCompat.kext').mkdir(parents=True)
            receipts = root / 'receipts.json'
            receipts.write_text('{}')
            log = root / 'calls.jsonl'
            mock = root / 'mock.py'
            mock.write_text('#!' + sys.executable + '\n' + '''import json, os, plistlib, sys
from pathlib import Path
name = Path(sys.argv[0]).name
args = sys.argv[1:]
with open(os.environ['XE_TEST_LOG'], 'a') as f:
    f.write(json.dumps([name, args]) + '\\n')
failure = os.environ['XE_TEST_FAILURE']
if name == 'sw_vers': print(os.environ['XE_TEST_VERSION'])
elif name == 'pkgutil':
    data = json.loads(Path(os.environ['XE_TEST_RECEIPTS']).read_text())
    if args[1] not in data: sys.exit(17)
    sys.stdout.buffer.write(plistlib.dumps({'pkg-version': data[args[1]]}))
elif name == 'kmutil':
    if failure == 'aux-failed': sys.exit(27)
    Path(args[args.index('-A') + 1]).write_bytes(b'new-kc')
elif name == 'sync' and failure == 'sync-failed': sys.exit(28)
''')
            mock.chmod(0o755)
            replacements = {}
            for tool in ('/usr/bin/sw_vers', '/usr/sbin/pkgutil', '/usr/bin/kmutil', '/bin/sync', '/sbin/reboot'):
                link = root / Path(tool).name
                link.symlink_to(mock)
                replacements[tool] = str(link)
            env = dict(os.environ, XE_TEST_LOG=str(log), XE_TEST_RECEIPTS=str(receipts),
                       XE_TEST_FAILURE=failure,
                       XE_TEST_VERSION='99.0' if failure == 'unsupported-os' else system['minimum'])
            target = '/Volumes/Other' if failure == 'other-volume' else '/'

            def execute(component, phase):
                text = (expanded / (component + '.pkg') / 'Scripts' / phase).read_text()
                text = text.replace('/System/Library/', '/__SYSTEM__/')
                text = text.replace('/Library/', str(library) + '/')
                text = text.replace('/__SYSTEM__/', str(system_library) + '/')
                text = text.replace('/var/db/.AppleSetupDone', str(setup))
                for src, dst in replacements.items():
                    text = text.replace(src, dst)
                script = root / (component + '-' + phase)
                script.write_text(text)
                argv = [] if failure == 'no-target' else ['fixture.pkg', '/', target, '/']
                return subprocess.run(['bash', str(script), *argv], env=env, capture_output=True, text=True)

            component = system['payload'].replace(' ', '')
            committed = {}
            result = execute('Common', 'preinstall')
            if result.returncode == 0:
                committed['org.b00t0x.WhateverXe.Common'] = policy['package_version']
                result = execute(component, 'preinstall')
            if result.returncode == 0:
                result = execute(component, 'postinstall')
            if result.returncode == 0:
                committed['org.b00t0x.WhateverXe.' + component] = policy['package_version']
                if failure == 'missing-receipt': committed.pop('org.b00t0x.WhateverXe.' + component)
                if failure == 'wrong-version': committed['org.b00t0x.WhateverXe.Common'] = '0.0.0'
                receipts.write_text(json.dumps(committed))
                if failure == 'missing-kc': kc.unlink()
                result = execute('AutoRestart', 'preinstall')
                if result.returncode == 0:
                    result = execute('AutoRestart', 'postinstall')
            calls = [json.loads(x) for x in log.read_text().splitlines()] if log.exists() else []
            rebooted = [x for x in calls if x[0] == 'reboot']
            if failure == 'success':
                assert result.returncode == 0, (system['name'], result.stderr)
                assert len(rebooted) == 1 and calls[-2:] == [['sync', []], ['reboot', []]]
                assert kc.read_bytes() == b'new-kc'
                queried = [x[1][1] for x in calls if x[0] == 'pkgutil']
                assert queried == ['org.b00t0x.WhateverXe.Common', 'org.b00t0x.WhateverXe.' + component]
                if system['major'] == 26:
                    flag = plistlib.loads((library / 'Preferences/FeatureFlags/Domain/CoreMedia.plist').read_bytes())
                    assert flag['AllowOnePassMetalScaling']['Enabled'] is False
            else:
                assert result.returncode != 0 and not rebooted, (failure, result.stdout, result.stderr, calls)
            if failure in ('configured', 'other-volume', 'no-target', 'old-system-patch', 'aux-failed'):
                assert kc.read_bytes() == b'previous-kc', failure
            assert not list(kc.parent.glob('.WhateverXe.*'))
    print(f'PASS: AutoPkg no payload finalizer; {len(cases)} script cases including failure without reboot')
