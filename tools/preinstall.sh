# Installer passes the target volume as its third argument.
[ "${3:-/}" = / ] || { echo 'Boot the target macOS before installing.' >&2; exit 1; }
for name in AppleIntelTGLCompat.kext AppleIntelTGLGraphics.kext AppleIntelTGLGraphicsFramebuffer.kext \
    AppleIntelTGLGraphicsGLDriver.bundle AppleIntelTGLGraphicsMTLDriver.bundle AppleIntelTGLGraphicsVADriver.bundle; do
    [ ! -e "/System/Library/Extensions/$name" ] || {
        echo 'Remove the old System Xe patch using its recovery procedure first.' >&2
        exit 1
    }
done
