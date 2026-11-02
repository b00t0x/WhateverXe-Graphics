# Only the installed OS's first-boot package phase may run this package.
[ "${3:-}" = / ] || { echo 'AutoPkg requires the running target OS.' >&2; exit 1; }
[ ! -e /var/db/.AppleSetupDone ] || {
    echo 'AutoPkg requires a fresh macOS installation before Setup Assistant.' >&2
    exit 1
}
# Policy ranges are generated from the same source as the normal Installer UI.
version=$(/usr/bin/sw_vers -productVersion)
selected=$(/usr/bin/awk -v actual="$version" '
    function compare(a, b, aa, bb, na, nb, i) {
        na = split(a, aa, "."); nb = split(b, bb, ".")
        for (i = 1; i <= na || i <= nb; i++) {
            if (aa[i] + 0 < bb[i] + 0) return -1
            if (aa[i] + 0 > bb[i] + 0) return 1
        }
        return 0
    }
    BEGIN {
@OS_RANGES@
        exit 1
    }
') || { echo "Unsupported AutoPkg macOS version: $version" >&2; exit 1; }
# Reject existing Graphics bundles, including files left by a failed attempt.
# A normal Graphics package is the supported route for an existing installation.
for path in @BUNDLE_PATHS@; do
    [ ! -e "/$path" ] && [ ! -L "/$path" ] || {
        echo "AutoPkg requires a clean installation; already present: /$path" >&2
        exit 1
    }
done
