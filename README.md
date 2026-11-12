# WhateverXe Graphics

[日本語](README_ja.md)

Signed graphics drivers and a macOS installer for [WhateverXe](https://github.com/b00t0x/WhateverXe). The package installs under `/Library` and rebuilds AuxKC without patching System files or snapshots.
Use the latest WEX and Graphics releases together. See [WEX](https://github.com/b00t0x/WhateverXe) for supported GPUs, configuration and known issues, and [CHANGELOG](CHANGELOG.md) for package changes.

## Requirements

- OpenCore with Lilu, the latest WEX and [AMFIPass 1.4.1 Mod](extras/AMFIPass-v1.4.1-Mod-RELEASE.zip). Upstream AMFIPass is not a substitute.
- SIP setting `csr-active-config=03080000` (`0x803`). Full SIP is unsupported.

| macOS | Required version |
| --- | --- |
| Big Sur | 11.7.11 |
| Monterey | 12.7.6 |
| Ventura | 13.7.8 |
| Sonoma | 14.8.9 |
| Sequoia | 15.8.x |
| Tahoe | 26.7 or newer |

For other OCLP root patches, use the [custom OCLP build](https://github.com/b00t0x/OpenCore-Legacy-Patcher) with the matching Mod signing chain.

## Install

1. Configure OpenCore as described in [WEX](https://github.com/b00t0x/WhateverXe#installation). Restore any older Xe System patch first.
2. Boot the target macOS and open `WhateverXe-Graphics-*.pkg` from [Releases](https://github.com/b00t0x/WhateverXe-Graphics/releases).
3. Restart after installation succeeds. Resolve any reported installation error before restarting.

The installer does not change EFI or SIP. The pkg is unsigned and not notarized; its modified graphics payloads carry the Mod code signature.

## Automatic installation before Setup Assistant

AutoPkg enables graphics acceleration during a **fresh macOS installation**. It has been tested on Sequoia and Tahoe.

1. Prepare a supported macOS USB installer and download [`AutoPkg-Assets.pkg`](https://github.com/b00t0x/WhateverXe-Graphics/releases/latest/download/AutoPkg-Assets.pkg) from Releases.
2. Copy it into `Library/Packages/` on that USB, keeping the filename. Create the `Packages` folder if it does not exist. To open the hidden `Library` folder, use the following command with your USB's volume name:

   ```sh
   open "/Volumes/Install macOS Tahoe/Library"
   ```

3. Add upstream [AutoPkgInstaller 1.0.4](https://github.com/dortania/OpenCore-Legacy-Patcher/blob/main/payloads/Kexts/Acidanthera/AutoPkgInstaller-v1.0.4-RELEASE.zip) to OpenCore alongside Lilu, WEX and Mod AMFIPass. Set `csr-active-config=030A0000` (`0xA03`); also add `-autopkgbeta` for Tahoe.
4. Install macOS normally. An extra restart applies Graphics before Setup Assistant; the initial USB installer UI is not accelerated.

Do not open AutoPkg manually. Use the standard pkg for existing systems or updates, and do not combine WEX and OCLP AutoPkg assets on one USB. The OCLP application, KDK and MetallibSupportPkg are unnecessary.
`0xA03` allows unapproved kexts to load; removing its extra `0x200` bit later does not necessarily preserve approval.

## Uninstall

Download the latest [`uninstall.sh`](uninstall.sh), run it, then restart:

```sh
sudo bash uninstall.sh
```

This removes Graphics installed by either method and rebuilds AuxKC. It leaves EFI components in place and does not restore an older graphics stack. Installation errors are recorded in `/var/log/install.log`.

## Build

Requires macOS, Xcode command-line tools and Python 3.10+. Verification also needs Node.js and `rcodesign` 0.29.0.

```sh
python3 tools/build.py
python3 tools/test.py dist/WhateverXe-Graphics-0.4.2.pkg
```

For AutoPkg, add `--autopkg` to the build command and test `dist/autopkg/AutoPkg-Assets.pkg`.
Add `--native-history` to the test command to replay released PCI dispatch and GL URB regressions on the extracted payloads; this requires x86_64 execution, either native or through Rosetta.
The builder uses the checked-in signed payloads; it does not fetch Apple originals or require signing keys.

[Source and signing information](docs/SOURCES.md) · [Third-party notices](THIRD_PARTY.md)
