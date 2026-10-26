# Full-content synchronization page

## Intent

Make synchronization readable and focused. Clicking **Sync** keeps the approved
left sidebar visible but replaces the current editor or Settings content with a
full-width synchronization page. Long operation details must not be duplicated
into the narrow sidebar footer.

## Chosen approach

Use the existing main content page stack. Register the current Sync panel as a
normal content page beside the editor, Settings, and conflict page. Remember
which non-Sync page was visible before entry; the Sync close action restores
that page. This was chosen over stretching the existing drawer overlay because
stack navigation has simpler geometry, focus, and restoration behavior.

## Presentation

- Preserve the complete approved sidebar, including its material, alignment,
  controls, ordering, and dimensions.
- Keep the sidebar visible while synchronization is open.
- Give the Synchronize notes interface the entire content region to the right
  of the sidebar; Settings and note editing are not simultaneously visible.
- The sidebar footer shows only the translated synchronization state, such as
  `Phone: Idle`, `Phone: Running`, `Phone: Completed`, or `Phone: Error`.
- The full operation explanation, counters, progress, and actionable errors
  remain on the Sync page.
- Closing Sync restores the content page that was visible before Sync opened.

## Behavior and boundaries

Sync selection, transfer, durable confirmation, conflicts, note storage, and
KDE Connect behavior do not change. The approved LiquidGlass rendering and
editor appearance do not change. No Android, deployment, production data, or
global theme work is included.

## Verification

Focused widget tests will cover page replacement from editor and Settings,
restoration on close, concise footer text, full details on the Sync page, and
unchanged synchronization controls. A new isolated candidate may be prepared
after tests, but final appearance remains subject to Reason's Wayland review.
