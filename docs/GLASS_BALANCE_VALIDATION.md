# Glass material balance correction — 2026-10-18

Original goal: complete, functionally compatible, visually accepted Qt Widgets +
system Kvantum ReasonNotes replacement. Production remains unchanged.

## Baseline and ownership

- Forge source: 4665147d0e0c8b236c5c01a4009a6426a9cf8187.
- ChatGPT-owned branch: sol/qtwidgets-glass-balance.
- Did not modify Forge's workspace, installed candidate, live app, notes,
  Android, system Kvantum assets, or Hyprland settings.

## Changes

- One top-level material fill behind previously transparent editor/list/input
  widgets, instead of almost bare wallpaper blur. Color comes from the running
  system Kvantum QPalette Base role, retaining its alpha (no bundled theme).
- CompositionMode_Source preserves framebuffer alpha on translucent Wayland
  surfaces. Opaque fallback outside Wayland remains unchanged.
- Removed Settings back control entirely. The permanent sidebar Settings
  button toggles between Settings and notes/editor.

## Evidence

- Focused visual tests: 5/5 PASS.
- Full suite: 222/222 PASS, 7.190 seconds, QT_QPA_PLATFORM=offscreen.
- Existing native blur helper compiled in ChatGPT worktree, not installed.
- Actual bounded Wayland probe with disposable XDG data/config and repository:
  RUNTIME_STYLE=kvantum, RUNTIME_PLATFORM=wayland,
  RUNTIME_BLUR_ACTIVE=1, RUNTIME_BLUR_ERROR empty.
- Offscreen alpha render with simulated Wayland translucent surface: Kvantum
  Base #2a2f32 at alpha 184, material pixel RGBA(42,47,50,184).
- The captured real desktop probe was over another dark window and is not
  reliable evidence of visual balance over a vivid wallpaper.
- Qt QColor nan warnings and Python shutdown ResourceWarning remain; tests
  passed, but those warnings were not independently investigated here.

## Open acceptance

Not installed; owner visual approval and physical Android interoperability
pending. No production cutover or migration. Next action is review on a
visually useful wallpaper/Dolphin comparison, then integrate accepted
improvements without discarding Forge work or retesting unchanged backend.
