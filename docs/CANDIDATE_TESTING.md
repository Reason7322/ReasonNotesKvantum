# Candidate testing

The candidate is deliberately separate from the installed ReasonNotes release.
Its default data root is
`~/.local/share/ReasonNotesKvantum-candidate`; it rejects the production
`~/.local/share/ReasonNotes` tree even when that path is supplied explicitly.

## Install the candidate

From a clean `forge/qtwidgets-rewrite` checkout:

```sh
/usr/bin/python3 scripts/install-candidate.py
```

This builds the Wayland helper and creates only these candidate-owned paths:

- `~/.local/opt/reasonnotes-kvantum-candidate/releases/<git-sha>/`
- `~/.local/opt/reasonnotes-kvantum-candidate/current`
- `~/.local/bin/reasonnotes-kvantum-candidate`
- `~/.local/share/applications/org.reasonnotes.ReasonNotesKvantum.desktop`

It does not change `~/.local/bin/reasonnotes`, the production desktop entry,
or production notes. Existing versioned candidate releases are immutable and
will not be overwritten.

## Safe smoke test

Start from a terminal so diagnostic output remains visible:

```sh
~/.local/bin/reasonnotes-kvantum-candidate
```

Confirm the sidebar and editor resize naturally, keyboard focus is visible,
notes survive restart, F5 imports incoming test bundles, and the Sync and
Conflict surfaces behave correctly. Test only disposable candidate notes.

On Hyprland, compare the candidate with another native Kvantum application.
The application must report the `kvantum` style and should display compositor
blur when `ext-background-effect-v1` is available. An opaque native-palette
fallback is expected when the protocol or helper is unavailable. Loading the
style is not, by itself, visual acceptance.

Do not point `--root`, `--inbox`, or `--received-dir` at production paths.
The process rejects them, but the testing procedure should remain explicit.
