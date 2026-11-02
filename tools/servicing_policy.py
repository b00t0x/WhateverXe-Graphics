"""Reject build-identity gates in servicing adapters before and after packaging.

This artifact regression check complements the source-level installer/ABI tests;
it is not proof of compatibility with an unknown future Apple ABI. Fixed Apple
donor binaries and their provenance hashes are intentionally outside its scope.
"""
import re
import posixpath
import struct

ADAPTERS = (
    'Library/GPUBundles/AppleIntelTGLGraphicsMTLDriver.bundle/Contents/MacOS/impostor.dylib',
    'Library/GPUBundles/AppleIntelTGLGraphicsMTLDriver.bundle/Contents/MacOS/descriptor.dylib',
    'Library/GPUBundles/AppleIntelTGLGraphicsVADriver.bundle/Contents/MacOS/TGLVA',
    'Library/GPUBundles/XeCompilerAdapter.bundle/Contents/MacOS/adapter.dylib',
)


def dylib_dependencies(data):
    """Read load dependencies, excluding the image's own LC_ID_DYLIB."""
    assert data[:4] == bytes.fromhex('cffaedfe'), 'expected x86_64 Mach-O'
    count, size = struct.unpack_from('<II', data, 16)
    end, offset = 32 + size, 32
    assert end <= len(data)
    result = []
    for _ in range(count):
        command, length = struct.unpack_from('<II', data, offset)
        assert length >= 8 and offset + length <= end
        if command in (0xc, 0x80000018, 0x8000001f, 0x80000023):
            name = struct.unpack_from('<I', data, offset + 8)[0]
            assert 24 <= name < length
            result.append(data[offset + name:offset + length].split(b'\0', 1)[0].decode())
        offset += length
    assert offset == end
    return result


def check_descriptor_dependency(data, label):
    dependencies = dylib_dependencies(data)
    assert dependencies.count('@loader_path/descriptor.dylib') == 1, label + ': missing local descriptor dependency'
    assert not any(p.startswith('/System/Library/Extensions/') for p in dependencies), label + ': obsolete System bundle dependency'
    return dependencies


def check_bytes(data, label):
    assert data[:4] == bytes.fromhex('cffaedfe'), label
    assert not any(key in data for key in (b'kern.osversion', b'ProductBuildVersion')), label
    assert not re.search(rb'(?<![A-Za-z0-9])(?:24|25)[A-Z][0-9]{1,5}[a-z]?(?![A-Za-z0-9])', data), label


def check_files(files, family):
    if family not in ('Sequoia', 'Tahoe'):
        return
    for name in ADAPTERS:
        check_bytes(files[name].read_bytes(), family + '/' + name)
    companion = files[ADAPTERS[0]].read_bytes()
    for dependency in check_descriptor_dependency(companion, family):
        if dependency.startswith('@loader_path/'):
            target = posixpath.normpath(posixpath.join(posixpath.dirname(ADAPTERS[0]), dependency[len('@loader_path/'):]))
            assert target in files, family + ': missing packaged dependency ' + target
    assert b'_dyld_get_shared_cache_range\0' in companion, family + ': missing dynamic cache classification'
    assert b'xe_install_descriptor_placement\0' in companion, family + ': missing descriptor integration'


def check_payloads(root):
    common = {p.relative_to(root / 'Common').as_posix(): p
              for p in (root / 'Common').rglob('*') if p.is_file()}
    for family in ('Sequoia', 'Tahoe'):
        selected = {p.relative_to(root / family).as_posix(): p
                    for p in (root / family).rglob('*') if p.is_file()}
        check_files(common | selected, family)


def test_rejection():
    # Generated identities, rather than an allowlist of reported Apple builds.
    prefix = bytes.fromhex('cffaedfe') + b'\0'
    check_bytes(prefix + b'kern.osrelease\0', 'valid')
    for value in (b'kern.osversion', b'ProductBuildVersion', b'24Z9876', b'25Q5432a'):
        try:
            check_bytes(prefix + value + b'\0', 'mutation')
        except AssertionError:
            continue
        raise AssertionError('build gate was not rejected')
    # LC_ID_DYLIB can retain the bridge's original identity; only load commands
    # create dependencies. Test the distinction and a missing local dependency.
    old = '/System/Library/Extensions/AppleIntelBDWGraphicsMTLDriver.bundle/Contents/MacOS/impostor.dylib'
    local = '@loader_path/descriptor.dylib'
    def image(identity, dependencies):
        commands = []
        for command, name in [(0xd, identity)] + [(0xc, p) for p in dependencies]:
            value = name.encode() + b'\0'
            length = (24 + len(value) + 7) & ~7
            commands.append(struct.pack('<6I', command, length, 24, 0, 0, 0) + value.ljust(length - 24, b'\0'))
        body = b''.join(commands)
        return struct.pack('<8I', 0xfeedfacf, 0x1000007, 3, 6, len(commands), len(body), 0, 0) + body
    check_descriptor_dependency(image(old, [local]), 'valid dependency')
    for dependencies in ([old], [], [local, old], [local, local]):
        try:
            check_descriptor_dependency(image(local, dependencies), 'dependency mutation')
        except AssertionError:
            continue
        raise AssertionError('broken descriptor dependency was not rejected')


if __name__ == '__main__':
    test_rejection()
    print('PASS: servicing artifact policy rejects build-gate mutations')
