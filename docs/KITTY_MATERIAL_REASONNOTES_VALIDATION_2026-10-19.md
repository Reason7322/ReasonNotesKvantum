# ReasonNotes Kitty-equivalent glass A/B — 2026-10-19

## Original deliverable
A complete, visually accepted native Qt Widgets/Kvantum ReasonNotes replacement preserving the approved UI, note CRUD, autosave, history, KDE Connect/Android synchronization, conflict/deletion handling and English/Polish. Owner approved this narrow reversible visual experiment, not production deployment or global theme refinement.

## Implemented
The existing custom renderer stays the default. The hidden, mutually exclusive --kitty-window-material variant renders a single QColor(28,33,33,209) top-level sheet with CompositionMode_Source, skips additional translucent rail and GlassCard fills while retaining their outlines, and preserves ordinary native Kvantum controls. The earlier --native-window-material switch remains available. Changed: linux-app/reasonnotes_widgets.py, src/reasonnotes_widgets/main_window.py, src/reasonnotes_widgets/material.py, tests/test_widgets_native_material.py.

## Tests
- Focused unittest discovery: 6/6 passed.
- Full unittest discovery, offscreen Qt and source PYTHONPATH: 233/233 passed in 7.085 seconds.
- git diff --check passed.
- Non-fatal QColor invalid value nan and Python garbage-collection shutdown warnings occurred; attribution was not established.

## Actual Wayland preview
Each variant ran from source on DP-2 / Hyprland Workspace 10 with separate disposable repositories and XDG configurations, --no-auto-receive and --runtime-probe-ms 5500. Both reported qt6ct-style, native Wayland, blur active without error, foreground purge relay disabled, and clean exit code 0. The displayed window was at [0,46], size [2048,1106] logical. Original workspace 1 was restored. No installed candidate, production notes, phone, global theme or compositor configuration was modified.

The captures are in docs/evidence/kitty-reasonnotes-material-2026-10-19. The approved sidebar/editor layout and controls remain recognizable. The Kitty variant is substantially darker and flatter; broad wallpaper-derived regions are still visible. This is NOT owner visual acceptance and does NOT demonstrate elimination of the rectangular artifacts.

Coarse non-masked desktop sample from physical x=850..2000, y=550..1010:
- Current editor: column luma mean 41.996, std.dev. 4.410, range 24.996.
- Kitty editor: column luma mean 29.636, std.dev. 3.995, range 26.703.
These descriptive measurements include some application content, and are not a clean blank-glass alpha measurement.

## Completion classes
- Coded: reversible mode, optional material fills, new focused tests.
- Tested: focused 6/6, full 233/233.
- Built: no distributable package.
- Deployed: no candidate or production installation changed.
- Verified in live app: both source variants launched and exited on native Wayland; dark/flat new mode did not conclusively fix wallpaper patches.
- Physical Android/device interoperability: NOT tested.

PRODUCT INCOMPLETE. Preserve both modes and get owner visual assessment of the A/B before choosing another rendering adjustment. Remaining product gates are visual acceptance, physical Android interoperability and separately authorized cutover. No next mission or renderer promotion is authorized by this checkpoint.
