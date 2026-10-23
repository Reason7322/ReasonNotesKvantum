# Brighter Search Frame Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Use Kvantum's brighter native focused line-edit edge as the resting Search notes frame without painting its center.

**Architecture:** Keep the existing clipped `PE_PanelLineEdit` path and add the native focus state to its style option unconditionally. Pin the brightness and unchanged-center behavior with image-based focused tests.

**Tech Stack:** Python, PySide6 Qt Widgets, qt6ct/Kvantum, unittest.

**Spec:** `docs/superpowers/specs/2026-10-23-brighter-search-frame-design.md`

## Global Constraints

- Change only Search notes frame rendering and its focused tests/status.
- Preserve the accepted sidebar material and alignment grid exactly.
- Add no color literals, opacity constants, fills, stylesheets, shaders, or global theme changes.
- Do not launch, install, deploy, synchronize, or touch production data.

## Review Focus

- Resting frame is measurably brighter than native normal.
- Center remains untouched by frame painting.
- Native focus artwork, not an app-owned stroke, produces the brighter edge.
- Search interactions and Ctrl+F remain intact.
- Supported sidebar widths retain the accepted alignment grid.

---

### Task 1: Brighten the clipped native frame

**Files:**
- Modify: `src/reasonnotes_widgets/sidebar.py`
- Modify: `tests/test_widgets_visual_polish.py`
- Modify: `PROJECT_STATUS.md`

**Interfaces:**
- Consumes: `SidebarSearchWell.draw_native_frame(QPainter, QRect)`.
- Produces: the same frame-only API with native focused-state artwork at rest.

- [x] **Step 1: Add a failing brightness regression**

Render the current resting frame and independent native normal/focused
references. Assert the resting frame is brighter than normal, equals focused,
and leaves its center unchanged.

- [x] **Step 2: Run the focused test and verify RED**

Run: `QT_QPA_PLATFORM=offscreen PYTHONPATH=src /usr/bin/python3 -m unittest tests.test_widgets_visual_polish.WidgetsVisualPolishTests.test_sidebar_search_resting_frame_uses_brighter_native_focus_edge -v`

Expected: FAIL because the resting frame currently equals native normal.

- [x] **Step 3: Add native focus state to the clipped frame option**

In `SidebarSearchWell.draw_native_frame`, retain all clipping and geometry and
set `QStyle.StateFlag.State_HasFocus` before delegating to Kvantum.

- [x] **Step 4: Run focused verification**

Run the visual-polish and main-window suites. Require all selected tests to
pass, `material.py` to retain its accepted SHA-256, and `git diff --check` to
remain clean.

- [x] **Step 5: Document and checkpoint**

Update project status, commit on `forge/reasonnotes-completion`, push the exact
commit to `handoff` and `github`, and verify both full remote SHAs equal HEAD.
