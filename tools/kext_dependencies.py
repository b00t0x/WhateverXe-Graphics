"""Check dependencies resolved within one selected graphics payload set."""
import plistlib
import re


def version(value):
    # These payloads use numeric release versions; reject unsupported spellings.
    if not isinstance(value, str) or not re.fullmatch(r'\d+\.\d+\.\d+', value):
        raise ValueError(f'unsupported payload dependency version: {value!r}')
    return tuple(map(int, value.split('.')))


def check_dependencies(plists, label, device_ids=None):
    providers = {}
    for path in plists:
        info = plistlib.loads(path.read_bytes())
        identifier = info['CFBundleIdentifier']
        if identifier in providers:
            raise ValueError(f'{label}: duplicate provider {identifier}')
        providers[identifier] = info
    checked = 0
    for client, info in providers.items():
        for dependency, requested in info.get('OSBundleLibraries', {}).items():
            provider = providers.get(dependency)
            if provider is None:
                if dependency.startswith('org.b00t0x.'):
                    raise ValueError(f'{label}: {client} requires missing provider {dependency}')
                continue  # System kexts are supplied by the target OS.
            current = provider['CFBundleVersion']
            compatible = provider['OSBundleCompatibleVersion']
            if not version(compatible) <= version(requested) <= version(current):
                raise ValueError(f'{label}: {client} requires {dependency} {requested}, '
                                 f'outside provider compatibility range {compatible}–{current}')
            checked += 1
    if device_ids is not None:
        expected = {int(device, 16) << 16 | 0x8086 for device in device_ids}
        for client in ('com.apple.driver.AppleIntelTGLGraphics',
                       'com.apple.driver.AppleIntelTGLGraphicsFramebuffer'):
            if client not in providers:
                raise ValueError(f'{label}: missing device-match client {client}')
            actual = set()
            for personality in providers[client].get('IOKitPersonalities', {}).values():
                for match in personality.get('IOPCIPrimaryMatch', '').split():
                    if not re.fullmatch(r'0x[0-9a-fA-F]{8}', match):
                        raise ValueError(f'{label}: unsupported device match {match}')
                    actual.add(int(match, 16))
            if actual != expected:
                missing = sorted(f'{pci >> 16:04x}' for pci in expected - actual)
                extra = sorted(f'{pci:08x}' for pci in actual - expected)
                raise ValueError(f'{label}: {client} PCI match mismatch: missing={missing}, extra={extra}')
    return checked


def check_payload_sets(payloads, systems, device_ids=None):
    from released_contracts import check_released_clients
    common = list((payloads / 'Common/Library/Extensions').rglob('*.kext/Contents/Info.plist'))
    for system in systems:
        clients = list((payloads / system['payload'] / 'Library/Extensions').rglob('*.kext/Contents/Info.plist'))
        if not check_dependencies(common + clients, system['name'], device_ids):
            raise ValueError(f"{system['name']}: no bundled kext dependencies checked")
        check_released_clients(common + clients, system['payload'])
