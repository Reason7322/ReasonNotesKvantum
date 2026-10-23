# Brighter Search Frame Design

## Intent

Make the resting Search notes edge visibly brighter while preserving the
owner-approved LiquidGlass sidebar, alignment grid, proportions, search
behavior, and unpainted center.

## Evidence and chosen approach

The active qt6ct/Kvantum chain paints identical normal, hover, and sunken
line-edit frames. Its native focused frame uses the same geometry but is
measurably brighter. `PE_FrameLineEdit` remains a no-op, so the existing
frame-only clipping of `PE_PanelLineEdit` is retained and the native focused
state is requested for the surround at rest.

This uses Kvantum's own focused line-edit artwork. It adds no color, opacity,
fill, shader, stylesheet, or global-theme change. The panel interior remains
outside the painter clip.

## Rejected alternatives

- A palette-light custom stroke would be application-owned styling rather
  than Kvantum's line-edit artwork.
- A wider panel clip would expose more of Kvantum's interior fill and risk an
  independently filled rectangle.
- Hover state cannot solve the baseline complaint because this theme paints
  hover identically to normal.

## Acceptance

Focused tests must show that the resting edge is brighter than Kvantum's
normal edge, matches its focused edge, leaves the center unchanged, and
preserves search interaction, Ctrl+F, layout, and accepted sidebar material.
Real Wayland appearance remains owner-reviewed.
