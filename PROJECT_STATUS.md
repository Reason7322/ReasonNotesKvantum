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
