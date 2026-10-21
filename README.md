# ReasonNotesKvantum

ReasonNotesKvantum is the native Qt Widgets replacement candidate for the
Fedora ReasonNotes desktop application. It uses `QApplication`, `QMainWindow`,
native item views/editors/dialogs, and the installed Qt 6 `kvantum` QStyle.
The currently selected system Kvantum theme remains authoritative; this
repository does not bundle or select White, Dark, or LiquidGlass themes.

The imported `reasonnotes_app` and `reasonnotes_sync` packages preserve the
existing immutable revision graph, recovery, KDE Connect transport, durable
receipts, bounded retries, conflict semantics, and foreground-only deletion
relay. Provenance is recorded in [docs/PROVENANCE.md](docs/PROVENANCE.md).

## Run from the worktree

Fedora dependencies include Python 3.14, PySide6 6.11, the Qt 6 Kvantum style
plugin, a C compiler, `wayland-scanner`, and Wayland client development files.

```sh
/usr/bin/python3 scripts/build-wayland-blur.py --target linux-app/native
/usr/bin/python3 linux-app/reasonnotes_widgets.py
```

The source entry point defaults to
`~/.local/share/ReasonNotesKvantum-candidate` and rejects the protected
production `~/.local/share/ReasonNotes` tree. Incoming KDE Connect bundles are
read from `~/Downloads`, matching the established desktop application; use an
explicit `--received-dir` for isolated fixture runs.

## Install the isolated candidate

```sh
/usr/bin/python3 scripts/install-candidate.py
~/.local/bin/reasonnotes-kvantum-candidate
```

Candidate releases, launcher, desktop entry, settings, and data all have
distinct names. The installer does not replace `~/.local/bin/reasonnotes` or
modify the installed production release. See
[candidate testing](docs/CANDIDATE_TESTING.md) and
[cutover/rollback](docs/CUTOVER_AND_ROLLBACK.md).

## Test

```sh
QT_QPA_PLATFORM=offscreen PYTHONPATH=src \
  /usr/bin/python3 -m unittest discover -s tests -v
```

Current validation evidence, including the actual Hyprland/Wayland probe, is
in [docs/VALIDATION.md](docs/VALIDATION.md).
