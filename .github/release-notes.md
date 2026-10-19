One standard pkg for macOS Big Sur through Tahoe. It installs signed graphics
components under `/Library` and rebuilds AuxKC without changing the System
snapshot. See the README for exact OS ranges, installation and removal.

Requires WhateverXe 0.3.0 or newer, Lilu, the attached AMFIPass 1.4.1 Mod and
the SIP configuration documented in the README. Configure EFI separately.
For GPU support and known issues, see https://github.com/b00t0x/WhateverXe.

Assets:
- `WhateverXe-Graphics-0.1.0.pkg`
- `uninstall.sh`
- `AMFIPass-v1.4.1-Mod-RELEASE.zip`
- `SHA256SUMS`

The pkg container is unsigned and not notarized. Modified payloads are signed
with the matching Mod chain. Original Apple compiler signatures are preserved.
