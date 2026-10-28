#!/usr/bin/env python3
"""Exercise extracted boot-install scripts without Distribution selection or receipts."""
import json
import os
from pathlib import Path
import plistlib
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET


def check_autopkg(expanded, policy, boundaries):
    system = policy['systems'][0]
    component = system['payload'].replace(' ', '')
    assert sorted(p.name for p in expanded.glob('*.pkg')) == sorted(['Common.pkg', component + '.pkg'])
    for name in ('Common', component):
        info = ET.parse(expanded / (name + '.pkg') / 'PackageInfo').getroot()
        assert info.attrib['version'] == policy['package_version']
        assert info.attrib['postinstall-action'] == ('none' if name == 'Common' else 'restart')
        for script in (expanded / (name + '.pkg') / 'Scripts').iterdir():
            body = script.read_text()
            assert all(x not in body for x in ('/sbin/reboot', '/usr/sbin/pkgutil', '/bin/launchctl'))
            assert '@MINIMUM@' not in body and '@BEFORE@' not in body

    cases = [(version, 'success' if expected == system['name'] else 'wrong-os')
             for version, expected in boundaries.items()]
    cases += [(system['minimum'], failure) for failure in (
        'configured', 'other-volume', 'no-target', 'old-system-patch', 'aux-failed', 'missing-kc')]
    for version, failure in cases:
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
            log = root / 'calls.jsonl'
            mock = root / 'mock.py'
            mock.write_text('#!' + sys.executable + '\n' + '''import json, os, sys
from pathlib import Path
name = Path(sys.argv[0]).name
args = sys.argv[1:]
with open(os.environ['XE_TEST_LOG'], 'a') as f:
    f.write(json.dumps([name, args]) + '\\n')
failure = os.environ['XE_TEST_FAILURE']
if name == 'sw_vers': print(os.environ['XE_TEST_VERSION'])
elif name == 'kmutil':
    if failure == 'aux-failed': sys.exit(27)
    if failure != 'missing-kc': Path(args[args.index('-A') + 1]).write_bytes(b'new-kc')
else: sys.exit(99)
''')
            mock.chmod(0o755)
            replacements = {}
            for tool in ('/usr/bin/sw_vers', '/usr/bin/kmutil'):
                link = root / Path(tool).name
                link.symlink_to(mock)
                replacements[tool] = str(link)
            env = dict(os.environ, XE_TEST_LOG=str(log), XE_TEST_FAILURE=failure, XE_TEST_VERSION=version)
            target = '/Volumes/Other' if failure == 'other-volume' else '/'

            def execute(name, phase):
                body = (expanded / (name + '.pkg') / 'Scripts' / phase).read_text()
                body = body.replace('/System/Library/', '/__SYSTEM__/')
                body = body.replace('/Library/', str(library) + '/')
                body = body.replace('/__SYSTEM__/', str(system_library) + '/')
                body = body.replace('/var/db/.AppleSetupDone', str(setup))
                for src, dst in replacements.items():
                    body = body.replace(src, dst)
                script = root / (name + '-' + phase)
                script.write_text(body)
                argv = [] if failure == 'no-target' else ['fixture.pkg', '/', target, '/']
                return subprocess.run(['bash', str(script), *argv], env=env, capture_output=True, text=True)

            # Boot-install schedules every component and commits receipts only
            # after postinstall. No selection expression or receipt mock is used.
            results = [execute(name, 'preinstall') for name in ('Common', component)]
            if all(r.returncode == 0 for r in results):
                results.append(execute(component, 'postinstall'))
            calls = [json.loads(x) for x in log.read_text().splitlines()] if log.exists() else []
            kmutil = [x for x in calls if x[0] == 'kmutil']
            if failure == 'success':
                assert all(r.returncode == 0 for r in results), (version, results[-1].stderr)
                assert len(kmutil) == 1 and kc.read_bytes() == b'new-kc'
                if system['major'] == 26:
                    flag = plistlib.loads((library / 'Preferences/FeatureFlags/Domain/CoreMedia.plist').read_bytes())
                    assert flag['AllowOnePassMetalScaling']['Enabled'] is False
            else:
                assert any(r.returncode != 0 for r in results), (failure, version)
                assert kc.read_bytes() == b'previous-kc', failure
                if failure not in ('aux-failed', 'missing-kc'):
                    assert len(results) == 2 and all(r.returncode != 0 for r in results)
                    assert not kmutil, failure
            assert not list(kc.parent.glob('.WhateverXe.*'))
    print(f'PASS: {system["name"]} AutoPkg; {len(cases)} script cases without receipts; native restart metadata')
