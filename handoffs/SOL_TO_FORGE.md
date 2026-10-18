# SOL -> FORGE: ReasonNotesKvantum design-continuation checkpoint

## Original product deliverable

Ship a **complete and usable** Qt Widgets desktop ReasonNotes using the
user-selected *system* Kvantum theme, preserving NoteService/history,
autosave, search, KDE Connect, receipts, conflicts, peer deletion, Polish/English,
and Android protocol compatibility. Owner must visually approve before a
production cutover; current production data/launcher are protected.

## Source and ownership

Incoming Forge branch: forge/qtwidgets-rewrite,
4665147d0e0c8b236c5c01a4009a6426a9cf8187.
This checkpoint is on a separate ChatGPT-owned
sol/qtwidgets-glass-balance branch; preserve Forge's workspace and history.

## Changes

First pass (earlier sol commit) used a flat palette background and removed the
Settings back button. Owner rejected the gray slab. Current pass repairs the
actual design: live-theme-derived spatial glass/backgrounds, NavigationRail,
GlassCard, SearchWell, TitleRule, wider Settings cards, consistent line icons,
more deliberate editor spacing, localized Notes header. Settings is navigated
only from the persistent sidebar. Backend and transport are unchanged.

## Evidence

- Latest complete automated suite: 223/223 PASS.
- Real isolated Wayland sessions: style=kvantum, blur.active=True, empty error.
- Inspected composited screen captures for empty editor, populated notes/editor,
  and Settings; user visual acceptance is still NOT established.
- Synthetic/disposable notes only. Source build of native helper succeeded.
- Production and installed candidate paths were not written; Forge workspace
  was not modified; no new app build was installed or deployed.
- QColor NaN diagnostics and shutdown ResourceWarning remain, were not audited
  as part of these visual changes.

## Exact remaining action

Owner should run the new isolated preview against the normal wallpaper and
give direct visual feedback. Fix only evidenced remaining UI problems before
integrating into Forge's own branch and repeating necessary candidate checks.
Then separately obtain Android physical validation and explicit approval
before changing any production launcher/data. This handoff is not final
product acceptance and is not a request for a fresh backend audit.
