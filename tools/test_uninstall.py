#!/usr/bin/env python3
"""Exercise standalone cleanup in temporary trees with mocked system tools."""
import os
import plistlib
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / 'uninstall.sh').read_text()
guard = '[ "$EUID" -eq 0 ] || { echo \'Run with sudo.\' >&2; exit 1; }'
assert source.count(guard) == 1
aux = (ROOT / 'tools/auxkc.sh').read_text().split('update_auxkc() {', 1)[1]
assert 'update_auxkc() {' + aux in source
subprocess.run(['bash', '-n', str(ROOT / 'uninstall.sh')], check=True)

for version, fail in [('11.7.11', False), ('26.7', False), ('26.7', True)]:
    with tempfile.TemporaryDirectory(prefix='xe-cleanup-test-') as tmp:
        root = Path(tmp)
        library = root / 'Library'
        payloads = set()
        for path in (ROOT / 'payloads').rglob('*'):
            if path.is_file():
                rel = path.relative_to(ROOT / 'payloads').parts
                payloads.add(Path(*rel[1:]))
        removed = [root / p for p in payloads]
        retained = [
            library / 'Extensions/Other.kext/Contents/keep',
            library / 'Extensions/WhateverXe.kext/Contents/keep',
            library / 'Extensions/AMFIPass.kext/Contents/keep',
            library / 'GPUBundles/XeCompilerAdapterNotes.bundle/keep',
            root / 'System/Library/Extensions/AppleIntelTGLGraphics.kext/keep',
        ]
        for path in removed + retained:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('fixture')
        feature = library / 'Preferences/FeatureFlags/Domain/CoreMedia.plist'
        feature.parent.mkdir(parents=True)
        feature.write_bytes(plistlib.dumps({'Other': True, 'AllowOnePassMetalScaling': {'Enabled': False, 'Other': 7}}))
        kc = library / 'KernelCollections/AuxiliaryKernelExtensions.kc'
        kc.parent.mkdir(parents=True)
        kc.write_text('previous')
        mock = root / 'system-tool'
        mock.write_text('#!' + sys.executable + '\n' + '''import os, sys
from pathlib import Path
name = Path(sys.argv[0]).name
args = sys.argv[1:]
with open(os.environ['XE_TEST_LOG'], 'a') as log: log.write(name + ' ' + repr(args) + '\\n')
if name == 'sw_vers': print(os.environ['XE_TEST_OS'])
elif name == 'kmutil':
    if os.environ['XE_TEST_FAIL'] == '1': sys.exit(27)
    Path(args[args.index('-A') + 1]).write_text('rebuilt')
elif name == 'pkgutil' and args[0] == '--pkg-info':
    sys.exit(0 if args[1] in ['org.b00t0x.WhateverXe.Common', 'org.b00t0x.WhateverXe.Tahoe'] else 1)
''')
        mock.chmod(0o755)
        body = source.replace(guard, ': # Root guard checked above; test uses a temporary tree.')
        body = body.replace('/System/Library/', '/__SYSTEM__/')
        body = body.replace('/Library/', str(library) + '/')
        body = body.replace('/__SYSTEM__/', str(root / 'System/Library') + '/')
        for tool in ['/usr/bin/sw_vers', '/usr/bin/kmutil', '/usr/sbin/pkgutil']:
            path = root / Path(tool).name
            path.symlink_to(mock)
            body = body.replace(tool, str(path))
        script = root / 'uninstall.sh'
        script.write_text(body)
        log = root / 'commands.log'
        env = dict(os.environ, XE_TEST_LOG=str(log), XE_TEST_OS=version, XE_TEST_FAIL=str(int(fail)))
        result = subprocess.run(['bash', str(script)], env=env, capture_output=True, text=True)
        assert result.returncode == (27 if fail else 0), result.stderr
        assert all(not p.exists() for p in removed)
        assert all(p.read_text() == 'fixture' for p in retained)
        assert plistlib.loads(feature.read_bytes()) == {'Other': True, 'AllowOnePassMetalScaling': {'Other': 7}}
        assert kc.read_text() == ('previous' if fail else 'rebuilt')
        commands = log.read_text()
        assert ('--allow-missing-kdk' in commands) == version.startswith('26.')
        forgotten = [line for line in commands.splitlines() if '--forget' in line]
        expected = [] if fail else [
            "pkgutil ['--forget', 'org.b00t0x.WhateverXe.Common']",
            "pkgutil ['--forget', 'org.b00t0x.WhateverXe.Tahoe']",
        ]
        assert forgotten == expected
        assert not list(kc.parent.glob('.WhateverXe.*'))
print('PASS: distributed payload removal, unrelated files, receipts and AuxKC success/failure')
