# Simplified Sync v2 offline acceptance — Fedora

## Scope and source

Task 8 validates the approved current-state protocol and prepares an isolated
candidate without launching it. Runtime source is
`forge/reasonnotes-completion` at
`3a6d68446b2829235f8a2f5b78e7d461498e0744`. Production ReasonNotes, personal
notes, global desktop/KDE Connect settings, and Android were untouched.

## Cross-platform fixtures

`tests/test_sync_v2_cross_platform.py` and Android's
`CrossPlatformV2AcceptanceTest` reproduce one deterministic eight-file
transcript with their native implementations. All carrier bytes and SHA-256
names agree across Python and Java. Fedora imports Android carriers through the
real v2 inbox scanner, preserves both complete independent edits, resolves with
both parent IDs, imports Android deletion, rejects stale resurrection, emits a
second-note Fedora deletion, and verifies deleted titles/bodies are absent from
durable storage. The exact acknowledgment fixture names Android's deletion.

Existing v2 tests additionally cover duplicate delivery, restart persistence,
unreachable-peer retry, unrelated-note progress, selection, old-v1 transition
import, and exact acknowledgment convergence. The candidate entrypoint now
opens only the explicitly supplied `CurrentNoteStore`; it does not attach the
legacy receipt-return or foreground-purge paths.

## Verification

The suite ran with isolated HOME/XDG/TMP roots and read-only copies of the
active qt6ct/Kvantum configuration. Result: 331/331 tests passed. Five methods
that explicitly start the application process were excluded to honor Task 8's
no-launch boundary and were named in the test output:

- two candidate installer check-launch tests;
- the bootstrap check-launch test; and
- the lifecycle check-launch and runtime-probe tests.

Focused cross-platform/bootstrap verification separately passed 5/5. The
native Wayland blur helper compiled successfully during candidate preparation.
The application itself was not started.

## Candidate and isolation

- Immutable release:
  `/home/reason/Temporary/ReasonNotes-Sync-v2-Candidates/desktop/install/releases/3a6d68446b2829235f8a2f5b78e7d461498e0744`
- Archive:
  `/home/reason/Temporary/ReasonNotes-Sync-v2-Candidates/desktop/ReasonNotes-Fedora-Sync-v2-3a6d684.tar.gz`
- Archive size: 35,522,367 bytes
- Archive SHA-256:
  `750843eac45682721ba2bbae9ea5f05e55344d97a4e3b2e3f86fe354b2e018a4`
- Launch procedure:
  `/home/reason/Temporary/ReasonNotes-Sync-v2-Candidates/desktop/LAUNCH_PROCEDURE.txt`
- Disposable runtime root:
  `/home/reason/Temporary/ReasonNotes-Sync-v2-Physical-Test/`

The fail-closed isolation preflight resolved HOME, every XDG root, repository,
inbox, and received directory beneath that disposable root and reported zero
conflicting ReasonNotes processes. The packaged source matches the checkpoint;
only source-tree `__pycache__` directories were intentionally absent, and the
candidate adds its compiled native helper.

The isolated received directory is not the account's normal KDE Connect
Downloads destination. Before Android-to-Fedora physical acceptance, a
separately authorized test must establish a non-global way to place the single
test carrier there. Global KDE Connect settings must not be changed merely to
make this candidate work.

## Migration and remaining acceptance

The isolated launcher treats `--root` as an already-current v2 store. It does
not migrate legacy or production data at launch. Production migration and
cutover remain separate, destructive, owner-gated work.

Still unverified physically: Android migration/installation, actual KDE
Connect delivery in each direction, durable acknowledgments, conflict-choice
presentation and convergence, permanent deletion in both directions,
unreachable-peer retry, restart persistence, and final production cutover.
