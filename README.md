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
its source and shared headers remain in the WEX repository.

## Requirements

- Intel macOS, with the WEX/OpenCore configuration described in the WEX README.
- WhateverXe **0.3.0 or newer**, with Lilu.
- [AMFIPass 1.4.1 Mod](https://github.com/b00t0x/WhateverXe-Graphics/releases/latest/download/AMFIPass-v1.4.1-Mod-RELEASE.zip), loaded through OpenCore. The ordinary upstream AMFIPass is not a substitute for this signing chain.
- SIP configuration `csr-active-config=03080000` (value `0x803`). Full SIP is not supported by this package.

| macOS | Installer accepts |
| --- | --- |
| Big Sur | 11.7.11 to before 12 |
| Monterey | 12.7.6 to before 13 |
| Ventura | 13.7.8 to before 14 |
| Sonoma | 14.8.9 to before 15 |
| Sequoia | 15.8.x |
| Tahoe | 26.7 to before 27 |

Installer version ranges are not a guarantee of compatibility with future OS
updates. The current payloads target builds 20G1443, 21H1320, 22H730, 23J631,
24H32 and 25G241. Check the WEX documentation and release notes before updating
macOS. `amfi=0x80` and `ipc_control_port_options=0` are not required.

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

Download `uninstall.sh` from the same release, then run:

```sh
sudo bash uninstall.sh
```

Restart after successful removal. The script removes the added Xe graphics
files, removes the scaling override, rebuilds AuxKC and forgets this package's
receipts. It leaves other CoreMedia settings intact. It does not remove WEX,
Lilu or AMFIPass from EFI, or restore an older graphics stack.

## Build

On macOS with Xcode Command Line Tools and Python 3.10 or newer:

```sh
python3 tools/build.py
python3 tools/test.py dist/WhateverXe-Graphics-0.1.0.pkg
```

The test also needs Node.js and `rcodesign` 0.29.0; CI supplies both. The builder
uses the checked-in signed `payloads/Common` and OS directories. It does not
fetch Apple originals, patch binaries or use signing keys. Output goes to
`dist/`. No Python, Node.js or rcodesign is needed on the target Mac.

[Source and signing information](docs/SOURCES.md). The license for the packaging
tools does not relicense the third-party payloads; see [notices](THIRD_PARTY.md).
