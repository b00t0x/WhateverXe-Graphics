#!/usr/bin/env python3
"""Build a standard distribution pkg with common and OS-specific payloads."""
import argparse
import hashlib
import json
import plistlib
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from kext_dependencies import check_payload_sets

HERE = Path(__file__).resolve().parent
PREFIX = 'org.b00t0x.WhateverXe'
ROOT = HERE.parent


def run(*args):
    subprocess.run(args, check=True)


def shell_script(path, body):
    path.write_text('#!/bin/bash\nset -euo pipefail\nexport PATH=/usr/bin:/bin:/usr/sbin:/sbin\n' + body)
    path.chmod(0o755)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--tag', default='')
    parser.add_argument('--autopkg', action='store_true',
                        help='build AutoPkg-Assets.pkg for fresh macOS installs before Setup Assistant')
    args = parser.parse_args()
    policy = json.loads((HERE / 'policy.json').read_text())
    assert not args.tag or args.tag == 'v' + policy['package_version'], 'tag/version mismatch'
    # Reject incompatible payloads before creating any package or output directory.
    check_payload_sets(ROOT / 'payloads', policy['systems'])
    components, sources = {}, {}
    for name in ['Common'] + [s['payload'] for s in policy['systems']]:
        directory = ROOT / 'payloads' / name
        files = {}
        for path in sorted(directory.rglob('*')):
            assert not path.is_symlink(), 'unexpected payload symlink'
            if not path.is_file():
                continue
            rel = path.relative_to(directory).as_posix()
            assert rel.startswith(('Library/Extensions/', 'Library/GPUBundles/'))
            data = path.read_bytes()
            sha = hashlib.sha256(data).hexdigest()
            mode = 0o755 if path.stat().st_mode & 0o111 else 0o644
            files[rel] = {'sha256': sha, 'size': len(data), 'mode': mode}
            sources[sha] = path
        assert files, name
        components[name] = files
    manifests = {}
    for system in policy['systems']:
        name = system['payload']
        assert not (components['Common'].keys() & components[name].keys()), name
        manifests[name] = components['Common'] | components[name]
    output = (args.output or (ROOT / 'dist' / 'autopkg' if args.autopkg else ROOT / 'dist')).resolve()
    output.mkdir(parents=True, exist_ok=True)
    version = policy['package_version']
    auto_guard = (HERE / 'autopkg-preinstall.sh').read_text() if args.autopkg else ''
    with tempfile.TemporaryDirectory(prefix='xe-pkg-') as tmp:
        work = Path(tmp)
        for name, files in components.items():
            component_id = name.replace(' ', '')
            root = work / name / 'root'
            scripts = work / name / 'scripts'
            scripts.mkdir(parents=True)
            for rel, info in files.items():
                target = root / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(Path(sources[info['sha256']]).read_bytes())
                target.chmod(info['mode'])
            shell_script(scripts / 'preinstall', auto_guard + (HERE / 'preinstall.sh').read_text())
            if name != 'Common':
                shell_script(scripts / 'postinstall',
                             (HERE / 'auxkc.sh').read_text() + '\n' +
                             (HERE / 'postinstall.sh').read_text())
            component_plist = work / name / 'components.plist'
            run('pkgbuild', '--analyze', '--root', str(root), str(component_plist))
            bundles = plistlib.loads(component_plist.read_bytes())

            def configure(items):
                for item in items:
                    item.update(BundleIsRelocatable=False, BundleIsVersionChecked=False,
                                BundleOverwriteAction='upgrade')
                    configure(item.get('ChildBundles', []))
            configure(bundles)
            component_plist.write_bytes(plistlib.dumps(bundles))
            run('pkgbuild', '--root', str(root), '--install-location', '/',
                '--component-plist', str(component_plist), '--ownership', 'recommended',
                '--identifier', PREFIX + '.' + component_id, '--version', version,
                '--scripts', str(scripts), str(work / (component_id + '.pkg')))
        if args.autopkg:
            # The payload components keep their normal receipts. Only this final,
            # payload-free component can interrupt its own receipt with a reboot.
            scripts = work / 'AutoRestart' / 'scripts'
            scripts.mkdir(parents=True)
            shell_script(scripts / 'preinstall', auto_guard)
            cases = '\n'.join(f"    {s['major']}) component={s['payload'].replace(' ', '')} ;;"
                              for s in policy['systems'])
            reboot = (HERE / 'autopkg-reboot.sh').read_text().replace('@OS_RECEIPTS@', cases)
            shell_script(scripts / 'postinstall', auto_guard +
                         f"expected_version='{version}'\n" + reboot)
            run('pkgbuild', '--nopayload', '--identifier', PREFIX + '.AutoRestart',
                '--version', version, '--scripts', str(scripts), str(work / 'AutoRestart.pkg'))
        dist = ET.Element('installer-gui-script', minSpecVersion='2')
        ET.SubElement(dist, 'title').text = ('WhateverXe Graphics — Automatic Installation'
                                            if args.autopkg else 'WhateverXe Graphics')
        ET.SubElement(dist, 'options', customize='never', rootVolumeOnly='true', hostArchitectures='x86_64')
        ET.SubElement(dist, 'domains', enable_anywhere='false', enable_currentUserHome='false', enable_localSystem='true')
        ranges = ET.SubElement(ET.SubElement(dist, 'volume-check', script='true'), 'allowed-os-versions')
        for system in policy['systems']:
            ET.SubElement(ranges, 'os-version', min=system['minimum'], before=system['before'])
        outline = ET.SubElement(dist, 'choices-outline')
        for name in list(components) + (['AutoRestart'] if args.autopkg else []):
            component_id = name.replace(' ', '')
            ET.SubElement(outline, 'line', choice=component_id)
            selected = 'true'
            if name not in ('Common', 'AutoRestart'):
                s = next(s for s in policy['systems'] if s['payload'] == name)
                selected = (f"system.compareVersions(system.version.ProductVersion, '{s['minimum']}') >= 0 && "
                            f"system.compareVersions(system.version.ProductVersion, '{s['before']}') < 0")
            choice = ET.SubElement(dist, 'choice', id=component_id, title=name, visible='false', enabled='false', selected=selected)
            ET.SubElement(choice, 'pkg-ref', id=PREFIX + '.' + component_id)
            ref = ET.SubElement(dist, 'pkg-ref', id=PREFIX + '.' + component_id, version=version)
            if not args.autopkg:
                ref.set('onConclusion', 'RequireRestart')
            ref.text = component_id + '.pkg'
        ET.indent(dist)
        distribution = work / 'Distribution'
        ET.ElementTree(dist).write(distribution, encoding='utf-8', xml_declaration=True)
        package = output / ('AutoPkg-Assets.pkg' if args.autopkg else f'WhateverXe-Graphics-{version}.pkg')
        run('productbuild', '--distribution', str(distribution), '--package-path', str(work), str(package))
        shutil.copyfile(distribution, output / 'Distribution.xml')
    # Development provenance stays outside the installer and installed system.
    manifest = {'policy': policy, 'systems': manifests}
    if args.autopkg:
        manifest['autopkg'] = True
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    digest = hashlib.sha256(package.read_bytes()).hexdigest()
    (output / 'SHA256SUMS').write_text(digest + '  ' + package.name + '\n')
    print(json.dumps({'package': package.name, 'bytes': package.stat().st_size,
                      'components': len(components) + int(args.autopkg), 'sha256': digest}))


if __name__ == '__main__':
    main()
