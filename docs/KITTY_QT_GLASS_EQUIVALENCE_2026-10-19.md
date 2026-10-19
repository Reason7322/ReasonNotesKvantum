# Kitty / Qt glass equivalence experiment — 2026-10-19

## Result

Yes. A minimal native Wayland Qt Widgets surface can reproduce Kitty's
translucent background pixels exactly under the same Hyprland conditions.

The Qt probe submitted one uniform framebuffer material:

```text
RGBA (28, 33, 33, 209) = #1C2121 at 81.96% alpha
```

All `1,640,000` raw framebuffer pixels had that exact value. In the matched
final captures, the 80 px inset region contained `1,245,600` pixels and Kitty
and Qt were byte-for-byte identical across every RGB channel.

The remaining full-window difference is not a different glass/compositor
result. It is Kitty's configured client-side `liquid-glass` shader around the
perimeter plus its terminal cursor. With the shader disabled through a
disposable Kitty configuration copy, the surface matched Qt everywhere except
one 38×49 software-cursor bounding box.

## Controlled conditions

- Hyprland Workspace 10 on monitor `DP-2`.
- Monitor: 2560×1440 physical pixels, scale 1.25.
- Both client windows: 1280×820 logical pixels at `(384, 164)`.
- Both client captures: 1600×1025 physical pixels.
- Same wallpaper, compositor settings, focus state, capture method, and
  window geometry.
- Kitty 0.49.2 used the normal user configuration read-only:
  `background #1c2121`, `background_opacity 0.82`, `background_blur 1`, and
  `custom_shaders liquid-glass`.
- Qt 6.11.2 used a plain `QWidget`, Fusion style, no controls, no card,
  gradient, palette autofill, or Kvantum painting.
- The Qt raw and composited captures were repeated with the ReasonNotes
  application-specific Wayland background-effect request enabled and omitted.
- Global Hyprland and Kitty configuration was not modified.

Workspace 10 was empty before the experiment and after all mission-owned
windows closed.

## Measurements

### Kitty versus Qt

| Region | Exact pixels | RGB MAE | Maximum channel difference |
| --- | ---: | ---: | ---: |
| 80 px inset | 100.000% | `(0, 0, 0)` | `(0, 0, 0)` |
| Full client | 96.066% | `(0.580, 0.535, 0.534)` | `(218, 215, 211)` |

The amplified full-client difference image confines the nonzero pixels to the
edge highlight/shadow bands described by Kitty's shader and the terminal
cursor. The shader source explicitly preserves the input alpha.

### Blur/background-effect isolation

The Qt client capture with its application blur request enabled is
byte-identical to the capture with the request omitted:

```text
8f495577c2e6dc14e89e2913d6625334458e5c64ef26f23a09655960d1b52636
```

Both raw images are also byte-identical. The request-enabled run reported
`QT_BLUR_ACTIVE=1`; the omitted run reported `QT_BLUR_ACTIVE=0`. Under the
active Hyprland policy, this request does not change the final pixels and is
not the source of the prior ReasonNotes difference.

### Relationship to the wallpaper

In the common inset region:

| Image | Luma range | Mean | Standard deviation | Correlation with wallpaper |
| --- | ---: | ---: | ---: | ---: |
| Wallpaper | 255.000 | 39.268 | 60.320 | 1.000000 |
| Kitty | 43.294 | 33.707 | 9.082 | 0.912021 |
| Qt | 43.294 | 33.707 | 9.082 | 0.912021 |

Kitty and Qt therefore receive the same blurred/transformed background and
composite it identically. The wallpaper comparison is descriptive rather than
a simple alpha-over model because the compositor blur deliberately changes the
underlying pixels before composition.

## Answers

### Can Qt reproduce Kitty's pixels?

Yes. A uniform Qt framebuffer of `#1C2121` at alpha 209 produced exact final
pixel equality throughout the shared interior.

### What measurable difference remains?

Only Kitty-specific client content: its custom edge shader and cursor. The
normal full-client captures differ in 64,518 of 1,640,000 pixels, concentrated
at those locations. There is no interior glass difference.

### Framebuffer or desktop composition?

The glass result is equivalent at both boundaries:

- Qt raw framebuffer: exactly the intended RGBA at every pixel.
- Final interior: exactly the same pixels as Kitty.
- Qt blur-request on/off: exactly the same final client image.

The small remaining full-window difference originates in Kitty's client-side
edge shader and cursor, not in Qt or desktop background composition.

### Specific ReasonNotes experiment to try next

Create a reversible ReasonNotes A/B variant that paints one continuous
top-level `QColor(28, 33, 33, 209)` sheet and does **not** invoke the native
Kvantum `PE_Widget` background. To preserve the accepted interface while
isolating this finding, first leave layout, controls, outlines, and behavior
unchanged, but bypass pane-sized translucent fills in that variant so the
large editor/background regions retain the proven Kitty-equivalent material.

That is a proposed next experiment, not an approved product change. It was not
implemented in this mission.

## Evidence

Full-resolution evidence is in
`docs/evidence/kitty-qt-equivalence-2026-10-19/`:

- `wallpaper.png` — empty Workspace 10 baseline.
- `kitty-desktop.png` and `kitty-client.png` — normal-config Kitty.
- `qt-blur-on-desktop.png`, `qt-client.png`, and `qt-raw.png` — matching Qt.
- `qt-no-request-client.png` — Qt without the application blur request.
- `kitty-no-shader-client.png` — disposable-config shader isolation.
- `kitty-vs-qt-side-by-side.png` — Kitty left, Qt right.
- `kitty-vs-qt-full-diff-8x.png` — amplified residual.
- `measurements.json` — captured comparison metrics.

Selected SHA-256:

```text
dd6e4dde1c13b9bd0da140caab81e19d1e7a97d1e9d5879ef2bb3080b8517312  kitty-client.png
8f495577c2e6dc14e89e2913d6625334458e5c64ef26f23a09655960d1b52636  qt-client.png
8f495577c2e6dc14e89e2913d6625334458e5c64ef26f23a09655960d1b52636  qt-no-request-client.png
1faff4a15606c7ce4f5785a29c2c502769156962225902af0c55534ffb1f4ecf  qt-raw.png
bf881247051cbc2d071bddc86e935839f1b845d2e6dcf28368dacb21830580ab  kitty-vs-qt-side-by-side.png
162f4cb48b4600febf20e1784f648c4769b1e464a7275cb491cfc135a04af396  kitty-vs-qt-full-diff-8x.png
7fd6a5be2de485800a33541dedc7c4b998061a99f188b21282d7b23d33a19384  wallpaper.png
```

## Boundaries and completion state

The disposable probe was not added to the application. No ReasonNotes source,
production installation, notes, Android state, theme, Kitty configuration, or
Hyprland configuration was changed. No candidate was built, installed, or
deployed.

**EXPERIMENT COMPLETE — OWNER DECISION REQUIRED BEFORE REASONNOTES CHANGES.**
The original product remains incomplete pending visual acceptance, physical
Android interoperability validation, and authorized production cutover.
