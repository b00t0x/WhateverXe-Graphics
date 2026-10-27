# Run after the Common and selected OS components, including their postinstall.
# Keep the receipt check before reboot so a component-ordering failure is visible.
major=$(/usr/bin/sw_vers -productVersion)
case "${major%%.*}" in
@OS_RECEIPTS@
    *) echo 'Unsupported AutoPkg target OS.' >&2; exit 1 ;;
esac
for part in Common "$component"; do
    receipt="org.b00t0x.WhateverXe.$part"
    installed=$(/usr/sbin/pkgutil --pkg-info-plist "$receipt" | /usr/bin/plutil -extract pkg-version raw -o - -)
    [ "$installed" = "$expected_version" ] || {
        echo "AutoPkg will not restart: $receipt is not version $expected_version." >&2
        exit 1
    }
done
[ -s /Library/KernelCollections/AuxiliaryKernelExtensions.kc ] || {
    echo 'AutoPkg will not restart: AuxiliaryKernelExtensions.kc is missing or empty.' >&2
    exit 1
}
echo 'WhateverXe Graphics installed. Restarting before Setup Assistant to load AuxKC.'
/bin/sync
/sbin/reboot
