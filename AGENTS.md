# WhateverXe Graphics

This repository distributes signed Data-volume graphics payloads and a standard
macOS pkg. WEX and AppleIntelTGLCompat source remain in WhateverXe.

Keep README.md and README_ja.md synchronized. General GPU/OS compatibility and
known issues belong in WhateverXe; this repository documents package use/builds.
Keep public project knowledge here, with source provenance in docs/SOURCES.md.
Private development notes, host details and test captures belong outside this repo.

Build: python3 tools/build.py
Test: python3 tools/test.py dist/WhateverXe-Graphics-0.1.0.pkg

Preserve signed payloads exactly unless deliberately updating and requalifying
an asset. Never sign original Apple compiler backends again. Keep signed bundles
whole. No keys, credentials, Apple original input caches or generated packages
in Git. The checked-in final payloads are an explicit binary exception.
Installer scripts use standard payloads and AuxKC; do not add custom backup,
manifest, hash-store or uninstall infrastructure to the installed system.
Release versioning is independent from WEX. Use source commits for provenance,
not a floating dependency on another repository's main branch.
