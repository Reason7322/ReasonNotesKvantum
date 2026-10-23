# Physical Synchronization Preparation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prepare a fail-closed, persistent Fedora fixture and exact instructions for one JSON v1 physical round trip.

**Architecture:** Add real-account production protection inside launch-path resolution, retain the external isolation verifier, reuse the established JSON v1 fixture/protocol, and document each transport/import/receipt evidence boundary.

**Tech Stack:** Python, PySide6 launcher, ReasonNotes JSON v1 transport, KDE Connect CLI, unittest.

**Spec:** `docs/superpowers/specs/2026-10-23-physical-sync-preparation-design.md`

## Global Constraints

- Do not launch the app, transmit through KDE Connect, install Android, or modify phone/production data.
- Preserve the approved sidebar and all transport/receipt semantics.
- Use persistent paths under `/home/reason/Temporary/`, never `/tmp`.
- Physical behavior remains unproven until separately authorized.

## Review Focus

- Isolated HOME cannot conceal the real production repository from bootstrap.
- Symlink aliases and broad parents remain rejected by the external verifier.
- Current source still descends from the proven JSON v1 checkpoint.
- The first sync selects one synthetic note only.
- Delivery, durable import, returned receipt, and confirmation remain separate evidence states.

---

### Task 1: Strengthen the in-process production-path guard

**Files:**
- Modify: `src/reasonnotes_widgets/bootstrap.py`
- Modify: `tests/test_widgets_bootstrap.py`

- [x] Add a failing test using isolated HOME with an explicit real-account production root.
- [x] Verify RED, then include the login account home in protected roots.
- [x] Run focused bootstrap and candidate-isolation tests.

### Task 2: Prepare persistent round-trip evidence

**Files:**
- Create: `docs/PHYSICAL_SYNC_PREPARATION_2026-10-23.md`
- Modify: `docs/ANDROID_PHYSICAL_ACCEPTANCE.md`
- Modify: `PROJECT_STATUS.md`

- [x] Prepare a fresh deterministic fixture under `/home/reason/Temporary/`.
- [x] Record source/fixture hashes, observed write timeline, and remaining unknowns.
- [x] Record read-only Android/KDE Connect peer identity evidence where available.
- [x] Document exact isolation gate, launch command, and one-note round-trip sequence.

### Task 3: Verify and checkpoint

- [x] Run JSON v1 transport, receipt, bootstrap, fixture, and isolation-focused tests using a persistent TMPDIR.
- [x] Confirm no ReasonNotes process was launched and production manifests did not change during preparation.
- [x] Commit on `forge/reasonnotes-completion`, push to `handoff` and `github`, and verify both full SHAs equal HEAD.
