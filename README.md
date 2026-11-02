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
- The latest WhateverXe release, with Lilu.
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

Sequoia and Tahoe accept compatible updates within their OS family. Future Apple changes may require a Graphics update. Big Sur through Sonoma require the versions listed above. `amfi=0x80` and `ipc_control_port_options=0` are not required.

## Relationship to WEX

WEX supplies the OS/GPU adaptations and display control. This package supplies
the graphics drivers, their compiler components and AppleIntelTGLCompat, which
provides shared driver services. The release numbers do not have to match.

Use the latest releases of both components. GPU and display requirements are
described in the [WEX configuration guide](https://github.com/b00t0x/WhateverXe#configuration).

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

## Automatic installation before Setup Assistant (experimental)

AutoPkg installs Graphics during a **fresh macOS installation**, so acceleration is available in Setup Assistant. It has been tested on Sequoia and Tahoe; all six supported OS versions use the same package.

1. Prepare a USB installer for a supported macOS version.
2. Add upstream [AutoPkgInstaller 1.0.4](https://github.com/dortania/OpenCore-Legacy-Patcher/tree/main/payloads/Kexts/Acidanthera) to OpenCore alongside Lilu, WEX and **Mod** AMFIPass. Add `-autopkgbeta` for Tahoe.
3. Set `csr-active-config=030A0000` (`0xA03`) before starting the installer. This allows unapproved kexts to load; do not assume approval persists if you later remove the extra `0x200` bit.
4. Run `python3 tools/build.py --autopkg` from this repository and copy `dist/autopkg/AutoPkg-Assets.pkg` to `Library/Packages/` at the USB root. Keep the filename unchanged.
5. Install macOS normally. AutoPkg installs the matching assets, builds AuxKC and requests an extra restart before Setup Assistant. The initial USB installer UI is not accelerated.

The OCLP application, KDK.pkg and MetallibSupportPkg.pkg are not needed. Do not open AutoPkg manually or use it for an existing installation, an in-place upgrade or OTA. Do not combine WEX and OCLP AutoPkg assets on the same USB. Use the normal pkg above to update an existing system.

For installation errors, check `/var/log/install.log`. The standard [uninstaller](#uninstall) also removes AutoPkg-installed Graphics files.

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
python3 tools/test.py dist/WhateverXe-Graphics-0.4.0.pkg
```

To build and verify the optional automatic-installation pkg:

```sh
python3 tools/build.py --autopkg
python3 tools/test.py dist/autopkg/AutoPkg-Assets.pkg
```

The test also needs Node.js and `rcodesign` 0.29.0; CI supplies both. The builder
uses the checked-in signed `payloads/Common` and OS directories. It does not
fetch Apple originals, patch binaries or use signing keys. Output goes to
`dist/`. No Python, Node.js or rcodesign is needed on the target Mac.

[Source and signing information](docs/SOURCES.md). The license for the packaging
tools does not relicense the third-party payloads; see [notices](THIRD_PARTY.md).
