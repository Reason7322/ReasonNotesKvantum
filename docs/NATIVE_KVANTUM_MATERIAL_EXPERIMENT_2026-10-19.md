# Native Kvantum window-material experiment — 2026-10-19

## Outcome

The installed Kvantum style can paint the complete ReasonNotes top-level
widget, but its native `PE_Widget` window sheet is not a suitable replacement
for the current ReasonNotes material under the selected LiquidGlass theme.

The native sheet reduced the visible desktop-coordinate patches, but did so by
becoming nearly opaque. In the blank editor sample, effective raw alpha rose
from a mean of `193.524` to `239.703`. The final image became a flat charcoal
surface and lost most of the accepted glass depth. This is an opacity tradeoff,
not evidence that native Kvantum painting supplies a smoother translucent blur.

The current renderer therefore remains the default. A hidden, source-only
`--native-window-material` switch preserves the native implementation as a
reversible comparison variant. No installation or theme setting was changed.

**ENGINEERING EXPERIMENT COMPLETE — OWNER VISUAL ACCEPTANCE PENDING.**

## Paint ownership and implementation

Before this experiment, `ReasonNotesMainWindow.paintEvent()` owned the
top-level material. `prepare_translucent_surface()` only enabled the alpha
surface; it did not cause Kvantum to paint a window background. The helpers in
`visuals.py` remove opaque editor/input bases, and `material.py` paints the
existing local rail/card hierarchy, but neither paints the whole window.

A direct primitive probe against the active `qt6ct-style → Kvantum` chain
showed:

- `PE_Widget`: a uniform center material with alpha `234`;
- `PE_FrameWindow`: edge decoration only, with a transparent center.

Removing the custom `paintEvent()` alone would therefore not be a valid native
implementation. The experiment explicitly clears the damaged alpha region and
asks the active style to draw `PE_Widget`. The accepted custom path is retained
unchanged and remains selected unless the hidden diagnostic flag is supplied.

Changed source:

- `src/reasonnotes_widgets/main_window.py` — reversible native primitive path;
- `linux-app/reasonnotes_widgets.py` — hidden diagnostic switch and runtime
  material report;
- `tests/test_widgets_native_material.py` — verifies explicit delegation and
  entry-point wiring.

## Controlled A/B

Both variants used:

- native Wayland on Hyprland Workspace 10;
- the same 1280×820 logical geometry at `(384, 166)`;
- the same 1600×1025 physical capture rectangle;
- byte-identical synthetic note content;
- separate disposable repository and XDG config/data/cache roots;
- disposable copies of the selected qt6ct and LiquidGlass configuration;
- `qt6ct-style`, active compositor blur, and no blur-helper error; and
- runtime-probe mode, which disables the foreground peer-purge relay.

Both processes exited normally with status 0. Production data, the installed
candidate, global theme configuration, and Hyprland configuration were not
accessed for writing.

## Automated validation

- Native-material focused tests: 2/2 passed.
- Affected main-window, visual, Wayland, and bootstrap coverage: 31/31 passed.
- Complete isolated suite: 229/229 passed in 6.895 seconds when granted the
  localhost socket access required by the foreground purge-relay tests.

The first sandboxed full-suite attempt ran all 229 tests but reported five
`PermissionError` setup errors because socket creation was prohibited. The
same five tests passed in the permitted rerun; this was an execution-environment
restriction, not an application failure.

## Framebuffer and compositor measurements

The common blank-editor region was physical x `560..1479`, y `560..929`.
It excludes text, pointer, and card edges.

| Variant | Raw alpha | Raw luma mean | Broad composited column range | Broad column std. dev. |
| --- | ---: | ---: | ---: | ---: |
| Current default | 192–195, mean 193.524 | 47.821 | 10.461 | 2.054 |
| Native Kvantum | 239–240, mean 239.703 | 30.966 | 2.668 | 0.529 |

Both raw editor regions were horizontally uniform after a 32 px box blur, so
neither path introduced a new tiled framebuffer pattern. The native final
capture attenuated the wallpaper-derived variation by about 75%, but its raw
surface opacity increased from about 76% to about 94% after the writing-card
layer. That density explains the attenuation.

The existing isolated Kitty optical reference reports
`background_opacity 0.82` and shows a subtle continuous blue-gray background
field. It is not a pixel-matched application capture, so it is used only as an
optical reference. The native ReasonNotes result is visibly darker and flatter
than that reference and than the accepted current ReasonNotes composition.

## Visual inspection

At original resolution:

- the current path retained the approved sidebar/editor hierarchy and visible
  background depth, including the already-documented desktop-coordinate
  regions;
- the native path retained layout, controls, text, and card boundaries;
- the native path made the regions much less visible, but the window read as an
  almost opaque charcoal slab rather than LiquidGlass; and
- no new crash, paint corruption, control breakage, or shutdown fault was
  observed.

The matched side-by-side image places the current renderer on the left and the
native Kvantum renderer on the right.

## Evidence

Full-resolution files are in
`docs/evidence/native-kvantum-material-2026-10-19/`:

- `current-composited.png`
- `current-raw.png`
- `native-composited.png`
- `native-raw.png`
- `current-vs-native.png`
- `kitty-reference-desktop.png`

SHA-256:

```text
fcb0632f3a3eee13ef2eb083bdaca8ced18a26c8642eca9c0e48cfb16a591b79  current-composited.png
b61811aa21181a35f85d9acc523c861df1cce7d7c7a07105bf4e5d1163eceb35  current-raw.png
75960f95a96e8eac1c8f3dbddec20bea53bb4c42b0e8e66bffd26cac1471e246  current-vs-native.png
4f226f89dbb41eb2f583e17b8ca1d9bdaff107267456f8fec51df09ea2ad003f  kitty-reference-desktop.png
6347fa0f9124d38edcbdc9631b37875a4d368817c651bf27f26ca644febef3a1  native-composited.png
46c3a828aae0d5d719932e9cc36a78f9e54673c95de0a874b5f45628a2b0e776  native-raw.png
```

## Decision

Native Kvantum window painting is technically supported and now reproducible,
but it does not improve the rectangular-patch problem while preserving the
requested translucent appearance. Promoting it would silently choose the
previously rejected higher-density tradeoff. The experiment therefore stops
with the current rendering path unchanged by default.

The original product objective remains unchanged. Owner visual acceptance,
physical Android interoperability, and explicit production cutover
authorization are still required.
