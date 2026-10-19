# Distributed separately from the pkg; run the generated standalone script as root.
[ "$EUID" -eq 0 ] || { echo 'Run with sudo.' >&2; exit 1; }
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
    if /usr/sbin/pkgutil --pkg-info "$id" >/dev/null 2>&1; then /usr/sbin/pkgutil --forget "$id"; fi
done
echo 'WhateverXe graphics removed. Restart macOS.'
