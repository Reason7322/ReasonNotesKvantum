# Current-operation Sync Status Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Report current sync success/failure without contamination from unrelated exhausted historical receipts.

**Architecture:** Keep durable historical ledger state, but scope the returned SyncReport and presenter message to items planned or processed by the current operation; expose unrelated attention separately.

**Tech Stack:** Python 3, unittest, PySide6.

**Spec:** `docs/superpowers/specs/2026-10-24-current-operation-sync-status-design.md`

## Global Constraints

- Preserve approved UI, JSON v1, histories, and ledgers.
- Never hide a failure affecting the current note or claim durable success without receipt evidence.

## Review Focus

- Historical exhausted receipt plus successful current import reports current success.
- Current transfer failure remains an error.
- Current waiting receipt remains pending, not success.
- Historical attention remains discoverable.
- Selected-note status never incorporates unselected notes.

---

### Task 1: Scope sync reports

**Files:** Modify the existing sync orchestration/report module and focused tests identified by `rg SyncReport`.

- [ ] Add RED regressions for historical-attention isolation and current failure/pending behavior.
- [ ] Implement minimal per-operation scoping without deleting ledger rows.
- [ ] Run focused sync and Widgets presenter tests GREEN; commit.

### Task 2: Status and checkpoint

**Files:** Modify `PROJECT_STATUS.md`.

- [ ] Record behavior, tests, and remaining physical verification.
- [ ] Run `git diff --check`, commit, dual-push, and verify remote SHAs.
