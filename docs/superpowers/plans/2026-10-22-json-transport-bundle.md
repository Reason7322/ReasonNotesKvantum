# JSON Transport Bundle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Send every non-empty desktop sync plan in one canonical JSON v1 KDE Connect payload.

**Architecture:** A focused codec builds and fully validates canonical JSON carriers around unchanged revision/receipt envelopes. Existing sync orchestration uses one carrier request, then records each member requested only after acceptance.

**Tech Stack:** Python 3 standard library, unittest, KDE Connect adapter.

**Spec:** `docs/superpowers/specs/2026-10-22-json-transport-bundle-design.md`

## Global Constraints

- Preserve per-envelope protocol semantics and all accepted UI code.
- Continue reading individual `.md` files and legacy received ZIP bundles.
- Never create a new ZIP bundle.
- Validate all JSON members before repository mutation.

## Review Focus

- Unicode and JSON escaping must produce canonical UTF-8 bytes.
- A one-item plan must still use one JSON carrier.
- Mixed revision/receipt request failure must advance neither ledger.
- Reordered or extra JSON fields must be rejected before import.
- Existing legacy `.md` and ZIP imports must remain readable.

---

### Task 1: Canonical Python JSON bundle codec

**Files:**
- Create: `src/reasonnotes_sync/transport_bundle.py`
- Create: `tests/test_transport_bundle.py`

**Interfaces:**
- Produces: `build_bundle(items) -> (str, bytes)` and `read_transport_bundle(data, name) -> tuple[(str, bytes)]`.

- [ ] Write failing codec tests for a literal Unicode fixture, canonical bytes/name, full validation before return, limits, duplicates, field/order rejection, and identity mismatch.
- [ ] Run `PYTHONPATH=src python3 -m unittest tests.test_transport_bundle -v`; expect failures because the module does not exist.
- [ ] Implement the minimal standard-library codec.
- [ ] Re-run the focused tests; expect PASS.
- [ ] Commit the task.

### Task 2: One-carrier desktop send path

**Files:**
- Modify: `src/reasonnotes_sync/sync.py`
- Modify: `src/reasonnotes_sync/receipt_return.py`
- Modify: `tests/test_sync.py`
- Modify: `tests/test_receipt_return.py`

**Interfaces:**
- Consumes: Task 1 `build_bundle`.
- Produces: one adapter `request_transfer(bundle_path)` call per non-empty operation.

- [ ] Write failing tests proving mixed plans and receipt backlogs create one JSON carrier, preserve all identities, and do not advance state on rejection.
- [ ] Run the focused tests and verify the expected per-file behavior fails them.
- [ ] Implement content-addressed carrier persistence and single-request ledger updates.
- [ ] Re-run focused tests; expect PASS.
- [ ] Commit the task.

### Task 3: JSON receive integration and desktop regression

**Files:**
- Modify: `src/reasonnotes_sync/sync.py`
- Modify: `tests/test_bundle_transport.py`
- Modify: `tests/test_kdeconnect_receive.py`

**Interfaces:**
- Consumes: Task 1 `read_transport_bundle`.
- Produces: atomic JSON classification beside legacy `.md` and ZIP input.

- [ ] Write failing tests for mixed JSON import, malformed all-or-nothing behavior, and legacy input compatibility.
- [ ] Run focused tests and verify RED.
- [ ] Integrate JSON discovery and parsing without changing ZIP or `.md` readers.
- [ ] Run the full Python suite; expect zero failures.
- [ ] Commit and dual-push the desktop checkpoint.
