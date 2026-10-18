# ReasonNotesKvantum - Project Status

## Current milestone

Engineering candidate implemented on `forge/qtwidgets-rewrite`; owner visual
acceptance and authorization for production replacement remain pending.

## Implemented

- Native `QApplication`/`QMainWindow`/Qt Widgets shell with a resizable 300 px
  sidebar, responsive editor capped at a 920 px writing column, native search,
  selection, keyboard navigation, dialogs, Settings, Sync, and Conflict views.
- The system `qt6ct-style` proxy is preserved when it wraps the installed
  `kvantum` QStyle, matching Dolphin's native font, icon, palette, and style
  chain without changing or bundling system themes.
- Optional `ext-background-effect-v1` compositor blur on Qt's QWidget Wayland
  surface, including pre-show alpha preparation and an opaque fallback.
- Imported baseline application/sync logic with note CRUD, autosave/recovery,
  immutable history, Unicode search, F5 receive refresh, selective KDE Connect
  sync, receipts/retries, exact conflict resolution, and peer deletion purge.
- English and Polish native chrome, foreground purge pairing information, and
  application-scoped candidate settings.
- Versioned candidate packaging, immutable releases, candidate-only activation,
  and documented rollback. No production cutover has occurred.
- The reviewed candidate is installed at candidate-only paths with launcher
  `~/.local/bin/reasonnotes-kvantum-candidate`; production remains selected.

## Validation state

- Complete automated suite: 224 tests passed in an isolated offscreen run;
  localhost purge-relay tests were run with socket access enabled.
- Native helper: compiled successfully from the system Wayland protocol.
- Actual Hyprland session: Qt platform `wayland`, style `qt6ct-style` over
  Kvantum, compositor blur active with no helper error, using disposable
  `/tmp` data and configuration copies.
- Composited screenshot inspected after correcting the responsive writing
  column. It is evidence of the observed candidate, not owner visual approval
  or a claim of identity with Dolphin.
- Android/device mutation was not performed; protocol and KDE Connect behavior
  are covered by imported regression/integration tests. Owner device acceptance
  remains pending.

See `docs/VALIDATION.md` for commands, hashes, and separated evidence classes.

## Production state

The installed launcher, release, desktop entry, settings, Android app, and
`~/.local/share/ReasonNotes` data have not been replaced or migrated. The
candidate rejects production data paths.

## Current owner and next action

Forge owns the branch. The whole-branch review's six Important findings were
fixed through interaction-level RED/GREEN tests and the full suite is green.
The next action is owner visual/device acceptance through the candidate
launcher. Do not modify `main` or the production launcher without explicit
owner authorization.

## ChatGPT-owned visual correction (2026-10-18)

Owner rejected the post-4665147 wallpaper-portal appearance. Separate branch
sol/qtwidgets-glass-balance adds a system-palette translucent backdrop and
removes the Settings back button. The sidebar Settings button toggles.
Full suite 222/222 passed; native Wayland/Kvantum/blur runtime verified.
No installed candidate or production files changed. Owner visual acceptance,
physical Android acceptance, and production cutover remain pending.
See docs/GLASS_BALANCE_VALIDATION.md.

## Second visual design iteration — 2026-10-18

Owner rejected the first flat-gray material pass. The current sol-owned
continuation adds real UI hierarchy using the active Kvantum palette:
NavigationRail, GlassCard editor/Settings, grouped action/search surfaces,
themed title rule, improved spacing, consistent iconography, and localized
Notes heading. It preserves the existing backend and removes all separate
Settings back navigation. Full suite 223/223 passed. Real Wayland/Kvantum
and compositor blur verified, with visual screenshots inspected using
disposable test notes and dummy pairing credentials.

**PRODUCT INCOMPLETE:** owner has not approved visuals; physical Android
interoperability and authorized production cutover are still pending. No
installed candidate or production files were changed during this iteration.
See docs/GLASS_BALANCE_VALIDATION.md and handoffs/SOL_TO_FORGE.md.

## Forge visual recovery — 2026-10-18

Forge selectively integrated Sol's preferred-direction layout composition and
the verified Dolphin-native qt6ct integration. The rejected editor-wide
`QPalette.Base` autofill and flat native-frame replacement were not imported.
The current source keeps the low-alpha writing/settings cards, grouped sidebar
commands, search surround, title rule, and system icons, while all colors are
derived from the active system palette. The Settings back bar and appearance
explanation remain absent.

The complete 224-test suite passes. Two unobstructed 2048x1106 Hyprland
captures (editor and Settings) were inspected from isolated source launches;
both reported `qt6ct-style`, native Wayland, active blur, and no blur error.
The editor capture visibly retained background depth and a distinct readable
writing panel; the Settings capture retained the sidebar and two translucent
cards without a back button.

**ENGINEERING CANDIDATE — VISUAL ACCEPTANCE PENDING.** Physical Android
interoperability and production cutover remain pending. No production data,
launcher, theme, compositor configuration, or Android state was changed.
See `docs/VISUAL_RECOVERY_VALIDATION_2026-10-18.md`.
