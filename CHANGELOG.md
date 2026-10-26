# Changelog

## 0.3.0

The new mobile GPU and fixed TC display support requires WEX **0.6.0**. Previously supported GPUs retain compatibility with WEX **0.3.0 or newer**; updating both components is recommended.

### Added

- Add signed graphics payloads for the Alder Lake-H/P/U and Raptor Lake-H/P/U devices accepted by WEX 0.6.0.
- Update the common AppleIntelTGLCompat provider for fixed TC HDMI/DisplayPort and scoped graphics-policy registration.

### Fixed

- Use the OS-native AIR converter on Sonoma–Tahoe to support shader inputs rejected by the previous converter. Tahoe checks confirmed improved App Store scrolling and Maps rendering.
- Accept compatible compiler updates without requiring an exact UUID match. Required API and image checks remain; incompatible inputs fail explicitly instead of falling back to the previous converter.

Monterey/Ventura retain their direct compiler path; Big Sur continues to use its native compiler plugin. Sequoia App Store video hangs remain unresolved. See [WEX compatibility and known issues](https://github.com/b00t0x/WhateverXe#compatibility) for hardware coverage and limitations.

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
