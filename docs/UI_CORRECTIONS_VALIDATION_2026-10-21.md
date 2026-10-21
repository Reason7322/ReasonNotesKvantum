# UI correction validation — 2026-10-21

## Scope

This bounded pass implements the two corrections requested after review of
checkpoint `eea23049762fb54ddd53c5f2479473bf7344308b`:

1. keep the sidebar splitter completely invisible at rest and on hover while
   retaining its drag target and persisted width; and
2. remove the dedicated horizontal rule below the title.

Font and Settings changes, physical Android testing, installed-candidate
replacement, and production cutover were deliberately out of scope.

## Implementation

- `src/reasonnotes_widgets/main_window.py` retains the real
  `QSplitterHandle`, its seven-pixel hit area, palette clearing, drag behavior,
  width limits, and persisted setting. The scoped proxy style now suppresses
  `CE_Splitter` artwork for the boundary handle in every state. The former
  three-dot hover painter and hover repaint plumbing were removed.
- `src/reasonnotes_widgets/editor_page.py` no longer constructs or inserts a
  `TitleRule`; the note body follows the title editor directly.
- Regression tests render the real boundary handle both while hovered and
  after leave, assert a fully transparent result, retain the synthetic drag
  assertion, and assert that no title-rule widget is present.

The source implementation was committed as
`d6d8aa4eadd159850e878b59cc439fff2fe20d49` before packaging so the tested
temporary release has an exact code identity.

## Automated validation

The two changed assertions were first observed failing against the prior
implementation: the hovered handle contained 36 painted pixels and the editor
still exposed `title_rule`. After the implementation:

- focused changed tests: **2/2 passed**;
- affected Widgets suites (`main_window`, `visual_polish`, `native_material`,
  and `i18n`): **34/34 passed**;
- complete isolated suite: **243/243 passed** in 7.875 seconds with
  `QT_QPA_PLATFORM=offscreen`, `QT_QPA_PLATFORMTHEME=qt6ct`, disposable
  HOME/XDG paths, and localhost access for the existing purge-relay tests.

The complete run emitted the already documented three-object uncollectable
Python/Qt shutdown warning after `OK`; no test failed.

## Built and launched

`scripts/install-candidate.py` created an immutable release only under
`/tmp/reasonnotes-ui-correction.i3X8lb`, compiled the native Wayland helper,
and created a temporary launcher. Source comparison, excluding generated
`__pycache__` and the compiled helper, was exact.

| Artifact | SHA-256 |
| --- | --- |
| native Wayland helper | `e7bb3e6269419810f884c8aa1294a9eba5ddb39e60d071e295cb54538a3e02c4` |
| temporary launcher | `934da4775180a6623dd4bd14ece42aff4f616fb1f982ac020059faaf9af2abc7` |

On Hyprland Workspace 10, the SHA-named package used copied qt6ct/Kvantum
configuration, copied synthetic notes, explicit disposable paths,
`--no-auto-receive`, `--kitty-window-material`, and a bounded runtime probe.
It reported:

```text
RUNTIME_STYLE=qt6ct-style
RUNTIME_PLATFORM=wayland
RUNTIME_BLUR_ACTIVE=1
RUNTIME_BLUR_ERROR=
RUNTIME_WINDOW_MATERIAL=kitty-equivalent
RUNTIME_PURGE_RELAY=disabled-for-probe
```

Hyprland reported a native, non-XWayland
`org.reasonnotes.ReasonNotesKvantum` client at `[0,46]`, size
`[2048,1106]` logical pixels. The preview exited with status 0, Workspace 2
was restored, and Workspace 10 was empty afterward.

## Visual inspection

The full-resolution captures are:

- [selected note](evidence/ui-corrections-2026-10-21/selected-note.png)
- [splitter hovered](evidence/ui-corrections-2026-10-21/splitter-hover.png)
- [title without rule crop](evidence/ui-corrections-2026-10-21/title-no-rule-crop.png)
- [divider at rest crop](evidence/ui-corrections-2026-10-21/divider-rest-crop.png)
- [divider hovered crop](evidence/ui-corrections-2026-10-21/divider-hover-crop.png)

Original-resolution inspection found no three-dot grip or other added
splitter artwork in the hover capture, and no dedicated rule widget below the
title. A pixel comparison over an 80×620 strip centered on the divider and
away from the pointer reported **0 differing pixels** between rest and hover.
The accepted layout, glass, editor sheet, controls, and sidebar hierarchy were
otherwise unchanged.

These captures are new evidence for Reason's visual review, not owner visual
acceptance.

## Isolation and remaining gates

The production launcher remains SHA-256
`05406228cadb43bcb6ad37be63d057d645c90e286a5ba8632c64d28c10e66eca`.
The relative-path/content manifest over all 404 production-data files remains
`d47802fa402edd0905cb28508ce806442e4e11f4345eeeecaa334807c5544890`.
Nothing was installed or deployed, and no production data, existing candidate,
Android device, KDE Connect state, or global desktop/theme configuration was
changed.

Product completion still requires owner visual acceptance, the separately
authorized physical Android interoperability sequence, and separately
authorized production migration/cutover/rollback verification.
