One standard pkg for macOS Big Sur through Tahoe. It installs signed graphics
components under `/Library` and rebuilds AuxKC without changing the System
snapshot. All supported OSes share one TGLCompat build in the Common payload.
See the [README](https://github.com/b00t0x/WhateverXe-Graphics#readme) for requirements,
installation, removal and using other OCLP root patches.

Requires WhateverXe 0.3.0 or newer, Lilu, Mod AMFIPass and the documented SIP
configuration. Configure EFI separately. Download
[AMFIPass](https://github.com/b00t0x/WhateverXe-Graphics/blob/main/extras/AMFIPass-v1.4.1-Mod-RELEASE.zip)
and the current [uninstall.sh](https://github.com/b00t0x/WhateverXe-Graphics/blob/main/uninstall.sh)
from the repository; they are maintained independently of pkg releases.
For GPU support and known issues, see [WhateverXe](https://github.com/b00t0x/WhateverXe).

Release assets are the pkg and `SHA256SUMS`.

The pkg container is unsigned and not notarized. Modified payloads are signed
with the matching Mod chain. Original Apple compiler signatures are preserved.
