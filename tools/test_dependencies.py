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
from released_contracts import check_released_clients


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


class DeviceMatchTests(unittest.TestCase):
    def check(self, framebuffer, accelerator='0x46a68086 0x46268086'):
        with tempfile.TemporaryDirectory() as tmp:
            paths = []
            for name, matches in [('AppleIntelTGLGraphics', accelerator),
                                  ('AppleIntelTGLGraphicsFramebuffer', framebuffer)]:
                path = Path(tmp) / (name + '.plist')
                path.write_bytes(plistlib.dumps({'CFBundleIdentifier': 'com.apple.driver.' + name,
                    'IOKitPersonalities': {'GPU': {'IOPCIPrimaryMatch': matches}}}))
                paths.append(path)
            check_dependencies(paths, 'test', ['46a6', '4626'])

    def test_single_and_dual_dimm(self):
        self.check('0x46a68086 0x46268086')

    def test_missing_framebuffer_identity(self):
        with self.assertRaisesRegex(ValueError, "missing=.*4626"):
            self.check('0x46a68086')

    def test_missing_accelerator_identity(self):
        with self.assertRaisesRegex(ValueError, "missing=.*4626"):
            self.check('0x46a68086 0x46268086', '0x46a68086')

    def test_unknown_or_masked_identity(self):
        with self.assertRaisesRegex(ValueError, 'extra=.*12348086'):
            self.check('0x46a68086 0x46268086 0x12348086')
        with self.assertRaisesRegex(ValueError, 'unsupported device match'):
            self.check('0x46008086&0xff00ffff')


class ReleasedContractTests(unittest.TestCase):
    def check_mutation(self, remove_device=False, raise_floor=False):
        # Change current policy and clients together. A self-consistency test
        # accepts that pair; frozen released contracts must detect the loss.
        devices = json.loads((build.HERE / 'policy.json').read_text())['device_ids']
        if remove_device:
            devices = [d for d in devices if d.lower() != '9a49']
        floor = '0.6.0' if raise_floor else '0.5.0'
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            infos = [{'CFBundleIdentifier': 'org.b00t0x.AppleIntelTGLCompat',
                      'CFBundleVersion': '0.8.0', 'OSBundleCompatibleVersion': floor}]
            for name in ['AppleIntelTGLGraphics', 'AppleIntelTGLGraphicsFramebuffer']:
                infos.append({'CFBundleIdentifier': 'com.apple.driver.' + name,
                    'IOKitPersonalities': {'GPU': {'IOPCIPrimaryMatch': ' '.join('0x' + d + '8086' for d in devices)}},
                    'OSBundleLibraries': {'org.b00t0x.AppleIntelTGLCompat': floor}})
            paths = []
            for i, info in enumerate(infos):
                path = root / f'{i}.plist'
                path.write_bytes(plistlib.dumps(info)); paths.append(path)
            self.assertGreater(check_dependencies(paths, 'Big Sur', devices), 0)
            if remove_device or raise_floor:
                with self.assertRaisesRegex(ValueError, 'lost released physical matches|released provider requirement'):
                    check_released_clients(paths, 'Big Sur')
            else:
                check_released_clients(paths, 'Big Sur')

    def test_preserved_contracts(self):
        self.check_mutation()

    def test_coordinated_device_removal_is_detected(self):
        self.check_mutation(remove_device=True)

    def test_coordinated_abi_floor_raise_is_detected(self):
        self.check_mutation(raise_floor=True)


class BuildPreflightTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        # Use the real supported OS list so newly added payloads are covered.
        policy = json.loads((build.HERE / 'policy.json').read_text())
        self.systems = policy['systems']
        self.device_ids = policy['device_ids']
        personalities = {'GPU': {'IOPCIPrimaryMatch': ' '.join('0x' + device + '8086' for device in self.device_ids)}}
        self.provider = self.write('Common', 'Compat', {
            'CFBundleIdentifier': 'org.b00t0x.AppleIntelTGLCompat',
            'CFBundleVersion': '0.6.0', 'OSBundleCompatibleVersion': '0.5.0'})
        self.clients = [self.write(s['payload'], 'Framebuffer', {
            'CFBundleIdentifier': 'com.apple.driver.AppleIntelTGLGraphicsFramebuffer',
            'OSBundleLibraries': {'org.b00t0x.AppleIntelTGLCompat': '0.5.0'},
            'IOKitPersonalities': personalities})
            for s in self.systems]
        for system in self.systems:
            self.write(system['payload'], 'Graphics', {
                'CFBundleIdentifier': 'com.apple.driver.AppleIntelTGLGraphics',
                'IOKitPersonalities': personalities})

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
        check_payload_sets(self.root / 'payloads', self.systems, self.device_ids)

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
