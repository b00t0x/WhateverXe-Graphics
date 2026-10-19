#!/usr/bin/env python3
"""Verify checked-in signatures without installing a private trust anchor."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOD_LEAF = '6de7fc5377deac4f5fe21194684f57f553c3592c'
APPLE_BACKEND = 'a27eaea380aee524a1972927cb44774da1affe0cea93e94c307927f38d41aaf4'
MAGICS = {b'\xcf\xfa\xed\xfe', b'\xce\xfa\xed\xfe', b'\xca\xfe\xba\xbe', b'\xbe\xba\xfe\xca'}


def run(*args):
    return subprocess.check_output([str(a) for a in args], stderr=subprocess.STDOUT)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rcodesign', default='rcodesign')
    args = parser.parse_args()
    seen = set()
    for path in sorted((ROOT / 'payloads').rglob('*')):
        assert not path.is_symlink(), path
        if not path.is_file():
            continue
        data = path.read_bytes()
        if data[:4] not in MAGICS:
            continue
        sha = hashlib.sha256(data).hexdigest()
        if sha in seen:
            continue
        seen.add(sha)
        # Original Apple compiler bytes (including signature) are part of the
        # adapter's input contract. Never re-sign this file.
        if path.name == 'libigc-tgl.dylib':
            assert sha == APPLE_BACKEND, path
        if path.name in {'AppleIntelTGLCompat', 'adapter.dylib', 'TGLVA'}:
            assert b'/Users/' not in data and b'/home/' not in data, path
        run(args.rcodesign, 'verify', path)
        info = run(args.rcodesign, 'print-signature-info', path).lower()
        assert b'signature_verifies: true' in info, path
        if path.name != 'libigc-tgl.dylib':
            assert MOD_LEAF.encode() in info, path
        result = subprocess.run(['codesign', '--verify', '--strict', str(path)], capture_output=True)
        # This private Mod chain is intentionally not installed in the CI trust
        # store. CMS verification above checks it cryptographically instead.
        assert result.returncode == 0 or b'CSSMERR_TP_NOT_TRUSTED' in result.stderr, result.stderr
    for plist in (ROOT / 'payloads').rglob('Contents/Info.plist'):
        bundle = plist.parent.parent
        result = subprocess.run(['codesign', '--verify', '--deep', '--strict', str(bundle)], capture_output=True)
        assert result.returncode == 0 or b'CSSMERR_TP_NOT_TRUSTED' in result.stderr, result.stderr
    expected = json.loads((ROOT / 'docs/payload-provenance.json').read_text())
    # One build supplies every OS. Reject accidentally reintroduced per-OS copies.
    provider = ROOT / 'payloads/Common/Library/Extensions/AppleIntelTGLCompat.kext'
    assert list((ROOT / 'payloads').rglob('AppleIntelTGLCompat.kext')) == [provider]
    assert set(expected['providers']) == {'Common'}
    for os, entry in expected['providers'].items():
        path = ROOT / 'payloads' / os / 'Library/Extensions/AppleIntelTGLCompat.kext/Contents/MacOS/AppleIntelTGLCompat'
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry['sha256'], os
    extra = ROOT / 'extras/AMFIPass-v1.4.1-Mod-RELEASE.zip'
    assert hashlib.sha256(extra.read_bytes()).hexdigest() == expected['amfipass_sha256']
    print(f'PASS: {len(seen)} unique signed Mach-O files, bundle seals, provider provenance and AMFIPass archive')


if __name__ == '__main__':
    main()
