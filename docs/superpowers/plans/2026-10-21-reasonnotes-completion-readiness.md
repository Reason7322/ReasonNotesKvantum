# ReasonNotes Completion Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Exhaust the remaining owner-independent engineering work by producing a reproducible physical-Android acceptance fixture, validating the exact current source as an isolated packaged candidate, and collecting current native Wayland evidence for owner acceptance.

**Architecture:** Preserve Qwen's Widgets/UI work and all backend protocols unchanged. Add one offline-only preparation utility around the existing `NoteService` and candidate path guards, then exercise the existing installer and runtime probe entirely under disposable roots. Keep the Kitty-equivalent renderer explicit until the owner accepts it; do not silently promote an earlier diagnostic mode.

**Tech Stack:** Python 3.14, PySide6/Qt Widgets, existing ReasonNotes service/sync packages, unittest, Qt6CT/Kvantum, native Wayland/Hyprland.

**Spec:** `docs/superpowers/specs/2026-10-18-qtwidgets-kvantum-rewrite-design.md`

## Global Constraints

- Do not modify the production launcher, release, desktop entry, settings, notes, KDE Connect configuration, Android device, or global desktop/theme configuration.
- Use only disposable repositories, configuration roots, and temporary candidate installation paths.
- Preserve the installed `qt6ct-style -> Kvantum` chain and Qwen's name-based `QProxyStyle` teardown fix.
- Do not make the hidden Kitty renderer the default without owner visual acceptance.
- Product completion remains gated by owner visual acceptance, physical Android interoperability, and separately authorized production cutover.

## Review Focus

- A fixture target resolving inside production data must fail before creating files.
- A non-empty fixture directory must not be overwritten or partially reused.
- Unicode, conflict-seed, and deletion-seed notes must reopen from immutable history with stable IDs.
- The packaged launcher must use candidate-only data and the exact staged source revision.
- Runtime validation must disable automatic receive/device activity and must report native Wayland, qt6ct/Kvantum, blur state, and selected material mode.

---

### Task 1: Offline physical-Android acceptance fixture

**Files:**
- Create: `scripts/prepare-android-acceptance.py`
- Create: `tests/test_android_acceptance_prep.py`
- Create: `docs/ANDROID_PHYSICAL_ACCEPTANCE.md`
- Modify: `docs/CANDIDATE_TESTING.md`

**Interfaces:**
- Consumes: `resolve_launch_paths(...)`, `Repository.open(...)`, and `NoteService.create_note(...)`.
- Produces: `prepare_fixture(workspace: Path) -> dict`, a JSON manifest, isolated repository/inbox/received paths, and exact human-run acceptance steps.

- [x] **Step 1: Write failing tests for production-path refusal, non-empty-target refusal, deterministic manifest structure, Unicode/history reopening, and absence of transport activity.**
- [x] **Step 2: Run `python3 -m unittest tests.test_android_acceptance_prep -v`; expect failure because the preparation utility does not exist.**
- [x] **Step 3: Implement the minimal offline fixture generator using existing path guards and `NoteService`; make the CLI require an explicit workspace.**
- [x] **Step 4: Run `python3 -m unittest tests.test_android_acceptance_prep -v`; expect all tests to pass.**
- [x] **Step 5: Run the utility once under `/tmp`, reopen all seeded notes, and record the generated manifest and next physical checks in the documentation.**
- [x] **Step 6: Commit the utility, tests, and acceptance documentation.**

### Task 2: Exact isolated candidate package

**Files:**
- Modify if evidence changes: `docs/VALIDATION.md`

**Interfaces:**
- Consumes: current Forge HEAD, `scripts/install-candidate.py`, and the Task 1 fixture.
- Produces: an immutable release under a temporary home, compiled Wayland helper, candidate-only launcher/desktop entry, hashes, and launch-check evidence.

- [x] **Step 1: Install current HEAD with `scripts/install-candidate.py` into a new `/tmp` home using explicit install, launcher, and desktop paths.**
- [x] **Step 2: Verify the release contains the current source, native helper, desktop entry, and no production paths or bundled Kvantum theme.**
- [x] **Step 3: Run the packaged launcher `--check-launch` with isolated HOME/XDG roots and verify production markers and paths remain unchanged.**
- [x] **Step 4: Exercise candidate rollback between two temporary immutable releases and verify both releases remain intact.**
- [x] **Step 5: Record exact artifact hashes and results without installing to the user's candidate or production paths.**

### Task 3: Native Wayland current-candidate validation

**Files:**
- Create: `docs/RELEASE_CANDIDATE_VALIDATION_2026-10-21.md`
- Create: `docs/evidence/release-candidate-2026-10-21/` captures and runtime logs

**Interfaces:**
- Consumes: Task 1 fixture and Task 2 packaged launcher.
- Produces: actual current-source and packaged-runtime evidence for the Qwen Mission 03/05/06 UI state.

- [x] **Step 1: Confirm Workspace 10 is empty without moving or closing user windows.**
- [x] **Step 2: Launch the packaged candidate on native Wayland with the Task 1 data, `--kitty-window-material`, `--no-auto-receive`, and a bounded runtime probe.**
- [x] **Step 3: Capture full-resolution editor and Settings views, including the splitter at rest and on hover where practical; inspect the images at full resolution.**
- [x] **Step 4: Verify runtime style/platform/blur/material output, clean shutdown, and unchanged production launcher/data hashes.**
- [x] **Step 5: Record observed UI strengths, visible weaknesses, and the exact owner visual decision still required.**

### Task 4: Completion checkpoint and remaining owner gates

**Files:**
- Modify: `PROJECT_STATUS.md`
- Modify: `handoffs/FORGE_TO_QWEN.md`

**Interfaces:**
- Consumes: Tasks 1-3 evidence and the 240-test integrated baseline.
- Produces: a durable Forge checkpoint stating the exact validated candidate and the smallest remaining owner-authorized actions.

- [x] **Step 1: Run affected fixture tests, installer tests, and the full isolated suite with localhost permission; expect all tests to pass.**
- [x] **Step 2: Run `git diff --check`, inspect status, and distinguish implemented/tested/built/launched/deployed states.**
- [x] **Step 3: Update status/handoff with the unchanged product goal, current evidence, physical Android test request, visual decision, and cutover boundary.**
- [x] **Step 4: Commit and push the exact Forge branch to `handoff` and `github`; verify both full remote SHAs equal local HEAD.**
