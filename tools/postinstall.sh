[ "${3:-/}" = / ] || exit 1
major=$(/usr/bin/sw_vers -productVersion)
if [ "${major%%.*}" = 26 ]; then
    feature=/Library/Preferences/FeatureFlags/Domain/CoreMedia.plist
    /bin/mkdir -p "${feature%/*}"
    if ! /usr/libexec/PlistBuddy -c 'Print :AllowOnePassMetalScaling' "$feature" >/dev/null 2>&1; then
        /usr/libexec/PlistBuddy -c 'Add :AllowOnePassMetalScaling dict' "$feature"
    fi
    if /usr/libexec/PlistBuddy -c 'Print :AllowOnePassMetalScaling:Enabled' "$feature" >/dev/null 2>&1; then
        /usr/libexec/PlistBuddy -c 'Set :AllowOnePassMetalScaling:Enabled false' "$feature"
    else
        /usr/libexec/PlistBuddy -c 'Add :AllowOnePassMetalScaling:Enabled bool false' "$feature"
    fi
fi
update_auxkc
