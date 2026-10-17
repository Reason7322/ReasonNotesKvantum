# ReasonNotes Qt Widgets and System Kvantum Rewrite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the complete isolated Fedora ReasonNotes candidate with native Qt Widgets rendered by the installed system Kvantum style while preserving existing backend behavior.

**Architecture:** Preserve `reasonnotes_app.NoteService`, `NotePresenter`, and `reasonnotes_sync`; replace the QML bridge with focused Widgets models/controller and a `QMainWindow`. Candidate bootstrap and packaging enforce separate data/configuration paths, while optional Wayland blur attaches to the top-level QWidget surface.

**Tech Stack:** Python 3.14, PySide6 6.11, Qt 6 Widgets, system Kvantum 1.1.6, unittest, KDE Connect, ext-background-effect-v1.

**Spec:** `docs/superpowers/specs/2026-10-18-qtwidgets-kvantum-rewrite-design.md`

## Global Constraints

- Never write to the installed production application, production note store, production settings, Android private data, or global desktop/theme configuration.
- Candidate default data root is `~/.local/share/ReasonNotesKvantum-candidate`, never `~/.local/share/ReasonNotes`.
- Use the installed `kvantum` QStyle and currently selected system Kvantum theme; bundle no theme assets and force no theme.
- Preserve immutable history, conflict, delivery, receipt, retry, deletion, and Android protocol semantics.
- Run network/inbox work off the GUI thread; opening UI must not initiate outgoing transfers.
- Preserve English and Polish support.
- Apply TDD to every new behavior and use disposable repositories/configuration in tests.

## Review Focus

- Missing/unavailable Kvantum plugin must fail clearly without silently styling production differently.
- Dirty or failed drafts must survive note switching, F5, sync completion, and close attempts.
- Candidate defaults and installer must not resolve to any production ReasonNotes path.
- Stale bulk-delete and conflict choices must never affect newer or unselected notes.
- Blur/transparency failure must remain readable and must not change global configuration.

---

### Task 1: Import the verified baseline and provenance

**Files:**
- Create: `src/reasonnotes_app/**`, `src/reasonnotes_sync/**`, `tests/**`
- Create: `linux-app/icons/**`, `linux-app/native/reasonnotes_wayland_blur.c`
- Create: `scripts/build-wayland-blur.py`
- Create: `docs/PROVENANCE.md`
- Create: `pyproject.toml`

**Interfaces:**
- Consumes: source commit `873dcd524179abc39ae708b055c76f2798af1e48`.
- Produces: unchanged backend packages and regression suite available in the Forge repository.

- [ ] Import only tracked application/backend/test/icon/native-helper material; exclude QML runtime, caches, build outputs, production data, and linked-worktree metadata.
- [ ] Record source repository, branch, exact commit, imported paths, and exclusions.
- [ ] Run the backend/presenter regression suite and record the unchanged baseline result.
- [ ] Commit the import and documentation.

### Task 2: Candidate bootstrap, path isolation, and Kvantum activation

**Files:**
- Create: `src/reasonnotes_widgets/bootstrap.py`
- Create: `src/reasonnotes_widgets/__init__.py`
- Create: `linux-app/reasonnotes_widgets.py`
- Test: `tests/test_widgets_bootstrap.py`

**Interfaces:**
- Produces: `candidate_data_directory() -> Path`, `create_application(argv) -> QApplication`, and parsed isolated launch options.
- Consumes: installed Qt style plugin and existing system Kvantum configuration read-only.

- [ ] Write failing tests for candidate default paths, explicit temporary roots, production-path rejection, and `application.style().objectName() == "kvantum"`.
- [ ] Run the focused tests and verify the expected failures.
- [ ] Implement the minimal bootstrap and distinct application identity.
- [ ] Run focused and full imported tests.
- [ ] Commit.

### Task 3: Native models and Widgets controller

**Files:**
- Create: `src/reasonnotes_widgets/models.py`
- Create: `src/reasonnotes_widgets/controller.py`
- Test: `tests/test_widgets_controller.py`

**Interfaces:**
- Consumes: `NotePresenter`, `NoteRow`, `ConflictVersion`, and injected incoming/sync workers.
- Produces: `NoteListModel`, `ConflictListModel`, `WidgetsController`, typed state signals, and safe note/sync/conflict operations.

- [ ] Write failing behavioral tests for targeted model refresh, selection snapshots, async incoming refresh, async sync, and draft retention.
- [ ] Verify RED, implement minimal controller/models, verify GREEN, and run presenter regressions.
- [ ] Commit.

### Task 4: Main window, sidebar, editor, and draft lifecycle

**Files:**
- Create: `src/reasonnotes_widgets/main_window.py`
- Create: `src/reasonnotes_widgets/editor_page.py`
- Create: `src/reasonnotes_widgets/sidebar.py`
- Test: `tests/test_widgets_main_window.py`

**Interfaces:**
- Consumes: `WidgetsController` signals/models.
- Produces: `ReasonNotesMainWindow`, 300px persisted splitter, centered 920px writing column, title/body editing, 500ms autosave, and native shortcuts.

- [ ] Write failing offscreen widget tests for layout, focus, editing, autosave, switch/close flushing, blank startup, and shortcuts.
- [ ] Verify RED, implement the native window/editor/sidebar, verify GREEN, and run affected regressions.
- [ ] Commit.

### Task 5: Search, keyboard navigation, and safe bulk deletion

**Files:**
- Modify: `src/reasonnotes_widgets/sidebar.py`
- Modify: `src/reasonnotes_widgets/controller.py`
- Test: `tests/test_widgets_selection.py`

**Interfaces:**
- Consumes: model note identities and presenter deletion operations.
- Produces: Unicode search, normal/extended selection behavior, frozen deletion snapshots, and native confirmation.

- [ ] Write failing tests for Unicode filtering, keyboard selection, non-contiguous bulk selection, search-stable snapshots, cancellation, and stale-note protection.
- [ ] Verify RED, implement, verify GREEN, and run service/presenter regressions.
- [ ] Commit.

### Task 6: English and Polish application chrome

**Files:**
- Create: `src/reasonnotes_widgets/i18n.py`
- Create: `src/reasonnotes_widgets/settings_page.py`
- Modify: `src/reasonnotes_widgets/main_window.py`
- Test: `tests/test_widgets_i18n.py`

**Interfaces:**
- Produces: `Translator`, persisted `en`/`pl` selection, and live retranslation of Widgets chrome.
- Consumes: candidate-specific `QSettings`; provides no appearance selector.

- [ ] Write failing tests for persistence, invalid fallback, complete Polish labels, and unchanged note content.
- [ ] Verify RED, implement, verify GREEN, and run affected tests.
- [ ] Commit.

### Task 7: Native synchronization panel

**Files:**
- Create: `src/reasonnotes_widgets/sync_panel.py`
- Modify: `src/reasonnotes_widgets/main_window.py`
- Test: `tests/test_widgets_sync_panel.py`

**Interfaces:**
- Consumes: controller sync catalogue/selection and asynchronous sync methods.
- Produces: edge-attached all/selected sync interface with search, select all/clear, evidence-accurate status, and no-open side effects.

- [ ] Write failing tests for all/selected modes, selection count, disabled empty selection, clean previews, no-open transfer, and worker-thread completion.
- [ ] Verify RED, implement, verify GREEN, and run sync/receipt regressions.
- [ ] Commit.

### Task 8: Native conflict interface

**Files:**
- Create: `src/reasonnotes_widgets/conflict_page.py`
- Modify: `src/reasonnotes_widgets/main_window.py`
- Test: `tests/test_widgets_conflicts.py`

**Interfaces:**
- Consumes: controller conflict model and exact resolution operations.
- Produces: full candidate display, explicit revision choice, deletion labeling, Skip, and stale-choice refresh.

- [ ] Write failing tests for full bodies, multi-head selection, keep/skip, deleted heads, stale choices, and preserved history.
- [ ] Verify RED, implement, verify GREEN, and run conflict/service regressions.
- [ ] Commit.

### Task 9: F5, foreground purge, and application lifecycle

**Files:**
- Modify: `linux-app/reasonnotes_widgets.py`
- Modify: `src/reasonnotes_widgets/main_window.py`
- Test: `tests/test_widgets_lifecycle.py`

**Interfaces:**
- Consumes: existing scan, receipt return, purge relay, and controller worker APIs.
- Produces: deferred startup scan, F5 queued refresh, foreground-only purge relay, refresh timer, and orderly shutdown.

- [ ] Write failing tests for first-window startup, F5 no-upload behavior, queued refresh, dirty-draft retention, remote purge refresh, and teardown.
- [ ] Verify RED, implement, verify GREEN, and run receive/purge regressions.
- [ ] Commit.

### Task 10: QWidget transparency and Wayland compositor blur

**Files:**
- Create: `src/reasonnotes_widgets/wayland_blur.py`
- Modify: `linux-app/reasonnotes_widgets.py`
- Modify: `linux-app/native/reasonnotes_wayland_blur.c`
- Test: `tests/test_widgets_wayland_blur.py`

**Interfaces:**
- Consumes: top-level QWidget `winId`, Qt native Wayland interface, and native helper.
- Produces: optional blur lifecycle, initial translucent surface, resize-safe region, and opaque readable fallback.

- [ ] Write failing tests for QWidget attachment, pre-show surface attributes, unsupported fallback, enable/disable/close, and no global configuration writes.
- [ ] Verify RED, implement/adapt, build helper, verify GREEN, and run native-helper tests.
- [ ] Commit.

### Task 11: Candidate packaging, cutover, and rollback documentation

**Files:**
- Create: `scripts/install-candidate.py`
- Create: `packaging/org.reasonnotes.ReasonNotesKvantum.desktop`
- Create: `docs/CANDIDATE_TESTING.md`
- Create: `docs/CUTOVER_AND_ROLLBACK.md`
- Test: `tests/test_candidate_install.py`

**Interfaces:**
- Produces: versioned isolated candidate install and launcher without touching any production path.
- Consumes: complete source tree and distinct candidate application ID.

- [ ] Write failing installer tests proving distinct paths, no overwrite, no production-data access, and rollback preservation.
- [ ] Verify RED, implement, verify GREEN, and exercise a temporary candidate install.
- [ ] Commit.

### Task 12: Full validation and runtime evidence

**Files:**
- Update: `PROJECT_STATUS.md`
- Update: `handoffs/FORGE_TO_QWEN.md`
- Create: `docs/VALIDATION.md`

**Interfaces:**
- Consumes: exact candidate artifact and all prior test suites.
- Produces: separated source-test, headless-widget, build, Wayland-runtime, blur-observation, and owner-acceptance evidence.

- [ ] Run the complete Python suite with isolated environment and record counts.
- [ ] Run candidate launch checks with temporary data/configuration.
- [ ] Run an actual Hyprland/Wayland candidate against disposable data, verify Kvantum style and blur-helper state, and capture non-production evidence.
- [ ] Document any subjective visual questions as owner acceptance pending.
- [ ] Perform whole-branch review, fix important findings through RED/GREEN tests, and rerun the complete suite.
- [ ] Commit and push the exact branch SHA to `handoff` and `github`; verify both with `git ls-remote`.
