# Resources stay in Installer's temporary Scripts directory, not as installed payloads.
assets="$(/usr/bin/dirname "$0")/Assets"
for component in Common "$selected"; do
    [ -d "$assets/$component/Library" ] || {
        echo "AutoPkg resource missing: $component" >&2
        exit 1
    }
done
echo "WhateverXe AutoPkg: macOS $version, selected $selected"
for component in Common "$selected"; do
    library="$assets/$component/Library"
    for category in Extensions GPUBundles; do
        source="$library/$category"
        [ -d "$source" ] || continue
        /bin/mkdir -p "/Library/$category"
        for bundle in "$source"/*; do
            target="/Library/$category/${bundle##*/}"
            /usr/bin/ditto --norsrc --noextattr --noacl --noqtn "$bundle" "$target"
            /usr/sbin/chown -R root:wheel "$target"
        done
    done
done
