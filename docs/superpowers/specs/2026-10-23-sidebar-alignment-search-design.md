# Sidebar Alignment and Search Design

## Intent

Refine the owner-approved LiquidGlass sidebar without changing its accepted
material, hierarchy, proportions, controls, or behavior. Align visual columns
and give Search notes a subtle theme-native frame inspired by Kitty's edge
definition rather than its whole-window shader.

## Chosen approach

- Define one sidebar-local alignment grid in `sidebar.py`: outer margin, icon
  inset/size, and text-column start.
- Keep the brand icon centered on the action-icon column and begin brand text,
  action labels, and search text on the same text column.
- Replace the line edit's embedded leading action with a separate fixed-size
  search-icon label inside the search row. Keep the existing `QLineEdit`, clear
  button, focus, accessibility, and search signal behavior.
- Add a sidebar-local `SearchWell` subclass which draws only Kvantum's native
  line-edit frame primitive. It must not ask Qt/Kvantum to draw a panel or
  interior and must leave the center pixels unchanged.
- Keep headings, note list, and footer on the shared outer margin. Validate the
  grid at the 250 px minimum, normal 300 px, and 520 px maximum widths.

## Constraints

- Do not modify `material.py` or the accepted NavigationRail painting path.
- No shader dependency, stylesheet, fixed RGB color, invented opacity, or
  independently filled search surface.
- No behavior, editor, Sync, Settings, storage, history, Android, installation,
  or global theme changes.
- Automated rendering verifies geometry and frame-only behavior; the owner
  decides final Wayland visual acceptance.

## Alternatives considered

- Embedded QLineEdit action with tuned margins: rejected because internal
  style spacing cannot guarantee the shared text column.
- Custom reflected-light painting: rejected because it would require
  application-chosen color or opacity and imitate Kitty's shader.
