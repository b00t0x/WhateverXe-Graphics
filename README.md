# WhateverXe Graphics

[日本語](README_ja.md)

Signed graphics payloads and a standard macOS installer for
[WhateverXe](https://github.com/b00t0x/WhateverXe). One pkg selects the payload
for the running macOS and installs it under `/Library`, then rebuilds AuxKC.
System files and snapshots are not patched. OpenCore/EFI configuration remains
separate.

For supported GPUs, features, configuration and known issues, see
[WhateverXe](https://github.com/b00t0x/WhateverXe). WEX and this package have
independent release versions. AppleIntelTGLCompat is included in the package;
its source and shared headers remain in the WEX repository. One TGLCompat build
is shared by all supported macOS versions through the Common payload.

See the [changelog](CHANGELOG.md) for changes in each package version.

## Requirements

- Intel macOS, with the WEX/OpenCore configuration described in the WEX README.
- WhateverXe **0.3.0 or newer**, with Lilu; **0.5.0** is needed for the newly added GPUs.
- [AMFIPass 1.4.1 Mod](extras/AMFIPass-v1.4.1-Mod-RELEASE.zip), loaded through OpenCore. The ordinary upstream AMFIPass is not a substitute for this signing chain.
- SIP configuration `csr-active-config=03080000` (value `0x803`). Full SIP is not supported by this package.

| macOS | Required version |
| --- | --- |
| Big Sur | 11.7.11 |
| Monterey | 12.7.6 |
| Ventura | 13.7.8 |
| Sonoma | 14.8.9 |
| Sequoia | 15.8.x |
| Tahoe | 26.7 or newer |

Installer version ranges are not a guarantee of compatibility with future OS
updates. The current payloads target builds 20G1443, 21H1320, 22H730, 23J631,
24H32 and 25G241. Check the WEX documentation and release notes before updating
macOS. `amfi=0x80` and `ipc_control_port_options=0` are not required.

## Relationship to WEX

WEX supplies the OS/GPU adaptations and display control. This package supplies
the graphics drivers, their compiler components and AppleIntelTGLCompat, which
provides shared driver services. The release numbers do not have to match.

Graphics 0.2.0 retains the interfaces used by WEX 0.3.0/0.4.0 for previously
supported GPUs. Its Chrome/rendering fixes can therefore be used without WEX
0.5.0. Newly added GPUs and features that need changes on both sides require
WEX 0.5.0 and Graphics 0.2.0. Safari-update compatibility and the WEX display
startup fixes require the updated WEX plugin.

Hardware regression testing for this release used updated development versions
of both components. Compatibility
with older WEX versions was checked in code and with CPU interface tests, not
with a new full hardware regression run. Updating both is recommended.

## Using other OCLP root patches

If you also use OCLP for other root patches, use the
[custom OCLP build](https://github.com/b00t0x/OpenCore-Legacy-Patcher).
The upstream OCLP and Xe payloads require different AMFIPass trust anchors;
one AMFIPass cannot validate both sets. The custom OCLP build uses the matching
Mod signing chain.

## Install

1. Configure WEX, Lilu and the linked **Mod** AMFIPass in OpenCore. If an older
   Xe System patch is installed, restore it using its original recovery method.
2. Boot the macOS you want to install into.
3. Download the pkg from [Releases](https://github.com/b00t0x/WhateverXe-Graphics/releases), open it in Installer, and restart after installation succeeds.

The pkg uses normal Installer payloads and receipts. It updates AuxKC, and on
Tahoe disables `CoreMedia / AllowOnePassMetalScaling`. It does not modify EFI,
boot arguments or SIP. The pkg container is unsigned and not notarized; the
modified payloads carry the Mod code signature. If installation reports an
error, resolve it and reinstall before restarting.

## Uninstall

Download the current [`uninstall.sh`](uninstall.sh) from this repository, then run:

```sh
sudo bash uninstall.sh
```

Restart after successful removal. The script removes the graphics components
distributed by this project, removes the scaling override, rebuilds AuxKC and forgets
the graphics package receipts. Use the current script regardless of which pkg
version was installed. It leaves other CoreMedia settings intact. It does not remove WEX,
Lilu or AMFIPass from EFI, or restore an older graphics stack.

AMFIPass and this cleanup script are maintained in the repository independently
of the graphics pkg. Releases contain the pkg and its checksum.

## Build

On macOS with Xcode Command Line Tools and Python 3.10 or newer:

```sh
python3 tools/build.py
python3 tools/test.py dist/WhateverXe-Graphics-0.2.0.pkg
```

The test also needs Node.js and `rcodesign` 0.29.0; CI supplies both. The builder
uses the checked-in signed `payloads/Common` and OS directories. It does not
fetch Apple originals, patch binaries or use signing keys. Output goes to
`dist/`. No Python, Node.js or rcodesign is needed on the target Mac.

[Source and signing information](docs/SOURCES.md). The license for the packaging
tools does not relicense the third-party payloads; see [notices](THIRD_PARTY.md).
