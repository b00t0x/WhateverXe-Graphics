# Payload sources and signing

This repository builds an installer from final, signed payload trees. It does
not reproduce the full Apple extraction, binary patching and signing pipeline.
Original installers, signing keys and development captures are not build inputs
for this repository.

## AppleIntelTGLCompat

Source and its shared headers remain in
[WhateverXe](https://github.com/b00t0x/WhateverXe). All supported macOS versions
use one RELEASE build of AppleIntelTGLCompat 0.5.0 from WEX commit
[`31826af`](https://github.com/b00t0x/WhateverXe/tree/31826afc837977e1f09f5109173d5a2b577aff78/AppleIntelTGLCompat).
Build that checkout with `python3 tools/build.py --release`, then sign the
resulting kext with the Mod chain before importing the complete bundle into
`payloads/Common/Library/Extensions/`. The package contains no per-OS provider
copies. OS admission uses the shared WEX kernel-version selector; physical-device
and binding guards remain in the shared source.

[Machine-readable provenance](payload-provenance.json) records this single source
revision, build configuration, source file hash and final signed executable hash.
The build strips debug maps before signing. These source references do not promise
byte-identical rebuilding with a different compiler or signing invocation.
The provider source and its shared headers belong to the same WEX revision.

## Graphics and compiler payloads

`payloads/Common` contains the shared TGLCompat kext, GL bundle and compiler adapter. OS-named
directories contain complete signed graphics/framebuffer, Metal, VA and OpenCL
units. The same compiler adapter serves Monterey through Tahoe; its unchanged Apple
backend and runtime accompany those OS payloads. Big Sur uses its native compiler plugin.
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
The ZIP is maintained in the repository independently of graphics pkg releases
and is configured in EFI separately. Download it from
[`extras/`](../extras/AMFIPass-v1.4.1-Mod-RELEASE.zip); it is not attached to every release.
OCLP itself is only needed when using other OCLP root patches. That combination
requires the custom OCLP build with the same Mod signing chain, as described
in the README.

CI pins [apple-codesign 0.29.0](https://github.com/indygreg/apple-platform-rs/releases/tag/apple-codesign%2F0.29.0)
for CMS/signature checks, alongside Apple's `codesign`. The Mod chain need not
be trusted by the build host. Signing happens before an asset is imported here;
there are no signing secrets in Actions.

## Repository utilities and package releases

The committed [`uninstall.sh`](../uninstall.sh) runs on its own and is maintained
across pkg versions. It removes the graphics components distributed by this
project under `/Library`, removes the scaling override, rebuilds AuxKC and
forgets the graphics receipts. It does not restore System-volume patches; use
the original patcher's restoration procedure for those.

Only the pkg and its checksum are release assets. AMFIPass and the uninstaller
have independent update schedules. The build does not generate an uninstaller
or copy either utility into its output.
