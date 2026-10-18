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

## Second design pass — 2026-10-18, owner requested retry

Goal is unchanged: a complete, fully functional, visually owner-approved Qt
Widgets + **system** Kvantum replacement for desktop ReasonNotes. Existing
production, Android, and installed candidate remain protected.

The first palette-only fill was visually rejected as a flat gray slab. This
continuation replaces that flat sheet with a more deliberately composed,
responsive writing interface while keeping the working backend/Qt architecture.

Changes:
- Introduced application-owned *layout surfaces* (not bundled themes, QSS, or
  replacement button/control styles): translucent navigation rail, soft writing
  surface, small grouped actions/search, and themed title rule.
- Background/shades use the live Kvantum QPalette for hue, text, highlight,
  and alpha. The system theme is still the authority; Wayland blur is retained.
- The editor's native QLineEdit and QPlainTextEdit remain editable/transparent,
  with increased spacing and typographic hierarchy, capped at 920 logical px.
- Settings uses distinct Language and Delete-pairing panels (no back button),
  improved responsive width, and a smaller fixed-pitch pairing key.
- Replaced unrelated Qt file-manager fallback icons with compact, consistently
  colored line pictograms. Added a localized Notes section heading.
- Kept the sidebar Settings button as the navigation toggle.

Verification:
- 223 of 223 automated tests pass after final changes. Exact command:
  QT_QPA_PLATFORM=offscreen PYTHONPATH=src /usr/bin/python3 -m unittest discover -s tests -q
- Actual bounded Hyprland/Wayland previews against disposable repositories
  and XDG locations reported Kvantum style and active compositor blur with an
  empty blur error. Existing native helper was built in this separate checkout.
- Visually inspected composited screenshots of the empty editor, populated
  notes/editor, and Settings with a dummy pairing token. These substantiate
  that the design has differentiated surfaces and correct Qt painting, but do
  NOT prove owner approval or exact appearance over every wallpaper.
- Previous test shutdown ResourceWarning and QColor NaN messages remain
  observable despite all passing tests; no new root-cause diagnosis performed.
- No candidate re-install, no production writes, no Android physical testing.

Open:
- Owner subjective visual acceptance on the real wallpaper/normal window
  size, including controls and Settings.
- Physical Android protocol compatibility and production cutover/rollback
  remain unapproved and unperformed.
- No new source commit should be merged to main just to checkpoint.
