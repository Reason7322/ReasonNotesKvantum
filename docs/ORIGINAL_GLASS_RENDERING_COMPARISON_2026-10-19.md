# Original Qt Quick vs Qt Widgets glass comparison — 2026-10-19

## Outcome

The original Qt Quick application does not suppress the reported
screen-fixed background regions more effectively than the current Qt Widgets
candidate. Under matched geometry, the current writing card reduced broad
horizontal luminance variation from `14.143` to `12.320`.

A temporary Widgets prototype reproduced the original QML material arrangement:
one continuous editor sheet at alpha 184, the original low-alpha sidebar tint,
and no card fill. Its raw editor framebuffer matched the original alpha exactly,
and its final composited variation and transition measurements matched the
original exactly. The only raw material difference in the sampled editor was a
one-level blue-channel rounding difference.

This establishes that Qt Quick scene-graph rendering versus Qt Widgets backing
store painting is not the material cause. When the two architectures submit the
same translucent sheet, Hyprland produces the same optical result. Promoting the
prototype would make the reported background variation stronger and would
remove part of the accepted writing-surface depth, so no product rendering code
was changed.

**INCOMPLETE — OWNER VISUAL DECISION REQUIRED.**

## Isolation and controlled environment

All windows and captures used Hyprland Workspace 10 on `DP-2` only.

- Physical monitor: 2560×1440, scale 1.25.
- Workspace 10 was empty before the first launch and after cleanup.
- Sequential comparison geometry: 1280×820 logical pixels at `(384, 166)`.
- Resulting window captures: 1600×1025 physical pixels.
- Side-by-side geometry: original at `(24, 166)`, candidate at `(1044, 166)`,
  both 980×820 logical pixels.
- Both applications used disposable copies of the selected `qt6ct` and
  `LiquidGlass` configuration.
- Separate disposable XDG config/data/cache directories, repositories,
  inboxes, and received directories were used.
- Three synthetic notes were created once and the repository was copied so
  both applications read byte-identical content.
- Device discovery was suppressed with a dummy device ID, automatic receiving
  was disabled, and the original foreground purge relay was replaced by a
  temporary no-op diagnostic object. No live peer communication occurred.

Production notes, settings, launchers, installed releases, theme files, and
Hyprland configuration were not modified.

## Runtime facts

Original installed Qt Quick release:

- Qt platform: `wayland`.
- Qt Quick Controls style: `fusion`.
- Native compositor blur: active.
- Blur helper error: empty.
- Purge relay: disabled by the temporary wrapper.
- The installed historical helper exited with SIGSEGV when the comparison
  window was closed. This is the already-known teardown defect in that old
  release; the installed files were not changed.

Current Qt Widgets source:

- QApplication style: `qt6ct-style`, with the verified Kvantum base style.
- Qt platform: `wayland`.
- Native compositor blur: active.
- Blur helper error: empty.
- Purge relay: disabled by runtime probe mode.
- Clean exit status: 0.

## Measured framebuffer and compositor results

The measurement region was the same blank editor rectangle in every matched
1600×1025 capture: physical x `560..1479`, y `560..929`. It excludes text,
the pointer, and card edges.

| Rendering | Raw alpha | Broad-column std. dev. | Broad-column range |
| --- | ---: | ---: | ---: |
| Original QML | 184, uniform | 2.955 | 14.143 |
| Current Widgets | mean 193.524, range 192–195 | 2.587 | 12.320 |
| Widgets with original QML composition | 184, uniform | 2.955 | 14.143 |

At the previously identified screen-fixed transition columns, the composited
luminance deltas were:

| Rendering | local x=612 | local x=998 |
| --- | ---: | ---: |
| Original QML | -0.719 | +0.219 |
| Current Widgets | -0.642 | +0.186 |
| Widgets with original QML composition | -0.719 | +0.219 |

The original raw QML editor was uniformly `(47, 58, 61, 184)`. The prototype
Widgets editor was uniformly `(47, 58, 62, 184)`. Comparing their final blank
editor regions gave channel MAE `0.333333`, maximum channel error `1`, and
exact equality for two thirds of channels. Their measured spatial variation
was identical.

The current Widgets raw editor contains the deliberate writing-card layer:
alpha `192..195` across the sampled region. That additional material is why it
attenuates the desktop-derived pattern slightly more strongly than the original
single alpha-184 sheet.

## Interpretation

The original app reads the Noctalia-generated `LiquidGlass.kvconfig` palette
directly and paints its own QML material. It does not render the Kvantum
QWidget SVGs; the runtime Qt Quick Controls style was Fusion. The replacement
instead retains the real `qt6ct-style → Kvantum` widget chain and derives its
composition colors from that native palette.

The controlled prototype proves that this style-chain difference does not
prevent Widgets from reproducing the original optical sheet. Once the source
RGBA material is matched, the compositor result is matched. Conversely, the
large regions are not generated by the QML or Widgets renderer: they are the
same desktop-coordinate background variation passed through the same
translucent material and compositor.

The original can look calmer as a design because it has one uninterrupted
editor plane and no large card boundary. That is a hierarchy/perception
difference, not evidence that its renderer removes the background patches.
Removing the current card fill reproduces the original but increases measured
background variation and weakens the already-approved distinct writing region.

## Evidence

Full-resolution captures are in
`docs/evidence/original-glass-comparison-2026-10-19/`:

- `original-qml-matched.png` — original at controlled geometry.
- `widgets-current-matched.png` — current candidate at identical geometry.
- `workspace10-side-by-side.png` — original left, candidate right.
- `original-qml-raw.png` — raw QQuickWindow framebuffer.
- `widgets-current-raw.png` — raw QWidget framebuffer.
- `widgets-qml-material-prototype-matched.png` — temporary composition probe.
- `widgets-qml-material-prototype-raw.png` — its raw framebuffer.

SHA-256:

```text
3d24bca3ffa2549fbb71f57dfb36dce3588787e41a6c02463ebdd998a93e6a04  original-qml-matched.png
5d0e6a4e71aac1359e009beb523d94f1bcca88deefa61a1b77bb0299d0f32679  original-qml-raw.png
da9d38e6b9c32fec524554305fb5da34f61595117aa67e7aaac931ed21fc7dc3  widgets-current-matched.png
b61811aa21181a35f85d9acc523c861df1cce7d7c7a07105bf4e5d1163eceb35  widgets-current-raw.png
d543e5e3cf2738f0128832a80d543fd9088021d04764e8eea7dfb8552a02859d  widgets-qml-material-prototype-matched.png
041e6754b878ded053a9901d1fa6ade9d45886facb96dbb3739013969540c000  widgets-qml-material-prototype-raw.png
1af225a9d0a590d9ac029a52a090559be7e59af2d3d7ab97fb2e5dcf6b1a31de  workspace10-side-by-side.png
```

## Decision boundary

There is no evidence-supported renderer substitution to commit. The remaining
choice is visual and product-level:

1. Keep the current native writing card, which measurably attenuates the
   background variation more than the original.
2. Adopt the original uninterrupted plane for its visual continuity while
   accepting measurably stronger background variation and reduced card depth.
3. Increase material density or alter compositor policy, which remains the
   previously documented translucency/blur tradeoff.

No option was silently selected in this checkpoint. Owner visual acceptance,
physical Android interoperability, and authorized production cutover remain
pending.
