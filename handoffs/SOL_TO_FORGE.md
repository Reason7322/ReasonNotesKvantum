# SOL -> FORGE: native Dolphin style chain continuation

ORIGINAL PRODUCT GOAL: Ship complete functional desktop ReasonNotes using the
user's actual system Qt Widgets/Kvantum styling, preserving all notes, history,
sync, conflicts, selective sends, Android compatibility, and owner-approved
appearance. No production cutover without approval.

SOURCE: Forked Forge branch forge/qtwidgets-rewrite at full SHA
4665147d0e0c8b236c5c01a4009a6426a9cf8187 into ChatGPT-owned
sol/qtwidgets-glass-balance. The previous sol committed checkpoint was
33c3af7c8c3f415bc44fac7ac511e89af014731e. This document describes its
later continuation at current branch HEAD.

DISCOVERY:
The live Dolphin process loads qt6ct platform theme and Kvantum style.
Qt6CTProxyStyle (qt6ct-style) wraps Kvantum base, using BreezeDark, Lato 11,
YAMIS, and selected LiquidGlass. Earlier isolated previews hid those config
files by overriding XDG_CONFIG_HOME, so were not a faithful comparison.

CODE:
- Preserve the actual qt6ct-style -> Kvantum chain at QApplication startup.
- Replace sol's custom window/card/rail gradients with Kvantum's native
  PE_Widget material, Qt palette Base view, and QFrame.
- Use the system icon theme, and keep frameless text inputs through a proxy
  of the current style instead of hardwired bare Kvantum.
- Remove appearance explanation from Language settings.
- Preserve no-back-button navigation and all existing backend code.
- scripts/preview-dolphin-style.zsh copies active theme config ONLY into an
  isolated preview area; it does not change global appearance or live data.

EVIDENCE:
- Full suite 224/224 PASS, 7.243 sec.
- Live Wayland preview using copied exact theme config:
  qt6ct-style, Wayland, blur=active, no error.
- Full code/worktree and theme chain details at
  docs/DOLPHIN_NATIVE_THEME_2026-10-18.md.
- No installed candidate/source production changes. No physical Android test.

OPEN:
Owner visual approval is not established. Dolphin-specific UI widgets differ
from ReasonNotes; running the same style is not proof of identical appearance.
Android physical test, protected production cutover, and owner acceptance are
still outstanding. Handoff must preserve previous tested functionality and
avoid restudying unaffected backend work.

NEXT ACTION: Owner tests the separate preview and provides visual feedback.
Forge then adopts accepted changes into its own feature branch and handles
remaining owner-reported UI issues without touching production.
