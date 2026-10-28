# This package is only for the installed OS's first-boot package phase.
# Do not relax the running-volume requirement to install into Recovery's target.
[ "${3:-}" = / ] || { echo 'AutoPkg requires the running target OS.' >&2; exit 1; }
[ ! -e /var/db/.AppleSetupDone ] || {
    echo 'AutoPkg is for fresh macOS installation before Setup Assistant. Use the normal Graphics pkg on a configured system.' >&2
    exit 1
}
# Do not rely on Distribution choices or volume checks in boot-install.
version=$(/usr/bin/sw_vers -productVersion)
if ! /usr/bin/awk -v actual="$version" -v minimum='@MINIMUM@' -v before='@BEFORE@' '
    function compare(a, b, aa, bb, na, nb, i) {
        na = split(a, aa, "."); nb = split(b, bb, ".")
        for (i = 1; i <= na || i <= nb; i++) {
            if (aa[i] + 0 < bb[i] + 0) return -1
            if (aa[i] + 0 > bb[i] + 0) return 1
        }
        return 0
    }
    BEGIN { exit !(compare(actual, minimum) >= 0 && compare(actual, before) < 0) }
'; then
    echo "This AutoPkg requires macOS @MINIMUM@ or later, before @BEFORE@; found $version." >&2
    exit 1
fi
