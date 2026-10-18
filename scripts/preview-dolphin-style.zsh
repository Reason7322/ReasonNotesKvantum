#!/usr/bin/env zsh
# Isolated real-theme preview; no production or installed candidate changes.
set -eu
work="/home/reason/Temporary/ChatGPTProjects/ReasonNotesKvantum/worktrees/GlassBalance"
cfg="/home/reason/.config"
source_qt6ct="$cfg/qt6ct/qt6ct.conf"
source_kvantum="$cfg/Kvantum/kvantum.kvconfig"
if [[ ! -r "$source_qt6ct" || ! -r "$source_kvantum" ]]; then
  print -u2 "Active qt6ct/Kvantum config missing; refusing unthemed preview"
  exit 1
fi
theme=$(sed -n 's/^theme=//p' "$source_kvantum" | head -n1)
if [[ -z "$theme" || "$theme" == *"/"* || "$theme" == *".."* ]]; then
  print -u2 "Cannot safely resolve selected Kvantum theme"
  exit 1
fi
theme_root="$cfg/Kvantum/$theme"
if [[ ! -r "$theme_root/$theme.svg" || ! -r "$theme_root/$theme.kvconfig" ]]; then
  print -u2 "Active theme SVG or config missing: $theme"
  exit 1
fi
if [[ ! -r "$work/linux-app/native/libreasonnotes_wayland_blur.so" ]]; then
  print -u2 "Blur helper missing in separate source worktree"
  exit 1
fi
preview="/home/reason/Temporary/ChatGPTProjects/ReasonNotesKvantum/NativeQtPreview"
mkdir -p "$preview/config/qt6ct" "$preview/config/Kvantum/$theme" \
         "$preview/data" "$preview/cache" "$preview/repository" \
         "$preview/inbox" "$preview/received"
# Disposable CONFIG COPY so the preview still sees exact Dolphin settings.
cp -f "$source_qt6ct" "$preview/config/qt6ct/qt6ct.conf"
cp -f "$source_kvantum" "$preview/config/Kvantum/kvantum.kvconfig"
cp -f "$theme_root/$theme.svg" "$preview/config/Kvantum/$theme/$theme.svg"
cp -f "$theme_root/$theme.kvconfig" "$preview/config/Kvantum/$theme/$theme.kvconfig"
print "Using Dolphin's actual Qt platform and $theme appearance."
print "Disposable notes directory: $preview/repository"
cd "$work"
env XDG_CONFIG_HOME="$preview/config" \
    XDG_DATA_HOME="$preview/data" \
    XDG_CACHE_HOME="$preview/cache" \
    XDG_DATA_DIRS="/home/reason/.local/share:/home/reason/.local/share/flatpak/exports/share:/var/lib/flatpak/exports/share:/usr/local/share:/usr/share" \
    QT_QPA_PLATFORMTHEME=qt6ct \
    QT_QPA_PLATFORM=wayland \
    PYTHONPATH="$work/src" \
    /usr/bin/python3 "$work/linux-app/reasonnotes_widgets.py" \
    --root "$preview/repository" \
    --inbox "$preview/inbox" \
    --received-dir "$preview/received" \
    --no-auto-receive \
    --runtime-probe-ms 180000
