#!/usr/bin/env zsh
# Launch an isolated Wayland preview using disposable copies of the currently
# selected qt6ct/Kvantum configuration. Production notes and settings are not
# addressable through this launcher.
set -eu

project_root="${0:A:h:h}"
system_config="/home/reason/.config"
source_qt6ct="$system_config/qt6ct/qt6ct.conf"
source_kvantum="$system_config/Kvantum/kvantum.kvconfig"

if [[ ! -r "$source_qt6ct" || ! -r "$source_kvantum" ]]; then
  print -u2 "Active qt6ct/Kvantum config missing; refusing unthemed preview"
  exit 1
fi

theme=$(sed -n 's/^theme=//p' "$source_kvantum" | head -n1)
if [[ -z "$theme" || "$theme" == *"/"* || "$theme" == *".."* ]]; then
  print -u2 "Cannot safely resolve selected Kvantum theme"
  exit 1
fi

theme_root="$system_config/Kvantum/$theme"
if [[ ! -r "$theme_root/$theme.svg" || ! -r "$theme_root/$theme.kvconfig" ]]; then
  print -u2 "Active theme SVG or config missing: $theme"
  exit 1
fi
if [[ ! -r "$project_root/linux-app/native/libreasonnotes_wayland_blur.so" ]]; then
  print -u2 "Blur helper missing; build the candidate before previewing"
  exit 1
fi

preview=$(mktemp -d /tmp/reasonnotes-kvantum-preview.XXXXXX)
mkdir -p "$preview/config/qt6ct" "$preview/config/Kvantum/$theme" \
         "$preview/data" "$preview/cache" "$preview/repository" \
         "$preview/inbox" "$preview/received"

# Disposable copies expose the same selected style without permitting the
# preview process to change the owner's live desktop configuration.
cp -f "$source_qt6ct" "$preview/config/qt6ct/qt6ct.conf"
cp -f "$source_kvantum" "$preview/config/Kvantum/kvantum.kvconfig"
cp -f "$theme_root/$theme.svg" "$preview/config/Kvantum/$theme/$theme.svg"
cp -f "$theme_root/$theme.kvconfig" "$preview/config/Kvantum/$theme/$theme.kvconfig"

print "Using system qt6ct and selected Kvantum theme: $theme"
print "Disposable preview root: $preview"
cd "$project_root"
env XDG_CONFIG_HOME="$preview/config" \
    XDG_DATA_HOME="$preview/data" \
    XDG_CACHE_HOME="$preview/cache" \
    XDG_DATA_DIRS="/home/reason/.local/share:/home/reason/.local/share/flatpak/exports/share:/var/lib/flatpak/exports/share:/usr/local/share:/usr/share" \
    QT_QPA_PLATFORMTHEME=qt6ct \
    QT_QPA_PLATFORM=wayland \
    PYTHONPATH="$project_root/src" \
    /usr/bin/python3 "$project_root/linux-app/reasonnotes_widgets.py" \
    --root "$preview/repository" \
    --inbox "$preview/inbox" \
    --received-dir "$preview/received" \
    --no-auto-receive \
    --runtime-probe-ms "${REASONNOTES_PREVIEW_MS:-180000}"
