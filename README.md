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

Installer version ranges are not a guarantee of compatibility with future OS
updates. The current payloads target builds 20G1443, 21H1320, 22H730, 23J631,
24H32 and 25G241. Check the WEX documentation and release notes before updating
macOS. `amfi=0x80` and `ipc_control_port_options=0` are not required.

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

An optional `AutoPkg-Assets.pkg` installs the same Graphics payloads during a
fresh macOS installation and requests a native Installer restart after AuxKC is built. It uses
OCLP's [AutoPkgInstaller.kext](https://github.com/dortania/OpenCore-Legacy-Patcher/tree/main/payloads/Kexts/Acidanthera);
the OCLP application is not included or required. This mode requires validation
on a test installation before relying on it for first-boot graphics.

1. Prepare a USB macOS installer whose version meets the requirements above.
2. Add upstream AutoPkgInstaller 1.0.4 to OpenCore alongside Lilu, WEX and the
   **Mod** AMFIPass. AutoPkgInstaller 1.0.4 requires `-autopkgbeta` for Tahoe;
   that flag bypasses its OS-version limit, not a guarantee of compatibility.
3. Set `csr-active-config=030A0000` (value `0xA03`) before booting the installer.
   The extra `0x200` allows unapproved kexts to load without a Privacy & Security
   approval; it applies to all kexts, not just WEX. Do not assume removing it
   after installation preserves approval.
4. Build with `python3 tools/build.py --autopkg` and copy
   `dist/autopkg/AutoPkg-Assets.pkg` to `Library/Packages/` at the USB root.
   The same package supports all six OS versions listed above. Keep that exact
   filename. Do not replace it with the upstream OCLP package.
5. Install macOS normally. The package selects the running OS's assets, builds
   AuxKC and requests an additional restart before Setup Assistant; the initial
   USB installer UI is unchanged.

AutoPkg has one script-only component. Its private resources contain Common and
all supported OS assets; only Common and the detected OS are copied to `/Library`.
The resources stay in Installer's temporary directory. The normal Graphics pkg
continues to use standard payloads and OS selection in the Installer UI.

Never open AutoPkg manually. It rejects configured systems, non-running target
volumes, unsupported OS versions, old System-volume patches and existing Graphics
bundles (including partial installations). It is intended for fresh OS installation;
these guards are misuse checks, not a security boundary. In-place upgrades,
Software Update/OTA, and combining WEX and OCLP AutoPkg assets on the same USB are
outside this mode's scope. KDK.pkg and MetallibSupportPkg.pkg are not needed by
WEX. Inspect `/var/log/install.log` if installation fails.

Installer handles completion and the restart request; no script forces a reboot
or reads unfinished receipts. AutoPkg uses the dedicated
`org.b00t0x.WhateverXe.AutoGraphics` receipt, rather than the normal Common/OS
receipts. Its receipt has no file inventory because its script copies the assets.
The same standalone uninstaller below removes its files and receipt.

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
python3 tools/test.py dist/WhateverXe-Graphics-0.3.2.pkg
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
