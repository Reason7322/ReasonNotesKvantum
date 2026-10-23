# Native Search Bar Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the blue frame-only Search notes surround with Kvantum's complete translucent native line-edit component.

**Architecture:** `SidebarSearchWell` delegates the complete `PE_PanelLineEdit` surface to the active style. Its option reflects actual field focus, while the child `QLineEdit` remains integrated with no independent frame or Base fill.

**Tech Stack:** Python, PySide6 Qt Widgets, qt6ct/Kvantum, unittest.

**Spec:** `docs/superpowers/specs/2026-10-23-native-search-bar-design.md`

## Global Constraints

- Preserve accepted sidebar material, alignment, structure, ordering, and dimensions.
- Add no application color, opacity, stylesheet, shader, or global theme change.
- Change no editor, synchronization, Android, installation, or production data behavior.
- Do not launch interactively during this milestone.

## Review Focus

- Theme-painted center exists but remains non-opaque.
- Resting and focused states match Kvantum's native line-edit states.
- Child line edit does not stack another panel over the surround.
- Typing, clearing, Ctrl+F, and accessibility remain operational.
- Alignment remains exact at 250, 300, and 520 px widths.

---

### Task 1: Restore the complete native search input

**Files:**
- Modify: `src/reasonnotes_widgets/sidebar.py`
- Modify: `tests/test_widgets_visual_polish.py`
- Modify: `PROJECT_STATUS.md`

**Interfaces:**
- Replaces: `SidebarSearchWell.draw_native_frame(QPainter, QRect)`.
- Produces: `SidebarSearchWell.draw_native_surface(QPainter, QRect)` using actual focus state.

- [x] **Step 1: Write failing native-surface tests**

Assert that the resting center is theme-painted with alpha strictly between
zero and 255, matches an independent native normal-state render, and changes
to the independent focused-state render only while the field has focus.

- [x] **Step 2: Run the focused tests and verify RED**

Run the new surface tests and require failure because the current implementation
clips the center and forces focus state.

- [x] **Step 3: Implement the complete native surface**

Rename the paint helper, remove the frame clip, derive `State_HasFocus` only
from the search field, and delegate the full panel to `PE_PanelLineEdit`.

- [x] **Step 4: Run focused verification**

Run visual-polish and main-window suites, compile changed Python, verify
`material.py` SHA-256, and run `git diff --check`.

- [x] **Step 5: Document and checkpoint**

Update status, commit on `forge/reasonnotes-completion`, push the exact commit
to `handoff` and `github`, and verify both remote SHAs equal local HEAD.
