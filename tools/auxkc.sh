# Shared at build time; no helper is installed on the target.
update_auxkc() {
    local major work kext
    major=$(/usr/bin/sw_vers -productVersion)
    major=${major%%.*}
    /bin/mkdir -p /Library/KernelCollections
    work=$(/usr/bin/mktemp -d /Library/KernelCollections/.WhateverXe.XXXXXX)
    trap "/bin/rm -rf -- '$work'" EXIT
    local args=(create -n aux -x -z -V release -r /Library/Extensions)
    if [ "$major" -ge 13 ]; then args+=(--allow-missing-kdk); fi
    for kext in /Library/Extensions/*.kext; do
        [ -d "$kext" ] && args+=(-p "$kext")
    done
    /usr/bin/kmutil "${args[@]}" \
        -B /System/Library/KernelCollections/BootKernelExtensions.kc \
        -S /System/Library/KernelCollections/SystemKernelExtensions.kc \
        -A "$work/AuxiliaryKernelExtensions.kc" --no-authentication
    /bin/chmod 0644 "$work/AuxiliaryKernelExtensions.kc"
    /bin/mv -f "$work/AuxiliaryKernelExtensions.kc" /Library/KernelCollections/AuxiliaryKernelExtensions.kc
    /bin/rm -rf "$work"
    trap - EXIT
}
