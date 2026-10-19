#!/bin/bash
# Standalone cleanup for all WhateverXe Graphics releases. Run with sudo.
set -euo pipefail
export PATH=/usr/bin:/bin:/usr/sbin:/sbin
[ "$EUID" -eq 0 ] || { echo 'Run with sudo.' >&2; exit 1; }

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

# Remove the components distributed by WhateverXe Graphics.
for name in AppleIntelTGLCompat AppleIntelTGLGraphics AppleIntelTGLGraphicsFramebuffer; do
    /bin/rm -rf "/Library/Extensions/$name.kext"
done
for name in AppleIntelTGLGraphicsGLDriver AppleIntelTGLGraphicsMTLDriver AppleIntelTGLGraphicsVADriver \
    XeCompilerAdapter XeMetalCompiler; do
    /bin/rm -rf "/Library/GPUBundles/$name.bundle"
done
/bin/rm -rf /Library/GPUBundles/XeOpenCL
feature=/Library/Preferences/FeatureFlags/Domain/CoreMedia.plist
if [ -f "$feature" ] && /usr/libexec/PlistBuddy -c 'Print :AllowOnePassMetalScaling:Enabled' "$feature" >/dev/null 2>&1; then
    /usr/libexec/PlistBuddy -c 'Delete :AllowOnePassMetalScaling:Enabled' "$feature"
fi
update_auxkc
for component in Common BigSur Monterey Ventura Sonoma Sequoia Tahoe; do
    id="org.b00t0x.WhateverXe.$component"
    if /usr/sbin/pkgutil --pkg-info "$id" >/dev/null 2>&1; then
        /usr/sbin/pkgutil --forget "$id"
    fi
done
echo 'WhateverXe graphics removed. Restart macOS.'
