"""Check dependencies resolved within one selected graphics payload set."""
import plistlib
import re


def version(value):
    # These payloads use numeric release versions; reject unsupported spellings.
    if not isinstance(value, str) or not re.fullmatch(r'\d+\.\d+\.\d+', value):
        raise ValueError(f'unsupported payload dependency version: {value!r}')
    return tuple(map(int, value.split('.')))


def check_dependencies(plists, label):
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
    return checked


def check_payload_sets(payloads, systems):
    common = list((payloads / 'Common/Library/Extensions').rglob('*.kext/Contents/Info.plist'))
    for system in systems:
        clients = list((payloads / system['payload'] / 'Library/Extensions').rglob('*.kext/Contents/Info.plist'))
        if not check_dependencies(common + clients, system['name']):
            raise ValueError(f"{system['name']}: no bundled kext dependencies checked")
