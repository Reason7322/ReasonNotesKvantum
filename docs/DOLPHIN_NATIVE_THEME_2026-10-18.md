# Dolphin's real theme chain and ReasonNotes native-style pass
Date: 2026-10-18, M A C H I N E

## Original unchanged product goal

Deliver a fully functional, visually accepted ReasonNotes native Qt Widgets
desktop replacement which follows the installed system Kvantum theme, retains
editing/history/search and KDE Connect sync semantics with Android, and never
modifies installed production without explicit owner authorization.

This is an engineering continuation, NOT final visual approval or production
cutover. The Android application is unchanged.

## Verified locally: Dolphin environment

A live Dolphin process (Dolphin 26.08.1 on Fedora 44) used:
- QT_QPA_PLATFORMTHEME=qt6ct and native Wayland.
- Loaded /usr/lib64/qt6/plugins/platformthemes/libqt6ct.so.
- Loaded /usr/lib64/qt6/plugins/styles/libkvantum.so.
- qt6ct.conf: style=kvantum, color scheme BreezeDark.colors,
  custom_palette=true, general font Lato 11, icon_theme=YAMIS.
- ~/.config/Kvantum/kvantum.kvconfig: theme=LiquidGlass.
- The selected installed LiquidGlass SVG/kvconfig are under
  ~/.config/Kvantum/LiquidGlass/.
- LiquidGlass.kvconfig sets composite=true, translucent_windows=true,
  blurring=false, base.color=#2a2f32B8, window.color=#1c2021.
  Its window-normal SVG element has opacity .72; controls and views have
  separately defined elements.
- Hyprland global decoration blur enabled, size=10, passes=3, vibrancy=.1696.

In a separate, clean Qt Widgets probe initialized with the matching qt6ct
configuration, the Qt application style was exactly:
  Qt6CTProxyStyle (objectName qt6ct-style)
  -> baseStyle Kvantum::Style (objectName kvantum)
The probe used Lato 11 and YAMIS, and a native Wayland compositor blur attach
succeeded. Drawing the installed style's PE_Widget primitive yielded actual
theme-sourced semi-transparent pixels.

What this does NOT prove: that Dolphin and ReasonNotes use identical
Dolphin-specific KDE widgets or paint paths; direct per-child inspection of
Dolphin internals was not performed. Native QWidget controls by themselves
are not a complete visual replica of Dolphin. The theme engine, fonts, colors,
icons, and compositor affect appearance, while app layout/widgets also matter.

## Critical test-environment correction

Older isolated previews set XDG_CONFIG_HOME to an empty temporary directory.
That hid qt6ct and the selected Kvantum theme settings from the test program.
Thus running the Kvantum plugin did NOT mean those screenshots reflected the
user's active LiquidGlass/qt6ct setup.

A repeatable test launcher now copies the actual selected qt6ct and Kvantum
configuration into a disposable config directory before launching. Only test
copies are made; no system files are edited or bundled with the app.

## This source pass (ChatGPT-owned)

- Preserve the system Qt6CTProxyStyle when its base is Kvantum; use explicit
  bare Kvantum only as a fallback if the system proxy does not provide it.
- Paint the top-level with the installed style's PE_Widget window primitive
  rather than application-defined wallpaper gradients.
- Use the real Qt/Kvantum palette Base brush for the reading pane and native
  QFrame construction for its other surfaces. Remove handwritten decorative
  card/rail/search/title gradients.
- Use system icon-theme pixmaps (YAMIS when active) rather than custom icon
  paintings; preserve the native Qt widget controls.
- Keep the intentional transparent line edit workaround; proxy it through
  the actual current Qt style, not forced bare Kvantum, so dark panel slabs
  do not return.
- Remove the unrelated appearance explanation from the Language settings.
  No separate appearance chooser and no Settings back button.
- Preserve NoteService, presenter/controller, sync, receipt, conflict, delete,
  autosave, F5, and Android protocol source unchanged.

## Tests / build / runtime / deployment

1. Source: updated layout/bootstrap/style code on the separate
   sol/qtwidgets-glass-balance worktree only.
2. Automated tests: 224/224 PASS in 7.243 s with
   QT_QPA_PLATFORM=offscreen PYTHONPATH=src
   /usr/bin/python3 -m unittest discover -s tests -q.
   Added a subprocess regression ensuring qt6ct-style is preserved over
   the Kvantum base style. Existing offscreen fallback tests passed.
3. Build: no new production/app package build. The previously compiled native
   Wayland helper in this ChatGPT worktree was reused.
4. Actual Wayland: bounded live probes with a copied (not modified) Dolphin
   theme configuration and disposable notes reported qt6ct-style, platform
   wayland, blur active=1, and empty blur error. Screenshots inspected for
   the native style/layout. The separate preview launcher was smoke-tested
   for 8 seconds; timeout exit 124 was intentional because the normal preview
   lasts 180 seconds.
5. Deployment: none. Production and the previously installed candidate were
   not changed. No physical Android interaction or data migration occurred.

Warnings: intermittent Qt QColor nan warnings and Python shutdown
ResourceWarning (3 uncollectable objects) were observed while tests passed.
Not investigated or claimed resolved here.

## Open work and acceptance

- Owner visually reviews this pass, ideally side-by-side with Dolphin and
  real wallpaper; no claim of visual acceptance is made here.
- Functional physical Android interoperability must be validated separately.
- Explicit approval is required before replacing production. Forge retains
  the primary engineering branch; this sol branch is a separate checkpoint.
