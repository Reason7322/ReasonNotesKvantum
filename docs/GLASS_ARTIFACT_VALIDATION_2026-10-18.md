# ReasonNotes glass artifact correction — 2026-10-18

## Change

The accepted UI structure is unchanged. The two lightest stops in the existing
palette-derived top-level material now use an alpha floor of 178. The gradient,
glass cards, navigation rail, controls, typography, splitter, and all backend
connections are unchanged.

A controlled Wayland comparison first replaced the top-level gradient with a
uniform sheet at the prior effective opacity. The same rectangular bands
remained in the same regions and crossed title/body widget boundaries. This
ruled out the child widget edges and gradient geometry. Raising only the
under-dense material stops masked the compositor blur tiles while retaining
visible background depth.

## Evidence

- New focused regression was observed failing at alpha 146 and 171 before the
  implementation, then passing with both exposed material points at or above
  178.
- Affected visual/main-window tests: 17/17 passed.
- Complete isolated suite: 227/227 passed in 7.469 seconds.
- Actual isolated Hyprland launches reported `qt6ct-style`, native `wayland`,
  active blur, and no blur-helper error.
- Normal 1280x820 editor and Settings captures were inspected. The formerly
  visible lower-editor rectangular bands were no longer distracting; the
  translucent background depth, writing-card separation, and Settings glass
  remained visible.

No production data, launcher, installed release, Android state, global theme,
or compositor configuration was modified.

**ENGINEERING CANDIDATE — UI VISUAL ACCEPTANCE PENDING.** Physical Android
interoperability and authorized production cutover remain outstanding.
