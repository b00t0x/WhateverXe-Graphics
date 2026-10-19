# Payload sources and signing

This repository builds an installer from final, signed payload trees. It does
not reproduce the full Apple extraction, binary patching and signing pipeline.
Original installers, signing keys and development captures are not build inputs
for this repository. The packaging scripts are derived from the Xe Data
installer maintained alongside WhateverXe.

## AppleIntelTGLCompat

Source and its shared headers remain in
[WhateverXe](https://github.com/b00t0x/WhateverXe). The included providers retain
the OS-specific 0.5.0 builds; they are not represented as builds of WEX's latest
source. Each row identifies the provider source revision:

| Payload | WEX source revision |
| --- | --- |
| Big Sur | [7a2725b](https://github.com/b00t0x/WhateverXe/tree/7a2725b6e036ace9051c5c64b204718d1e72a0e5/AppleIntelTGLCompat) |
| Monterey | [b04f9c2](https://github.com/b00t0x/WhateverXe/tree/b04f9c2a76ef6b6c52c3379c90c181e951f42b16/AppleIntelTGLCompat) |
| Ventura | [91132d8](https://github.com/b00t0x/WhateverXe/tree/91132d890080769facd0fb29a7aa4ad3b1e666ff/AppleIntelTGLCompat) |
| Sonoma | [5adb0e1](https://github.com/b00t0x/WhateverXe/tree/5adb0e1220c69ddad4b4909dd1d04e3cf2c8f897/AppleIntelTGLCompat) |
| Sequoia | [4736307](https://github.com/b00t0x/WhateverXe/tree/4736307613f4ce40e881ce3e7f95fd6c18408a66/AppleIntelTGLCompat) |
| Tahoe | [2446f37](https://github.com/b00t0x/WhateverXe/tree/2446f372e4f41652f543f795660250a2ecb1d8c7/AppleIntelTGLCompat) |

[Machine-readable provenance](payload-provenance.json) records the source file
and final executable hashes. Provider debug maps were removed where present,
and the same Mod chain was reapplied. Section contents/addresses, exported
symbols and entitlements were preserved. These source references do not promise
byte-identical rebuilding with a different compiler or signing invocation.

## Graphics and compiler payloads

`payloads/Common` contains the shared GL bundle. OS-named directories contain
complete signed kernel, Metal, VA and OpenCL units. Compiler adapter/backend
units accompany the later OS payloads; Big Sur uses its native compiler plugin.
The imported assets preserve the established Data paths and OS-specific ABI
adaptations. The builder never rewrites them or chooses hardware/connector paths.

The original Apple-signed `libigc-tgl.dylib` must remain byte-for-byte unchanged:
the adapter checks its complete file hash. The verifier enforces that identity.
No distribution of original installation media is needed to assemble this pkg.

## Mod signing and AMFIPass

Modified payloads use the Mod certificate chain. Its leaf SHA-1 fingerprint is
`6DE7FC5377DEAC4F5FE21194684F57F553C3592C`. This fingerprint identifies the
signer; it is not a private key. CI verifies signatures and builds the pkg
without importing a signing identity or installing a private trust anchor.

The separate `extras/AMFIPass-v1.4.1-Mod-RELEASE.zip` is copied unchanged from
[the existing Mod distribution](https://github.com/b00t0x/OpenCore-Legacy-Patcher/blob/b78fdeb8ffaa78168db076dc4bcbb3c3f67c07c4/payloads/Kexts/Acidanthera/AMFIPass-v1.4.1-Mod-RELEASE.zip).
Its SHA-256 is
`71f41de42e355d2a83e6f093ef34a5b24d0a9c9a9085830b2317f1b874f56250`.
This is provenance, not an OCLP installation dependency. The ZIP is included in
this repository's release assets and is configured in EFI separately.

CI pins [apple-codesign 0.29.0](https://github.com/indygreg/apple-platform-rs/releases/tag/apple-codesign%2F0.29.0)
for CMS/signature checks, alongside Apple's `codesign`. The Mod chain need not
be trusted by the build host. Signing happens before an asset is imported here;
there are no signing secrets in Actions.
