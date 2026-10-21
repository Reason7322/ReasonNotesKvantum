# Sidebar refinement validation — 2026-10-21

## Scope

The left sidebar was refined without changing note, synchronization, deletion,
Settings, search, selection, or navigation behavior. The notes list keeps its
existing row height, icon slot, spacing, selection behavior, and surrounding
layout.

The visual changes are limited to:

- a fill-free, cyan-accented New Note action;
- deterministic palette-owned Save, Sync, and Settings line icons;
- Settings directly below Sync and before the unchanged Delete action; and
- a cyan stacked-page glyph for ordinary note rows, derived from the
  ReasonNotes layered-note mark.

## Test evidence

The sidebar regressions were developed red-green. The rejected state failed
because New Note was still primary-filled, Settings remained below the notes
list, Save/Sync/Settings still depended on theme-named glyphs, and ordinary
notes had no accented pixels.

The affected widget surface passed 45/45. The final complete isolated suite
passed 250/250 in 9.557 seconds with offscreen Qt, copied qt6ct/Kvantum
configuration, disposable HOME/XDG roots, and localhost socket access for the
existing purge-relay tests. The run emitted the already documented deliberate
argument-parser output, duplicate-ZIP warning, and three-object Qt shutdown
ResourceWarning after `OK`; no test failed.

## Actual Wayland evidence

The candidate is running on Hyprland Workspace 10 with four disposable
synthetic notes. Hyprland reported class
`org.reasonnotes.ReasonNotesKvantum`, `xwayland=false`, position `[0,46]`, and
size `[2048,1106]` logical pixels. The application reported:

```text
RUNTIME_STYLE=qt6ct-style
RUNTIME_PLATFORM=wayland
RUNTIME_BLUR_ACTIVE=1
RUNTIME_BLUR_ERROR=
RUNTIME_WINDOW_MATERIAL=kitty-equivalent
RUNTIME_PURGE_RELAY=disabled-for-probe
```

The first disposable launch correctly exposed that isolated `XDG_DATA_HOME`
hid the installed YAMIS icon theme, so it was stopped before capture. The
review launch keeps candidate data isolated and exposes
`/home/reason/.local/share` read-only through `XDG_DATA_DIRS`; YAMIS therefore
loads in the real qt6ct/Kvantum context. Its missing inherited
Papirus-Dark/Cosmic theme warnings remain non-fatal, and the captured Delete
glyph retains its prior red treatment. Qt also emitted two repeated groups of
non-fatal `QColor::set*F: invalid value nan` warnings during style startup;
the runtime probe and rendering continued.

| Evidence | SHA-256 |
| --- | --- |
| `docs/evidence/sidebar-refinement-2026-10-21/sidebar-review.png` | `b5e9a8f10208ef7e4eafe800b9213de423df2e34f82912ea2bc13cff39e47428` |
| `docs/evidence/sidebar-refinement-2026-10-21/full-window.png` | `d1f42cfc1965f282a45ea32c63221f88d57aec4b36b737c85c33ffaa70aa0605` |

These captures establish native rendering and runtime provenance. Owner visual
acceptance of this sidebar iteration remains pending.

## Boundaries

No Android/device interaction, sync transfer, production installation,
production data access, global theme/configuration edit, compositor edit, or
`main` change occurred. The review window uses only `/tmp` data and copied
configuration. Android validation and production cutover remain stopped until
separately authorized.
