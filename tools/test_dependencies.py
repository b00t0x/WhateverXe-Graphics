#!/usr/bin/env python3
"""Regression coverage for provider/client compatibility interval checks."""
import plistlib
import tempfile
import unittest
from pathlib import Path
from kext_dependencies import check_dependencies


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


if __name__ == '__main__':
    unittest.main()
