# Native Search Bar Design

## Intent

Make Search notes immediately recognizable as an input field while preserving
the approved LiquidGlass sidebar, alignment grid, dimensions, ordering, and
behavior.

## Approved approach

Paint Kvantum's complete native line-edit panel behind the separate search icon
and integrated `QLineEdit`. Use the normal state at rest and the focused state
only while the text field actually has focus. LiquidGlass owns the panel's
edge, interior color, and translucency; ReasonNotes supplies no replacement
color or opacity.

The theme's line-edit interior is non-opaque, so this adds recognizable input
depth without becoming an opaque slab. The existing embedded text field keeps
its `NoBrush` base and no frame, preventing a second panel from stacking above
the native surround.

## Rejected alternatives

- The always-focused clipped frame is rejected by the owner because it reads
  as a blue outline rather than a search bar.
- The normal clipped frame is too faint and still lacks input-field depth.
- Application-painted palette strokes or fills would imitate the theme rather
  than use its real line-edit component.

## Acceptance

Tests must prove a theme-painted but non-opaque center, normal-at-rest and
focused-on-focus native states, preserved alignment and search interaction,
and unchanged approved sidebar material. Owner review on Wayland remains the
visual acceptance gate.
