# Sidebar Alignment and Search Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Align the accepted ReasonNotes sidebar on one shared grid and add a Kvantum-native, frame-only Search notes surround without changing the approved LiquidGlass material.

**Architecture:** Keep all production changes local to `sidebar.py`. Expose the action-button paint geometry, build the search row from a separate icon and integrated line edit, and use a sidebar-specific `SearchWell` subclass that delegates only `PE_FrameLineEdit` to the active style chain.

**Tech Stack:** Python, PySide6 Qt Widgets, qt6ct/Kvantum, unittest.

**Spec:** `docs/superpowers/specs/2026-10-23-sidebar-alignment-search-design.md`

## Global Constraints

- Preserve the accepted NavigationRail material, gradient, proportions, controls, and behavior.
- Do not use literal colors, invented opacity, custom fallback palettes, shaders, or stylesheets.
- Do not modify global theme configuration, installed applications, repositories, synchronization, or Android.
- Do not launch the application; owner visual acceptance remains pending.

## Review Focus

- Minimum, normal, and maximum sidebar widths retain the icon and text columns.
- Kvantum's frame primitive changes edge pixels while leaving the center untouched.
- Focus, typing, clear-button, and Ctrl+F behavior remain native and operational.
- Empty or long search text does not move the leading icon or text column.
- Existing note list and footer keep their intended outer margin.

---

### Task 1: Pin the alignment grid and frame-only rendering

**Files:**
- Modify: `tests/test_widgets_visual_polish.py`
- Modify: `src/reasonnotes_widgets/sidebar.py`

**Interfaces:**
- Produces: `SidebarActionButton.icon_rect()`, `SidebarActionButton.text_rect()`, and sidebar-local frame-only search well behavior.

- [x] **Step 1: Write failing geometry and rendering tests**

Assert shared icon centers and text starts at 250, 300, and 520 px widths. Paint the search well's native frame onto a sentinel image and assert that at least one edge pixel changes while the center pixel does not.

- [x] **Step 2: Run the focused tests and confirm they fail for the current layout**

Run: `QT_QPA_PLATFORM=offscreen PYTHONPATH=src /usr/bin/python3 -m unittest tests.test_widgets_visual_polish.WidgetsVisualPolishTests.test_sidebar_alignment_grid_at_supported_widths tests.test_widgets_visual_polish.WidgetsVisualPolishTests.test_sidebar_search_native_frame_is_edge_only -v`

- [x] **Step 3: Implement the shared grid and native frame-only search row**

Add sidebar geometry constants; use them for action painting and the brand row. Replace the embedded line-edit action with a separate fixed icon label. Subclass `SearchWell` locally and draw only `PE_FrameLineEdit` through the active style chain.

- [x] **Step 4: Run the focused tests and confirm they pass**

Run the two tests from Step 2 and require `OK`.

### Task 2: Preserve search interaction and accepted material

**Files:**
- Modify: `tests/test_widgets_visual_polish.py`
- Modify: `PROJECT_STATUS.md`

**Interfaces:**
- Consumes: Task 1's sidebar layout and search well.
- Produces: focused behavioral/material evidence and review instructions.

- [x] **Step 1: Add focused interaction and material assertions**

Assert typing/filter signaling, clearing, focus, accessibility, no stylesheet, no Base brush, and unchanged accepted material source identity.

- [x] **Step 2: Run focused sidebar and existing line-edit tests**

Run only the relevant visual-polish and main-window search tests; require all selected tests to pass.

- [x] **Step 3: Update project status**

Record the bounded change, reference screenshots, tests, no-launch state, safe isolated review procedure, and pending owner visual acceptance plus Android synchronization.

- [ ] **Step 4: Verify scope and checkpoint**

Confirm only intended files changed and `material.py` retains its accepted SHA-256. Commit on `forge/reasonnotes-completion`, push the same SHA to `handoff` and `github`, and verify both remote SHAs equal local HEAD.
