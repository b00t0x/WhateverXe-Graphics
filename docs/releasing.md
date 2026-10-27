# Release checks

1. Finalize versions before validation. `CFBundleVersion` is the provider's
   release version; `OSBundleCompatibleVersion` is its oldest compatible ABI.
   Do not raise both just to bump a release. For each bundled dependency, require
   `OSBundleCompatibleVersion <= requested version <= CFBundleVersion`.
   An intentional ABI break needs coordinated client updates for every OS.
2. Build from the final signed bundles. `tools/build.py` checks Common combined
   with each OS payload before invoking the package tools. Never edit a signed
   plist in place; rebuild and sign the bundle, then update its provenance.
3. Run `tools/test.py` on the resulting pkg. It must pass dependency regressions,
   source signature/provenance checks, and checks of every extracted OS payload
   set. A successful build or matching checksums alone are insufficient.
4. Compare the final extracted bundles and installer scripts with the last
   hardware-tested candidate. Include plist versions, dependency declarations
   and personalities in that comparison, not only executable code. If these or
   installation behavior changed, use the final pkg on a supported test OS and
   check Installer completion, AuxKC generation, then reboot and verify the
   loaded components and graphics. Record the pkg hash and tested OS. Do not
   present earlier development-bundle tests as final-pkg installation tests;
   any omitted hardware check must be explicit in the maintainer's review.
5. Review the final changes before merging and tagging. PR and tag CI must pass;
   tags create drafts only. Confirm the draft's pkg/checksum, tag commit and
   CHANGELOG-derived text before publication. Publish the CI-tested artifact,
   not a separate untested local rebuild. If rebuilding changes only packaging
   timestamps/compression, verify extracted payload and script equivalence;
   otherwise repeat the affected checks.

Any version, metadata, payload or installer change after validation invalidates
the corresponding result. Repeat those checks before publication. Keep release
approval separate from CI success.
