# Local-only Deletion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Delete a trace-free local purge on Fedora and Android, while explicit push synchronization can restore a note from the device that still has it.

**Architecture:** Remove deletion as a synchronized current-state operation. Each store gains an atomic local purge that erases note-specific state and never queues transport work; legacy incoming deletion envelopes are ignored. Explicit Sync stages the selected current live snapshots for the existing state-v2/ack-v2 confirmation path. A newly delivered carrier may be imported by the receiver's normal scanner, while occurrence indexing prevents already processed historical files from replaying.

**Tech Stack:** Python 3/PySide6/unittest on Fedora; Java 17/Android/Gradle/JUnit on Android; canonical JSON v1 transport with state-v2 and ack-v2 items.

**Spec:** `docs/superpowers/specs/2026-10-26-local-only-deletion-design.md`

## Global Constraints

- Deletion is local-only and emits no carrier, tombstone, acknowledgment, retry, or peer status.
- Purge title/body, drafts, conflicts, pending work, note-specific acknowledgments, history, and deletion metadata from the deleting device.
- Retain only generic processed-file occurrence markers that contain no note identity or content.
- Restoration requires explicit Sync from the device that still has the note.
- Preserve ordinary live-note durable confirmation and complete two-version conflict handling.
- Do not install, deploy, migrate personal data, or perform physical synchronization.

## Review Focus

- A pending local edit must not survive local Delete or leak into a later carrier.
- Deleting a conflicted note must erase both complete candidates without generating a resolution or deletion state.
- Legacy/v2 deletion envelopes must neither delete a live note nor generate an acknowledgment.
- Explicit Sync of unchanged live notes must remain confirmable through the existing exact acknowledgment flow.
- One Sync press on the surviving device must restore the receiver through its normal scan, while already-processed historical files remain ignored.

---

### Task 1: Fedora local purge semantics

**Files:**
- Modify: `src/reasonnotes_sync/current_store.py`
- Modify: `src/reasonnotes_app/service.py`
- Modify: `tests/test_current_store.py`
- Modify: `tests/test_note_service.py`

**Interfaces:**
- Produces: `CurrentNoteStore.delete_local(note_id: UUID) -> None` as an atomic local purge with no outgoing state.
- Preserves: `processed-exchange/` occurrence markers as generic scanner bookkeeping.

- [ ] Write failing tests proving local deletion removes current, conflict, pending, queued note acknowledgments, fence metadata, and serialized content; returns no envelope; and survives reopen with no outgoing state.
- [ ] Write a failing test proving an incoming deletion envelope is ignored without deleting a live state or queuing an acknowledgment.
- [ ] Run the focused store/service tests and verify RED.
- [ ] Implement the smallest atomic purge and obsolete-fence cleanup needed for GREEN.
- [ ] Run the focused tests and commit the Fedora task.

### Task 2: Fedora explicit live-snapshot push and restoration

**Files:**
- Modify: `src/reasonnotes_sync/current_store.py`
- Modify: `src/reasonnotes_sync/sync.py`
- Modify: `tests/test_sync_v2.py`
- Modify: `tests/test_widgets_lifecycle.py`

**Interfaces:**
- Consumes: Task 1 live-only store.
- Produces: explicit Sync stages selected/all current live states for the existing pending/ack path; a new delivered occurrence restores the receiver through normal scanning.

- [ ] Write failing tests for unchanged-live-state push, exact confirmation, one-sided restoration of a locally absent note, both-deleted no-op, and processed historical occurrence suppression.
- [ ] Run focused sync/lifecycle tests and verify RED.
- [ ] Implement explicit staging of live snapshots without creating new state IDs and retain retry after failed transfer.
- [ ] Run focused and affected Fedora tests; record the known unrelated installer assertion separately.
- [ ] Commit the Fedora task.

### Task 3: Android local purge semantics

**Files:**
- Modify: `android-probe/app/src/main/java/org/reasonnotes/probe/CurrentNoteStore.java`
- Modify: `android-probe/app/src/main/java/org/reasonnotes/probe/NoteService.java`
- Modify: `android-probe/app/src/test/java/org/reasonnotes/probe/CurrentNoteStoreTest.java`
- Modify: relevant `NoteService` tests.

**Interfaces:**
- Produces: Android `deleteLocal(UUID noteId)` with the same no-output local purge contract as Fedora.

- [ ] Write failing Java tests mirroring Task 1, including drafts and note-specific acknowledgment removal.
- [ ] Run focused Android tests and verify RED.
- [ ] Implement the minimal synchronized purge and obsolete-fence cleanup.
- [ ] Run focused tests and commit the Android task.

### Task 4: Android explicit live-snapshot push and restoration

**Files:**
- Modify: `android-probe/app/src/main/java/org/reasonnotes/probe/SyncCoordinator.java`
- Modify: `android-probe/app/src/main/java/org/reasonnotes/probe/CurrentTransport.java`
- Modify: relevant current-state sync and receive tests.

**Interfaces:**
- Consumes: Task 3 live-only store.
- Produces: Android explicit Sync pushes current live snapshots and normal scanning imports a newly delivered live occurrence on the receiver.

- [ ] Write failing tests matching Task 2 behavior, including one-sided restoration and historical occurrence suppression.
- [ ] Run focused Android tests and verify RED.
- [ ] Implement explicit staging and confirmation compatibility without changing the carrier format.
- [ ] Run focused Android tests and `assembleDebug`; do not install the APK.
- [ ] Commit the Android task.

### Task 5: Cross-platform compatibility and independent checkpoints

**Files:**
- Modify: cross-platform fixture/acceptance tests in both repositories as needed.
- Modify: each repository's `PROJECT_STATUS.md` and `handoffs/FORGE_TO_QWEN.md`.

**Interfaces:**
- Consumes: Tasks 1–4 symmetric contracts.
- Produces: byte-compatible live-state restoration evidence and two independently durable Git checkpoints.

- [ ] Verify Fedora-delete/Android-live restoration, Android-delete/Fedora-live restoration, both-delete no-op, no deletion carriers/acks, historical occurrence suppression, restart persistence, and unchanged conflict behavior.
- [ ] Run the relevant Fedora and Android suites without repeating unrelated physical tests.
- [ ] Update both project records with actual tests, artifact identity, and remaining physical acceptance.
- [ ] Commit each repository independently; push each exact `forge/*` branch to `handoff` and `github`; verify both full remote SHAs match local HEAD.
- [ ] Stop before installation, application launch, personal-data migration, or physical synchronization.
