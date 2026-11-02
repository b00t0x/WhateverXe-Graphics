"""Build one boot-install component with private, OS-selected script resources."""
import hashlib
import json
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from build import HERE, PREFIX, run, shell_script


def build_autopkg(output, policy, components, sources, manifests):
    version = policy['package_version']
    guard = (HERE / 'autopkg-preinstall.sh').read_text()
    ranges = '\n'.join(
        f'        if (compare(actual, "{s["minimum"]}") >= 0 && compare(actual, "{s["before"]}") < 0) '
        f'{{ print "{s["payload"]}"; exit 0 }}' for s in policy['systems'])
    bundles = sorted({'/'.join(rel.split('/')[:3]) for files in components.values() for rel in files})
    assert all(' ' not in p and p.startswith(('Library/Extensions/', 'Library/GPUBundles/')) for p in bundles)
    guard = guard.replace('@OS_RANGES@', ranges).replace('@BUNDLE_PATHS@', ' '.join(bundles))
    guard += '\n' + (HERE / 'preinstall.sh').read_text()
    with tempfile.TemporaryDirectory(prefix='xe-autopkg-') as tmp:
        work = Path(tmp)
        scripts = work / 'scripts'
        scripts.mkdir()
        for name, files in components.items():
            for rel, info in files.items():
                target = scripts / 'Assets' / name / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(sources[info['sha256']].read_bytes())
                target.chmod(info['mode'])
        shell_script(scripts / 'preinstall', guard)
        shell_script(scripts / 'postinstall', guard + '\n' +
                     (HERE / 'autopkg-install.sh').read_text() + '\n' +
                     (HERE / 'auxkc.sh').read_text() + '\n' + (HERE / 'postinstall.sh').read_text())
        component = work / 'AutoGraphics.pkg'
        run('pkgbuild', '--nopayload', '--identifier', PREFIX + '.AutoGraphics',
            '--version', version, '--scripts', str(scripts), str(component))
        expanded = work / 'metadata'
        run('pkgutil', '--expand', str(component), str(expanded))
        info = ET.parse(expanded / 'PackageInfo')
        info.getroot().set('postinstall-action', 'restart')
        info.write(expanded / 'PackageInfo', encoding='utf-8', xml_declaration=True)
        component.unlink()
        run('pkgutil', '--flatten', str(expanded), str(component))
        dist = ET.Element('installer-gui-script', minSpecVersion='2')
        ET.SubElement(dist, 'title').text = 'WhateverXe Graphics — Automatic Installation'
        ET.SubElement(dist, 'options', customize='never', rootVolumeOnly='true', hostArchitectures='x86_64')
        ET.SubElement(dist, 'domains', enable_anywhere='false', enable_currentUserHome='false', enable_localSystem='true')
        allowed = ET.SubElement(ET.SubElement(dist, 'volume-check', script='true'), 'allowed-os-versions')
        for s in policy['systems']:
            ET.SubElement(allowed, 'os-version', min=s['minimum'], before=s['before'])
        ET.SubElement(ET.SubElement(dist, 'choices-outline'), 'line', choice='AutoGraphics')
        choice = ET.SubElement(dist, 'choice', id='AutoGraphics', title='AutoGraphics', visible='false', enabled='false', selected='true')
        ET.SubElement(choice, 'pkg-ref', id=PREFIX + '.AutoGraphics')
        ET.SubElement(dist, 'pkg-ref', id=PREFIX + '.AutoGraphics', version=version,
                      onConclusion='RequireRestart').text = component.name
        ET.indent(dist)
        distribution = work / 'Distribution'
        ET.ElementTree(dist).write(distribution, encoding='utf-8', xml_declaration=True)
        package = output / 'AutoPkg-Assets.pkg'
        run('productbuild', '--distribution', str(distribution), '--package-path', str(work), str(package))
        (output / 'Distribution.xml').write_bytes(distribution.read_bytes())
    (output / 'manifest.json').write_text(json.dumps(
        {'policy': policy, 'systems': manifests, 'autopkg': True}, indent=2) + '\n')
    digest = hashlib.sha256(package.read_bytes()).hexdigest()
    (output / 'SHA256SUMS').write_text(digest + '  ' + package.name + '\n')
    print(json.dumps({'package': package.name, 'bytes': package.stat().st_size,
                      'components': 1, 'sha256': digest}))
