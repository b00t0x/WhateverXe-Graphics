# This package is only for the installed OS's first-boot package phase.
# Do not relax the running-volume requirement to install into Recovery's target.
[ "${3:-}" = / ] || { echo 'AutoPkg requires the running target OS.' >&2; exit 1; }
[ ! -e /var/db/.AppleSetupDone ] || {
    echo 'AutoPkg is for fresh macOS installation before Setup Assistant. Use the normal Graphics pkg on a configured system.' >&2
    exit 1
}
