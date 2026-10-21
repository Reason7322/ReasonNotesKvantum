# Confirmed Phone Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the frozen desktop Sync drawer wait for durable Android receipt confirmation and show honest running, success, no-op, and error states.

**Architecture:** Keep `sync_linux()` as the one-shot protocol primitive and add a receipt-waiting GUI orchestration around it with injected time dependencies. Wire that orchestration into the existing worker, and add only an indeterminate progress bar to the accepted action card.

**Tech Stack:** Python 3.14, PySide6/Qt Widgets, unittest, KDE Connect CLI, native Wayland/Hyprland.

**Spec:** `docs/superpowers/specs/2026-10-21-confirmed-phone-sync-design.md`

## Global Constraints

- The accepted UI is frozen; no hierarchy, sizing, wording, scope, note-list, or action redesign.
- Success requires durable receipt confirmation for every revision requested by the click.
- Preserve protocol envelopes, Android interoperability, note/history/conflict/deletion behavior, and one-shot CLI semantics.
- Use only the prepared disposable fixture for physical validation; do not perform production cutover.

## Review Focus

- A receipt confirmed between polling scans must still complete via durable ledger state.
- A partial confirmation followed by disconnect must report error, not partial success.
- A revision at the bounded retry limit must not be silently represented as a no-op.
- An empty or already-confirmed selection must not appear as a newly successful phone transfer.
- The progress indicator must hide again after both worker success and worker failure.

---

### Task 1: Receipt-confirmed desktop orchestration

**Files:**
- Modify: `src/reasonnotes_sync/sync.py`
- Test: `tests/test_confirmed_sync.py`

**Interfaces:**
- Consumes: existing `sync_linux()`, `scan_inbox()`, `DeliveryLedger`, and `DeliveryState`.
- Produces: `sync_linux_confirmed(repository, inbox, adapter, *, selected_note_ids=None, received_dir=None, timeout_seconds=120.0, poll_interval_seconds=0.5, monotonic=..., sleeper=...) -> SyncReport`.

- [ ] Write failing tests for exact confirmed success, request-only timeout, partial-confirmation disconnect, initial unreachable failure, neutral no-op, and retry-limit error.
- [ ] Run `PYTHONPATH=src /usr/bin/python3 -m unittest tests.test_confirmed_sync -v`; expect failures because the orchestration does not exist.
- [ ] Implement the smallest orchestration that aggregates scan results, reads durable ledger state, observes reachability, and preserves the one-shot primitive.
- [ ] Rerun the focused tests; expect all to pass.
- [ ] Run existing sync, selective-sync, delivery, receipt, and CLI tests; expect all to pass.

### Task 2: Honest presenter state and frozen-drawer progress

**Files:**
- Modify: `src/reasonnotes_app/presenter.py`
- Modify: `src/reasonnotes_widgets/sync_panel.py`
- Test: `tests/test_linux_presenter.py`
- Test: `tests/test_widgets_sync_panel.py`
- Test: `tests/test_widgets_controller.py`

**Interfaces:**
- Consumes: Task 1 `SyncReport` convention: requested revisions are successful only when included in confirmations and no errors exist.
- Produces: presenter `Completed` only for receipt-confirmed requested revisions, neutral `Idle` for no-op, `Error` for failures; `SyncPanel.progress_bar` mirrors `Running`.

- [ ] Write failing presenter tests proving request-only is not complete, confirmed request is complete, no-op is neutral, and errors remain errors.
- [ ] Write a failing real-widget test proving the indeterminate progress bar is visible only while running and preserves the accepted card geometry/controls.
- [ ] Run the focused tests and verify the expected failures.
- [ ] Implement the minimal presenter rules and progress bar without changing other drawer layout or behavior.
- [ ] Rerun the focused tests; expect all to pass.

### Task 3: Candidate wiring and bounded KDE Connect command failure

**Files:**
- Modify: `linux-app/reasonnotes_widgets.py`
- Modify: `src/reasonnotes_sync/kdeconnect_linux.py`
- Test: `tests/test_kdeconnect_linux.py`
- Test: `tests/test_widgets_bootstrap.py`

**Interfaces:**
- Consumes: Task 1 `sync_linux_confirmed()`.
- Produces: GUI `run_sync()` uses receipt-confirmed orchestration; default KDE Connect subprocess calls terminate with a clear failed request on timeout or launch error.

- [ ] Write failing tests for candidate wiring and default KDE Connect command timeout/failure conversion.
- [ ] Run the focused tests and verify the expected failures.
- [ ] Wire the GUI runner and add bounded command execution without changing envelope or device-selection semantics.
- [ ] Rerun the focused tests; expect all to pass.

### Task 4: Integrated and physical acceptance evidence

**Files:**
- Create: `docs/CONFIRMED_PHONE_SYNC_VALIDATION_2026-10-21.md`
- Update only if needed: `docs/ANDROID_PHYSICAL_ACCEPTANCE.md`

**Interfaces:**
- Consumes: Tasks 1-3 candidate behavior and the existing disposable-fixture script.
- Produces: exact automated, Wayland, Android success/failure, artifact, and production-boundary evidence.

- [ ] Run `QT_QPA_PLATFORM=offscreen PYTHONPATH=src /usr/bin/python3 -m unittest discover -s tests -q` with required localhost/filesystem permission; expect all tests to pass.
- [ ] Run `git diff --check`, compile checks, and build/install the exact disposable candidate artifacts as required.
- [ ] Launch the exact desktop candidate on native Wayland with a fresh acceptance fixture and capture the frozen drawer in idle/running/result states.
- [ ] Validate durable receipt success and disconnected/unreachable error against the physical Android test app; then complete the documented Unicode/conflict/deletion/restart fixture sequence.
- [ ] Record exact Git SHA, Android build/version/hash, KDE Connect device identity, transferred files, timestamps, screenshots, final fixture state, and the still-unperformed production cutover.
