"""Reject build-identity gates in servicing adapters before and after packaging.

This artifact regression check complements the source-level installer/ABI tests;
it is not proof of compatibility with an unknown future Apple ABI. Fixed Apple
donor binaries and their provenance hashes are intentionally outside its scope.
"""
import re

ADAPTERS = (
    'Library/GPUBundles/AppleIntelTGLGraphicsMTLDriver.bundle/Contents/MacOS/impostor.dylib',
    'Library/GPUBundles/AppleIntelTGLGraphicsMTLDriver.bundle/Contents/MacOS/descriptor.dylib',
    'Library/GPUBundles/AppleIntelTGLGraphicsVADriver.bundle/Contents/MacOS/TGLVA',
    'Library/GPUBundles/XeCompilerAdapter.bundle/Contents/MacOS/adapter.dylib',
)


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


if __name__ == '__main__':
    test_rejection()
    print('PASS: servicing artifact policy rejects build-gate mutations')
