# Changelog

## 0.3.1

### Packaging correction

- Correct the AppleIntelTGLCompat dependency metadata that prevented installation of 0.3.0.

### Changes carried over from 0.3.0

- Add graphics payloads for Alder Lake-H/P/U and Raptor Lake-H/P/U, with the updated Compat provider for fixed HDMI/DisplayPort support. Use the latest [WhateverXe](https://github.com/b00t0x/WhateverXe/releases).
- Fix shader compilation failures on Sonoma–Tahoe using the OS-native AIR converter, based on work in [JulioNectar/Hackintosh-XPS13Plus-IrisXe-Tahoe](https://github.com/JulioNectar/Hackintosh-XPS13Plus-IrisXe-Tahoe/tree/0ad1bc5d3b9e73c918be174f791f4d739cde51e9/macos/src).
- Accept compatible compiler updates on Sonoma–Tahoe without requiring an exact UUID match; retain API and image checks and remove the previous converter fallback.

See [WEX compatibility and known issues](https://github.com/b00t0x/WhateverXe#compatibility) for remaining limitations.

## 0.3.0

Use the latest [WhateverXe](https://github.com/b00t0x/WhateverXe/releases) release for the new mobile GPU and fixed TC display support.

### Added

- Add signed graphics payloads for the Alder Lake-H/P/U and Raptor Lake-H/P/U devices accepted by WEX 0.6.0.
- Update the common AppleIntelTGLCompat provider for fixed TC HDMI/DisplayPort and scoped graphics-policy registration.

### Fixed

- Fix shader compilation failures on Sonoma–Tahoe by using the OS-native AIR converter for inputs rejected by the previous converter. This approach was informed by the compiler adapter and LLVM bridge in [JulioNectar/Hackintosh-XPS13Plus-IrisXe-Tahoe](https://github.com/JulioNectar/Hackintosh-XPS13Plus-IrisXe-Tahoe/tree/0ad1bc5d3b9e73c918be174f791f4d739cde51e9/macos/src).
- On Sonoma–Tahoe, accept compatible compiler updates without requiring an exact UUID match. Required API and image checks remain; incompatible inputs fail explicitly instead of falling back to the previous converter.

Sequoia App Store video hangs remain unresolved. See [WEX compatibility and known issues](https://github.com/b00t0x/WhateverXe#compatibility) for hardware coverage and limitations.

## 0.2.0

Works with WEX **0.3.0 or newer** on previously supported GPUs. The newly added GPUs require WEX **0.5.0**; updating both components is recommended.

### Added

- Add graphics drivers for Alder Lake-S support and the additional GPU models accepted by WEX 0.5.0.

### Fixed

- Fix observed Chrome drawing failures and incorrect rendering with antialiasing enabled.
- Correct rendering errors on smaller integrated GPUs.

See the [WEX compatibility and known issues](https://github.com/b00t0x/WhateverXe#compatibility) for tested hardware and remaining limitations.

## 0.1.0

Initial signed graphics package for WhateverXe 0.3.0 or newer, covering Big Sur through Tahoe.
