# Payload sources and signing

This repository builds an installer from final, signed payload trees. It does
not reproduce the full Apple extraction, binary patching and signing pipeline.
Original installers, signing keys and development captures are not build inputs
for this repository.

## AppleIntelTGLCompat

Source and its shared headers remain in
[WhateverXe](https://github.com/b00t0x/WhateverXe). All supported macOS versions
use one RELEASE build of AppleIntelTGLCompat 0.8.0 from WEX commit
[`ceb7bae`](https://github.com/b00t0x/WhateverXe/tree/ceb7bae3401979ae189919e6809d0c9117167311/AppleIntelTGLCompat).
Build that checkout with `python3 tools/build.py --release`, then sign the
resulting kext with the Mod chain before importing the complete bundle into
`payloads/Common/Library/Extensions/`. The package contains no per-OS provider
copies. OS admission uses the shared WEX kernel-version selector; physical-device
and binding guards remain in the shared source. The provider also carries the
source GraphicsPolicy.plist personality, restricted to admitted Display13 Intel
framebuffer clients; it does not override policy for other GPUs.
The provider includes the USB-C DisplayPort Alt Mode capability required by
the corresponding WEX connector support, including admission when another
output such as HDMI is connected. It also recognizes the complete Linux i915
Alder Lake-P and Raptor Lake-P/U PCI ID sets, including the single-DIMM
`4626` identity; WEX must use the same updated device table.

[Machine-readable provenance](payload-provenance.json) records this single source
revision, build configuration, source file hash and final signed executable hash.
The build strips debug maps before signing. These source references do not promise
byte-identical rebuilding with a different compiler or signing invocation.
The provider source and its shared headers belong to the same WEX revision.
Both native kernel drivers depend on Compat. Compat starts only when an active
WEX publishes the compatible runtime activation ABI; it does not import EFI-only
WEX symbols into AuxKC. The shared activation header is included in provenance.
Its compatibility floor is 0.5.0, matching the bundled framebuffer dependency.
The provider release version is independent of this ABI compatibility floor.

## Graphics and compiler payloads

`payloads/Common` contains the shared TGLCompat kext, GL bundle and compiler adapter. OS-named
directories contain complete signed graphics/framebuffer, Metal, VA and OpenCL
units. Framebuffer and accelerator PCI personalities use the supported IDs recorded
in `tools/policy.json`; build and extracted-package checks require both client
match sets to agree with that list. ID additions preserve driver code and
re-sign the complete bundles. The same compiler adapter serves Monterey through Tahoe; its unchanged Apple
backend and runtime accompany those OS payloads. Big Sur uses its native compiler plugin.
The common GL payload uses one set of exact-layout URB rules for four/six/eight-bank
VS-only and six-bank VS/GS allocations. The four-bank VS allocation ends at
160 KiB; the other measured layouts end at 360 KiB. The signed executable and predecessor hashes are recorded in
`payload-provenance.json`.

The GL, VA and OS-specific OpenCL dispatches admit the same physical IDs as
the supported device list. OpenCL uses exact vendor-checked bitmaps to fit
its existing code padding. Original compiler backends remain byte-identical;
these additions do not alter shader, URB or codec behavior. The signed file
hashes and accepted ID set are recorded under `userspace_admission` in the
provenance file and checked before package validation.

The imported assets preserve the established Data paths and OS-specific ABI
adaptations. The builder never rewrites them or chooses hardware/connector paths.

The Sequoia/Tahoe `impostor.dylib` and `TGLVA` companions select the OS family
without a product-build allowlist. Metal checks the method types and descriptor
private-pointer contract; VA retains its donor vtable and SPS input checks.
`servicing_adapters` in `payload-provenance.json` records the companion source
hashes and signed outputs. The servicing adaptation preserves `descriptor.dylib`,
`libigdmd.dylib` and the donor driver code/data. The enclosing bundles are sealed
with the Mod chain.
Package build/test checks cover the servicing adapters in both normal payloads
and AutoPkg resources. Source-build labels remain provenance only.
The companion also replaces the imported bridge's numeric shared-cache threshold
with dyld's current cache range. Only its symbol-resolved, byte-verified predicate
entry is redirected in process memory; projection code and the signed on-disk
bridge are unchanged. The companion remains mapped for that redirect's lifetime.

On Sonoma–Tahoe the adapter uses the OS GPUCompiler's native AIR-v4 serializer.
It checks the required APIs, System paths and shared LLVM image identity rather
than pinning compiler UUIDs. Missing APIs or incompatible inputs produce an
explicit error; there is no fallback to the previous bitcode converter.
Monterey and Ventura retain the direct compiler path.

The Metal executable in each of the six OS payloads includes the POSH ownership
repair for [WhateverXe #47](https://github.com/b00t0x/WhateverXe/issues/47).
Command-buffer deallocation checks whether the POSH pointer belongs to the queue
and frees it only when the command buffer owns the allocation. The patch checks
the exact predecessor executable and allocation and teardown instructions before
changing code. The Mod signature seals the updated executable with the existing
bundle resources and the original signed companion binaries.

The VA bundles for Big Sur through Tahoe include the video conversion shader
repair for [WhateverXe #60](https://github.com/b00t0x/WhateverXe/issues/60).
The TGLVA companion checks the donor shader table and native loader contract,
then supplies the Tiger Lake translation of the Gen11 conversion program at
index 3. The native loader processes the other programs with their original
inputs. The companion preserves the advertised video capabilities.
`servicing_adapters` in `payload-provenance.json` records the shader and signed
companion hashes for these payloads.

The VA context factory rejects its incomplete VPHAL post-processing context
before allocation. The donor has no concrete G12 VEBOX/SFC renderer for this
path, so VideoToolbox can use its image-conversion fallback. The original
factory refusal follows
[retropineaple/WhateverXe a5f4265](https://github.com/retropineaple/WhateverXe/commit/a5f4265).
The Big Sur payload distinguishes standalone image processing from codec scaler
contexts: both use feature `0x800`, but their native producer hint at config
offset `0x14` is zero for standalone processing and nonzero for codecs. It
preserves the codec scaler's native creation and dimension checks while rejecting
standalone processing and features `0x20`/`0x40`. The other OS payloads retain
the original factory refusal.
The signed VA executable hashes are recorded in `userspace_admission.files`.

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

## Installer-time package chainloading

The optional AutoPkg build uses the additional-package entry point described in
[OCLP PR #986](https://github.com/dortania/OpenCore-Legacy-Patcher/pull/986).
Upstream [AutoPkgInstaller 1.0.4](https://github.com/dortania/OpenCore-Legacy-Patcher/blob/main/payloads/Kexts/Acidanthera/AutoPkgInstaller-v1.0.4-RELEASE.zip)
registers the fixed `Library/Packages/AutoPkg-Assets.pkg` path during Installer
boot. The ZIP checked on 2026-10-27 has SHA-256
`91368c6e37002d19f5b8f39a6746790b8f73fc17a80fb27ab78d9ae743725745`.
The kext is obtained separately; this repository does not redistribute it.
Its plugin accepts Darwin 20–24 by default and provides `-autopkgbeta`.

The Graphics AutoPkg contains the existing signed payloads and native shell
scripts. It does not embed OCLP, its patch-selection engine or support DMGs.
A single script-only component selects Common and the running OS from private
script resources, then builds AuxKC. It uses the native package restart requirement,
including `postinstall-action="restart"` on that component. This component
metadata is also used by [Yubico's package builder](https://github.com/Yubico/ifd-yubico/blob/master/build-installer.sh).
The package scripts do not force a reboot or query in-progress receipts.
As documented by [munki-pkg](https://github.com/munki/munki-pkg#payload-free-packages),
`pkgbuild --nopayload` leaves no package receipt. AutoPkg success is recorded in
the install log and install history; its component identifier is not a receipt.
No OCLP application source is copied into this package.

## Repository utilities and package releases

The committed [`uninstall.sh`](../uninstall.sh) runs on its own and is maintained
across pkg versions. It removes the graphics components distributed by this
project under `/Library`, removes the scaling override, rebuilds AuxKC and
forgets the graphics receipts. It does not restore System-volume patches; use
the original patcher's restoration procedure for those.

Only the pkg and its checksum are release assets. AMFIPass and the uninstaller
have independent update schedules. The build does not generate an uninstaller
or copy either utility into its output.
