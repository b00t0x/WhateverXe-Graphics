#!/usr/bin/env python3
"""Regression coverage for provider/client compatibility interval checks."""
import plistlib
import json
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
import build
from kext_dependencies import check_dependencies, check_payload_sets


class DependencyTests(unittest.TestCase):
    def check(self, minimum='0.5.0', requested='0.5.0', include_provider=True):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            provider = {'CFBundleIdentifier': 'org.b00t0x.AppleIntelTGLCompat',
                        'CFBundleVersion': '0.6.0', 'OSBundleCompatibleVersion': minimum}
            client = {'CFBundleIdentifier': 'com.apple.driver.AppleIntelTGLGraphicsFramebuffer',
                      'OSBundleLibraries': {'org.b00t0x.AppleIntelTGLCompat': requested,
                                            'com.apple.kpi.iokit': '10.0.0'}}
            entries = [client, provider] if include_provider else [client]
            paths = []
            for index, entry in enumerate(entries):
                path = root / f'{index}.plist'
                path.write_bytes(plistlib.dumps(entry))
                paths.append(path)
            return check_dependencies(paths, 'test')

    def test_released_030_mismatch(self):
        with self.assertRaisesRegex(ValueError, 'outside provider compatibility range'):
            self.check(minimum='0.6.0')

    def test_compatible_lower_boundary(self):
        self.assertEqual(self.check(), 1)

    def test_current_upper_boundary(self):
        self.assertEqual(self.check(requested='0.6.0'), 1)

    def test_future_requirement(self):
        with self.assertRaisesRegex(ValueError, 'outside provider compatibility range'):
            self.check(requested='0.7.0')

    def test_missing_provider(self):
        with self.assertRaisesRegex(ValueError, 'missing provider'):
            self.check(include_provider=False)


class BuildPreflightTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        # Use the real supported OS list so newly added payloads are covered.
        policy = json.loads((build.HERE / 'policy.json').read_text())
        self.systems = policy['systems']
        self.provider = self.write('Common', 'Compat', {
            'CFBundleIdentifier': 'org.b00t0x.AppleIntelTGLCompat',
            'CFBundleVersion': '0.6.0', 'OSBundleCompatibleVersion': '0.5.0'})
        self.clients = [self.write(s['payload'], 'Framebuffer', {
            'CFBundleIdentifier': 'com.apple.driver.AppleIntelTGLGraphicsFramebuffer',
            'OSBundleLibraries': {'org.b00t0x.AppleIntelTGLCompat': '0.5.0'}})
            for s in self.systems]

    def write(self, component, name, info):
        path = self.root / 'payloads' / component / 'Library/Extensions' / (name + '.kext') / 'Contents/Info.plist'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(plistlib.dumps(info))
        return path

    def assert_build_rejected(self):
        output = self.root / 'dist'
        with patch.object(build, 'ROOT', self.root), patch.object(build, 'run') as commands, \
                patch.object(sys, 'argv', ['build.py', '--output', str(output)]):
            with self.assertRaises(ValueError):
                build.main()
            commands.assert_not_called()
        self.assertFalse(output.exists())

    def test_current_payload_sets(self):
        check_payload_sets(self.root / 'payloads', self.systems)

    def test_released_mismatch_stops_build(self):
        info = plistlib.loads(self.provider.read_bytes())
        info['OSBundleCompatibleVersion'] = '0.6.0'
        self.provider.write_bytes(plistlib.dumps(info))
        self.assert_build_rejected()

    def test_each_os_is_checked_before_packaging(self):
        for path in self.clients:
            with self.subTest(payload=path.relative_to(self.root).parts[1]):
                original = path.read_bytes()
                info = plistlib.loads(original)
                info['OSBundleLibraries']['org.b00t0x.AppleIntelTGLCompat'] = '0.7.0'
                path.write_bytes(plistlib.dumps(info))
                self.assert_build_rejected()
                path.write_bytes(original)

    def test_missing_common_provider_stops_build(self):
        self.provider.unlink()
        self.assert_build_rejected()


if __name__ == '__main__':
    unittest.main()
