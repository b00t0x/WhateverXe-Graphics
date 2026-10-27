#!/usr/bin/env python3
"""Check the built distribution, BOMs and reconstructed payloads offline."""
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from kext_dependencies import check_dependencies

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('package', type=Path)
parser.add_argument('--rcodesign', default='rcodesign')
args = parser.parse_args()
subprocess.run([sys.executable, str(Path(__file__).with_name('test_uninstall.py'))], check=True)
subprocess.run([sys.executable, str(Path(__file__).with_name('test_dependencies.py'))], check=True)
subprocess.run([sys.executable, str(Path(__file__).with_name('verify.py')), '--rcodesign', args.rcodesign], check=True)
manifest = json.loads((args.package.parent / 'manifest.json').read_text())
autopkg = manifest.get('autopkg', False)
assert (args.package.parent / 'SHA256SUMS').read_text() == (
    hashlib.sha256(args.package.read_bytes()).hexdigest() + '  ' + args.package.name + '\n')
cases = {
    '11.7.10': None, '11.7.11': 'Big Sur', '12.7.5': None, '12.7.6': 'Monterey',
    '13.7.7': None, '13.7.8': 'Ventura', '14.8.8': None, '14.8.9': 'Sonoma',
    '15.7.9': None, '15.8': 'Sequoia', '15.8.0': 'Sequoia', '15.8.99': 'Sequoia',
    '15.9': None, '16.0': None, '26.6.99': None, '26.7': 'Tahoe',
    '26.7.1': 'Tahoe', '26.8': 'Tahoe', '26.99.99': 'Tahoe', '27.0': None,
}
with tempfile.TemporaryDirectory(prefix='xe-pkg-test-') as tmp:
    root = Path(tmp) / 'expanded'
    subprocess.run(['pkgutil', '--expand-full', str(args.package.resolve()), str(root)], check=True)
    distribution = ET.parse(root / 'Distribution').getroot()
    assert all(distribution.find(tag) is None for tag in ['readme', 'welcome', 'license', 'conclusion'])
    ranges = [(x.attrib['min'], x.attrib['before']) for x in distribution.findall('./volume-check/allowed-os-versions/os-version')]
    assert ranges == [(s['minimum'], s['before']) for s in manifest['policy']['systems']]
    choices = {x.attrib['title']: x.attrib['selected'] for x in distribution.findall('choice')}
    payload_choices = {name: expr for name, expr in choices.items() if name != 'AutoRestart'}
    order = [x.attrib['choice'] for x in distribution.findall('./choices-outline/line')]
    expected_order = ['Common'] + [s['payload'].replace(' ', '') for s in manifest['policy']['systems']]
    assert order == expected_order + (['AutoRestart'] if autopkg else [])
    # productbuild adds a second pkg-ref per identifier for bundle metadata.
    refs = [x for x in distribution.findall('pkg-ref') if (x.text or '').strip().startswith('#')]
    assert len(refs) == len(order)
    assert all(x.attrib.get('onConclusion') == (None if autopkg else 'RequireRestart')
               for x in refs)
    if autopkg:
        assert args.package.name == 'AutoPkg-Assets.pkg'
        assert choices['AutoRestart'] == 'true'
        from test_autopkg import check_autopkg
        check_autopkg(root, manifest['policy'])
    # Exercise the actual generated expressions with numeric compareVersions semantics.
    js = '''const input = JSON.parse(process.argv[1]);
const system = {version: {}, compareVersions(a, b) {
  a=a.split('.').map(Number); b=b.split('.').map(Number);
  for(let i=0;i<Math.max(a.length,b.length);i++) {
    const d=(a[i]||0)-(b[i]||0); if(d) return Math.sign(d);
  } return 0;
}};
for (const [version, expected] of Object.entries(input.cases)) {
  system.version.ProductVersion=version;
  const actual=Object.entries(input.choices).filter(([id, expr])=>id!=='Common' && eval(expr)).map(([id])=>id);
  if(JSON.stringify(actual)!==JSON.stringify(expected ? [expected] : [])) throw new Error(version);
}
'''
    subprocess.run(['node', '-e', js, json.dumps({'choices': payload_choices, 'cases': cases})], check=True)
    payloads = {}
    for name in payload_choices:
        component = root / (name.replace(' ', '') + '.pkg')
        assert (component / 'Bom').is_file()
        info = ET.parse(component / 'PackageInfo').getroot()
        assert info.attrib['identifier'] == 'org.b00t0x.WhateverXe.' + name.replace(' ', '')
        assert int(info.find('payload').attrib['numberOfFiles']) > 0
        for bundle in info.findall('./bundle-version/bundle'):
            assert bundle.attrib.get('path', '').startswith('Library/')
        files = {str(p.relative_to(component / 'Payload')): p
                 for p in (component / 'Payload').rglob('*') if p.is_file()}
        bom = subprocess.check_output(['lsbom', '-s', '-f', str(component / 'Bom')], text=True)
        bom_files = {p.removeprefix('./') for p in bom.splitlines()}
        assert set(files) == bom_files, (name, set(files) - bom_files, bom_files - set(files))
        payloads[name] = files
        scripts = component / 'Scripts'
        assert {p.name for p in scripts.iterdir()} == ({'preinstall'} if name == 'Common' else {'preinstall', 'postinstall'})
        for script in scripts.iterdir():
            subprocess.run(['bash', '-n', str(script)], check=True)
            assert '/sbin/reboot' not in script.read_text()
        source = Path(__file__).parent
        preinstall = (scripts / 'preinstall').read_text()
        assert preinstall.endswith((source / 'preinstall.sh').read_text())
        if autopkg:
            assert (source / 'autopkg-preinstall.sh').read_text() in preinstall
        else:
            assert 'AutoPkg' not in preinstall
        if name != 'Common':
            assert (scripts / 'postinstall').read_text().endswith(
                (source / 'auxkc.sh').read_text() + '\n' + (source / 'postinstall.sh').read_text())
    total = 0
    provider = 'Library/Extensions/AppleIntelTGLCompat.kext/Contents/MacOS/AppleIntelTGLCompat'
    assert choices['Common'] == 'true'
    assert provider in payloads['Common']
    assert all(provider not in files for name, files in payloads.items() if name != 'Common')
    for build, expected in manifest['systems'].items():
        assert not (payloads['Common'].keys() & payloads[build].keys())
        actual = payloads['Common'] | payloads[build]
        assert actual.keys() == expected.keys()
        plists = [p for rel, p in actual.items() if rel.startswith('Library/Extensions/') and rel.endswith('.kext/Contents/Info.plist')]
        assert check_dependencies(plists, build) > 0
        for rel, p in actual.items():
            data = p.read_bytes()
            assert hashlib.sha256(data).hexdigest() == expected[rel]['sha256'], rel
            assert len(data) == expected[rel]['size']
            assert p.stat().st_mode & 0o777 == expected[rel]['mode'], rel
        total += len(actual)
    subprocess.run(['bash', '-n', str(Path(__file__).resolve().parents[1] / 'uninstall.sh')], check=True)
print(f'PASS: {len(cases)} version boundaries, 7 standard payloads/BOMs, {total} reconstructed files, script syntax; autopkg={autopkg}')
