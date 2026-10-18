# ReasonNotesKvantum - Project Status

## Current milestone

Engineering candidate implemented on `forge/qtwidgets-rewrite`; owner visual
acceptance and authorization for production replacement remain pending.

## Implemented

- Native `QApplication`/`QMainWindow`/Qt Widgets shell with a resizable 300 px
  sidebar, responsive editor capped at a 920 px writing column, native search,
  selection, keyboard navigation, dialogs, Settings, Sync, and Conflict views.
- Installed system `kvantum` QStyle is required and selected without changing
  the system theme or bundling application themes.
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

- Complete automated suite: 217 tests passed in an isolated offscreen run.
- Native helper: compiled successfully from the system Wayland protocol.
- Actual Hyprland session: Qt platform `wayland`, style `kvantum`, compositor
  blur active with no helper error, using disposable `/tmp` data.
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

## Native Dolphin theme investigation and continuation — 2026-10-18

An investigation of the actual running Dolphin process established the Qt
platform chain qt6ct-style -> Kvantum (LiquidGlass), Lato 11, YAMIS,
BreezeDark, and Hyprland native Wayland. This supersedes earlier assumptions
that selecting bare Kvantum was equivalent. Prior isolated previews had
inadvertently hidden system qt6ct/Kvantum config via an empty XDG_CONFIG_HOME.

The separate sol/qtwidgets-glass-balance continuation now preserves that
native platform/style proxy, lets Kvantum render its real PE_Widget window
material, uses its palette for the editor pane, and removes the handwritten
imitation glass/card/icon painters. The Language pane no longer discusses
theming. The Settings back button remains absent.

Latest source test: 224/224 PASS. Actual Wayland preview with disposable
copies of the system theme: qt6ct-style, active compositor blur, no blur
error. No Forge/installed candidate/production mutation. Owner visual
acceptance and physical Android interoperability remain pending. The
original full product deliverable is INCOMPLETE pending those gates.
See docs/DOLPHIN_NATIVE_THEME_2026-10-18.md.
