# ReasonNotes glass artifact diagnosis — 2026-10-18

## Superseded attempt

Commit `8eb91e17654e33bac783340a82633fdc86a33c43` raised two
top-level gradient alpha values and added an alpha-floor test. Owner testing
showed no meaningful visual improvement. That attempt is recorded as
**FAILED VISUAL ACCEPTANCE**; its test did not exercise the visible defect.

## Controlled A/B diagnosis

An isolated Wayland preview used the same disposable notes, system-theme copy,
window geometry, and backdrop for three captures:

1. normal application-specific compositor blur;
2. the same translucent window without the application blur request and
   without the opaque fallback; and
3. the Qt-painted window captured directly with `QWidget.render()` before
   compositor processing.

The compositor captures with and without the application blur request were
pixel-identical in the matched window region. The two raw Qt framebuffers were
also pixel-identical. More importantly, the repeated rectangular bands were
already present in the raw Qt framebuffer, fixed in widget coordinates.

Sampling the exposed top-level strip found 44 long runs of identical RGBA
values (four or more consecutive pixels). The shallow, window-sized
`QLinearGradient` was being quantized into wide equal-color runs in the 8-bit
Qt backing store. Translucent child surfaces made those runs easier to see,
but neither the children nor Hyprland blur created them.

## Correction

Only the top-level sheet was changed. It now uses one palette-derived
translucent color (`Base.lighter(108)`, preserving the original 0.93 alpha
factor) instead of a low-contrast spatial gradient. This does not raise the
opacity, add noise, change compositor behavior, or alter the accepted layout.
The local `GlassCard` and navigation-rail materials continue to provide the
visual hierarchy and depth.

The regression now renders the real window and checks the exposed material
strip for the repeated long-run pattern. It failed against the rejected
gradient with 44 long runs and passes against the uniform top-level sheet.

## Evidence

- Affected visual/main-window tests: 17/17 passed.
- Complete isolated suite: 227/227 passed in 6.900 seconds.
- Actual isolated Hyprland launches reported `qt6ct-style`, native `wayland`,
  active blur, and no blur-helper error.
- Matching 1280x820 editor and Settings captures were inspected at full
  resolution. The repeated top-level bands visible in the control capture were
  absent, while the sidebar/editor cards and translucent depth remained.
- Preview windows were closed normally after capture.

No production data, launcher, installed release, Android state, global theme,
or compositor configuration was modified.

These observations establish an engineering candidate, not owner acceptance.
Reason must still judge the rendered result on the target desktop.

**ENGINEERING CANDIDATE — UI VISUAL ACCEPTANCE PENDING.** Physical Android
interoperability and authorized production cutover remain outstanding.
