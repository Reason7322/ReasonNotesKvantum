# Sync drawer redesign validation — 2026-10-21

## Scope

The rejected Sync layout was replaced without changing the controller,
presenter, sync protocol, Android interoperability code, note data, or
unrelated pages.

The drawer now has one connected hierarchy: title and close action, explicit
All-notes/Selected-notes scope, included-note presentation, transfer and
receipt meaning, live status, and a contextual primary action.

## Automated evidence

The complete suite passed 247/247 with:

- `QT_QPA_PLATFORM=offscreen`;
- copied qt6ct/Kvantum configuration under `/tmp`;
- isolated XDG data and state roots under `/tmp`;
- localhost socket access enabled for the foreground purge-relay tests.

The focused Sync-panel tests were developed red-green and cover mode
visibility, compact All-notes flow, contextual action labels and enablement,
dense note-card sizing, selection, unchanged asynchronous sync calls, and
running/completed status presentation.

## Actual Wayland evidence

Both states ran on Hyprland Workspace 10 using disposable synthetic notes and
reported:

```text
RUNTIME_STYLE=qt6ct-style
RUNTIME_PLATFORM=wayland
RUNTIME_BLUR_ACTIVE=1
RUNTIME_BLUR_ERROR=
RUNTIME_WINDOW_MATERIAL=kitty-equivalent
RUNTIME_PURGE_RELAY=disabled-for-probe
```

Exact drawer-surface captures:

| State | Evidence | SHA-256 |
| --- | --- | --- |
| All notes | `docs/evidence/sync-redesign-2026-10-21/all-notes-drawer.png` | `3caf735d8e10eb3b279d03ec0e7af04394e8442ef1b307e8fc1f0e6218dbba6b` |
| Selected notes | `docs/evidence/sync-redesign-2026-10-21/selected-notes-drawer.png` | `4f343e8ace00113fd8fd3dd87d389f17b8d2b80f429a531d5c5f291f96582c78` |

These captures establish rendering and runtime provenance. Reason visually
accepted the redesigned Sync drawer on 2026-10-21.

## Boundaries

No Android/device interaction occurred. The installed candidate, production
launcher, production data, global theme/configuration, and `main` were not
modified. Production cutover remains unauthorized.
