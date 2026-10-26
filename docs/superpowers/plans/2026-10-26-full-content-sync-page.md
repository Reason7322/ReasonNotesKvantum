# Full-content Synchronization Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Sync occupy the full content region beside the approved sidebar and keep verbose synchronization details out of the sidebar footer.

**Architecture:** Convert `SyncPanel` from a dock widget into a normal page owned by the existing `QStackedWidget`. `ReasonNotesMainWindow` remembers the previous non-Sync page, switches to Sync on navigation, restores that page on close, and renders only the translated sync state in the sidebar footer.

**Tech Stack:** Python 3, PySide6 Qt Widgets, `unittest`, Qt offscreen test platform.

**Spec:** `docs/superpowers/specs/2026-10-26-full-content-sync-page-design.md`

## Global Constraints

- Preserve the approved sidebar material, alignment, controls, ordering, and dimensions.
- Do not change synchronization, confirmation, conflict, storage, Android, or KDE Connect behavior.
- Keep detailed status and actionable errors visible on the Sync page.
- Do not deploy, migrate production data, or modify global theme settings.

## Review Focus

- Opening Sync from Settings must replace Settings rather than display beside it.
- Closing Sync must restore the exact prior editor, Settings, or conflict page when still valid.
- Controller refreshes during an open Sync page must not unexpectedly navigate back to the editor.
- Sidebar status must stay concise for idle, running, completed, and error states.
- Existing Sync controls, progress state, selection, and complete diagnostic text must remain functional.

---

### Task 1: Stack-based Sync navigation and concise footer

**Files:**
- Modify: `src/reasonnotes_widgets/sync_panel.py`
- Modify: `src/reasonnotes_widgets/main_window.py`
- Modify: `tests/test_widgets_sync_panel.py`
- Modify: `tests/test_widgets_lifecycle.py`

**Interfaces:**
- Consumes: `ReasonNotesMainWindow.page_stack`, `SyncPanel`, and presenter `sync_state`/`sync_message`.
- Produces: `ReasonNotesMainWindow.open_sync_panel()`, `close_sync_page()`, and a stack-owned `sync_panel` page.

- [ ] **Step 1: Write failing widget tests**

Add tests proving that Sync is a `QWidget` in `page_stack`, opening from the editor and Settings replaces the current page, closing restores the prior page, controller refresh leaves an open Sync page visible, the sidebar contains only `Phone: <state>`, and `SyncPanel.status_label` retains the complete message.

- [ ] **Step 2: Run the focused tests and verify RED**

Run: `QT_QPA_PLATFORM=offscreen python -m unittest tests.test_widgets_sync_panel tests.test_widgets_lifecycle`

Expected: failures showing the panel is still a `QDockWidget`, Settings remains visible beneath it, and the sidebar still includes `sync_message`.

- [ ] **Step 3: Implement the minimal page conversion**

Change `SyncPanel` to a `QWidget` with its existing content/layout and controls. Add it to `page_stack`; route close/cancel through `ReasonNotesMainWindow.close_sync_page()`. Preserve the page during controller refresh and restore the remembered prior page on close. Render only translated `sync_state` in the sidebar footer.

- [ ] **Step 4: Run focused tests and verify GREEN**

Run: `QT_QPA_PLATFORM=offscreen python -m unittest tests.test_widgets_sync_panel tests.test_widgets_lifecycle`

Expected: all focused tests pass.

- [ ] **Step 5: Run affected Widgets regression tests**

Run: `QT_QPA_PLATFORM=offscreen python -m unittest tests.test_widgets_sync_panel tests.test_widgets_lifecycle tests.test_widgets_visual_polish tests.test_widgets_i18n tests.test_widgets_conflicts tests.test_widgets_controller`

Expected: all tests pass with no synchronization-logic changes.

- [ ] **Step 6: Update project status and checkpoint**

Record the UI correction and verification in `PROJECT_STATUS.md`, commit the spec/plan/source/tests on `forge/reasonnotes-completion`, push the exact commit to `handoff` and `github`, and verify both full remote SHAs match local HEAD. Do not install or replace the running candidate.
