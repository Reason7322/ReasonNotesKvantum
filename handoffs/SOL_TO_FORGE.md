# ChatGPT visual continuation → Forge

Original deliverable: complete native Qt Widgets/Kvantum ReasonNotes replacement,
full functional parity and owner-approved UI, without production modification.

Incoming source: forge/qtwidgets-rewrite at
4665147d0e0c8b236c5c01a4009a6426a9cf8187.
This work is on a separate sol/qtwidgets-glass-balance branch.

Implemented: palette-derived full-window glass backing with original system
alpha, alpha-preserving QPainter source composition, complete removal of the
Settings back button, sidebar Settings toggles to return to notes.

Passed: 222 automated tests; real Wayland + kvantum + blur-active launch
against disposable files; buffer alpha 184/255. Not installed or visually
owner-accepted. Other production/Android functionality remains unmodified.
See docs/GLASS_BALANCE_VALIDATION.md for evidence and limitations.

Next concrete action: compare this branch with Forge's state, preserve any
separate WIP, transfer useful changes into a Forge-owned branch, and seek
owner feedback over a contrasting backdrop before approving visual quality.
Do not repeat unrelated validated backend research/tests.
