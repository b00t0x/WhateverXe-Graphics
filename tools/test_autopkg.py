#!/usr/bin/env python3
"""Run the universal AutoPkg scripts with real resource copies in temporary roots."""
import hashlib
import json
import os
from pathlib import Path
import plistlib
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from kext_dependencies import check_dependencies
from released_contracts import check_released_clients
from servicing_policy import check_files as check_servicing_files


def files_at(root):
    return {p.relative_to(root).as_posix(): p for p in root.rglob('*') if p.is_file()}


def check_files(actual, expected):
    assert actual.keys() == expected.keys(), (actual.keys() - expected.keys(), expected.keys() - actual.keys())
    for rel, path in actual.items():
        data = path.read_bytes()
        assert hashlib.sha256(data).hexdigest() == expected[rel]['sha256'], rel
        assert len(data) == expected[rel]['size'], rel
        assert path.stat().st_mode & 0o777 == expected[rel]['mode'], rel


def check_autopkg(expanded, manifest, boundaries):
    policy = manifest['policy']
    assert [p.name for p in expanded.glob('*.pkg')] == ['AutoGraphics.pkg']
    component = expanded / 'AutoGraphics.pkg'
    info = ET.parse(component / 'PackageInfo').getroot()
    assert info.attrib['identifier'] == 'org.b00t0x.WhateverXe.AutoGraphics'
    assert info.attrib['version'] == policy['package_version']
    assert info.attrib['postinstall-action'] == 'restart'
    assert not (component / 'Payload').exists()
    distribution = ET.parse(expanded / 'Distribution').getroot()
    assert [c.attrib['id'] for c in distribution.findall('choice')] == ['AutoGraphics']
    refs = [r for r in distribution.findall('pkg-ref') if (r.text or '').strip().startswith('#')]
    assert len(refs) == 1 and refs[0].attrib['onConclusion'] == 'RequireRestart'
    scripts = component / 'Scripts'
    assert {p.name for p in scripts.iterdir()} == {'preinstall', 'postinstall', 'Assets'}
    for phase in ('preinstall', 'postinstall'):
        body = (scripts / phase).read_text()
        assert all(x not in body for x in ('/sbin/reboot', '/usr/sbin/pkgutil', '/bin/launchctl', '@OS_RANGES@', '@BUNDLE_PATHS@'))
        subprocess.run(['bash', '-n', str(scripts / phase)], check=True)
    assets = scripts / 'Assets'
    assert {p.name for p in assets.iterdir()} == {'Common'} | {s['payload'] for s in policy['systems']}
    common = files_at(assets / 'Common')
    for system in policy['systems']:
        name = system['payload']
        selected = files_at(assets / name)
        assert not common.keys() & selected.keys()
        actual = common | selected
        check_servicing_files(actual, name)
        check_files(actual, manifest['systems'][name])
        plists = [p for r, p in actual.items() if r.startswith('Library/Extensions/') and r.endswith('.kext/Contents/Info.plist')]
        assert check_dependencies(plists, name, policy['device_ids']) > 0
        check_released_clients(plists, name)

    cases = [(v, name, 'success' if name else 'unsupported') for v, name in boundaries.items()]
    cases += [('15.8.1', 'Sequoia', failure) for failure in (
        'configured', 'existing-payload', 'other-volume', 'no-target',
        'old-system-patch', 'aux-failed', 'missing-kc', 'copy-failed', 'missing-resource')]
    for version, selected, failure in cases:
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
            if failure == 'existing-payload':
                p = library / 'GPUBundles/XeMetalCompiler.bundle'
                p.mkdir(parents=True)
                (p / 'previous').write_bytes(b'preserve')
            system_library = root / 'System/Library'
            if failure == 'old-system-patch':
                (system_library / 'Extensions/AppleIntelTGLCompat.kext').mkdir(parents=True)
            if failure == 'missing-resource':
                (root / 'Assets').mkdir()
                (root / 'Assets/Common').symlink_to(assets / 'Common')
            else:
                (root / 'Assets').symlink_to(assets)
            log = root / 'calls.jsonl'
            mock = root / 'mock.py'
            mock.write_text('#!' + sys.executable + '\n' + '''import json, os, subprocess, sys
from pathlib import Path
name = Path(sys.argv[0]).name
args = sys.argv[1:]
with open(os.environ['XE_TEST_LOG'], 'a') as f: f.write(json.dumps([name, args]) + '\\n')
failure = os.environ['XE_TEST_FAILURE']
if name == 'sw_vers': print(os.environ['XE_TEST_VERSION'])
elif name == 'chown': pass
elif name == 'ditto':
    if failure == 'copy-failed': sys.exit(28)
    sys.exit(subprocess.call(['/usr/bin/ditto', *args]))
elif name == 'kmutil':
    if failure == 'aux-failed': sys.exit(27)
    if failure != 'missing-kc': Path(args[args.index('-A') + 1]).write_bytes(b'new-kc')
else: sys.exit(99)
''')
            mock.chmod(0o755)
            replacements = {}
            for tool in ('/usr/bin/sw_vers', '/usr/sbin/chown', '/usr/bin/ditto', '/usr/bin/kmutil'):
                link = root / Path(tool).name
                link.symlink_to(mock)
                replacements[tool] = str(link)
            env = dict(os.environ, XE_TEST_LOG=str(log), XE_TEST_FAILURE=failure, XE_TEST_VERSION=version)
            target = '/Volumes/Other' if failure == 'other-volume' else '/'

            def execute(phase):
                body = (scripts / phase).read_text()
                body = body.replace('/System/Library/', '/__SYSTEM__/')
                body = body.replace('/Library/', str(library) + '/')
                body = body.replace('/__SYSTEM__/', str(system_library) + '/')
                body = body.replace('"/$path"', '"' + str(root) + '/$path"')
                body = body.replace('/var/db/.AppleSetupDone', str(setup))
                for src, dst in replacements.items():
                    body = body.replace(src, dst)
                script = root / phase
                script.write_text(body)
                argv = [] if failure == 'no-target' else ['fixture.pkg', '/', target, '/']
                return subprocess.run(['bash', str(script), *argv], env=env, capture_output=True, text=True)

            before = {r: p.read_bytes() for r, p in files_at(library).items()}
            results = [execute('preinstall')]
            # Also validate postinstall's own guards, even when preinstall fails.
            results.append(execute('postinstall'))
            calls = [json.loads(x) for x in log.read_text().splitlines()] if log.exists() else []
            kmutil = [x for x in calls if x[0] == 'kmutil']
            copied = [x for x in calls if x[0] == 'ditto']
            if failure == 'success':
                assert all(r.returncode == 0 for r in results), (version, results[-1].stderr)
                assert len(kmutil) == 1 and kc.read_bytes() == b'new-kc'
                actual = {r: p for r, p in files_at(root).items() if r.startswith(('Library/Extensions/', 'Library/GPUBundles/'))}
                check_files(actual, manifest['systems'][selected])
                check_servicing_files(actual, selected)
                assert len([x for x in calls if x[0] == 'chown']) == len(copied) > 0
                assert all(x[1][:2] == ['-R', 'root:wheel'] for x in calls if x[0] == 'chown')
                assert all('/Common/' in x[1][-2] or '/' + selected + '/' in x[1][-2] for x in copied)
                if selected == 'Tahoe':
                    flag = plistlib.loads((library / 'Preferences/FeatureFlags/Domain/CoreMedia.plist').read_bytes())
                    assert flag['AllowOnePassMetalScaling']['Enabled'] is False
                else:
                    assert not (library / 'Preferences/FeatureFlags/Domain/CoreMedia.plist').exists()
            else:
                assert results[-1].returncode != 0, (failure, version, results[-1].stderr)
                assert kc.read_bytes() == b'previous-kc', failure
                if failure not in ('aux-failed', 'missing-kc', 'copy-failed', 'missing-resource'):
                    assert results[0].returncode != 0 and not copied and not kmutil, failure
                    assert {r: p.read_bytes() for r, p in files_at(library).items()} == before
                if failure == 'missing-resource':
                    assert not copied and not kmutil
                if failure == 'copy-failed':
                    assert not kmutil
            assert not list(kc.parent.glob('.WhateverXe.*'))
    print(f'PASS: 6 OS resource sets; {len(cases)} universal AutoPkg cases with real file copies, no receipt mocks')
