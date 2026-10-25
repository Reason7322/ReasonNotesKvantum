# Forge -> Qwen directional handoff

## 2026-10-25 checkpoint — simplified sync v2 Task 8 partial

- Original goal: save/edit on Fedora and Android, explicit Sync transfer,
  complete two-version conflict choice, and permanent bidirectional deletion.
- Added the shared deterministic eight-carrier JSON fixture transcript and a
  Fedora test that consumes Android carriers through the real v2 inbox scanner.
- Verified byte-identical generation, create/import, edit/edit conflict,
  selected resolution, exact ack, permanent deletion in both directions,
  stale-state rejection, and deleted-content absence.
- The desktop entrypoint now opens the isolated `CurrentNoteStore` directly and
  does not attach legacy receipt-return or foreground-purge mechanisms. It does
  not migrate production or legacy candidate data.
- Focused result: 5/5 PASS. Android counterpart focused result: 2/2 PASS.
- Task 8 remains incomplete: full suites, Android APK build, isolated Fedora
  archive, acceptance documentation, hashes, and final checkpoint remain.
- No launch, installation, personal migration, KDE Connect transfer, or
  physical synchronization occurred.

## 2026-10-25 checkpoint — simplified sync v2 Task 8 complete offline

- Runtime source checkpoint: `3a6d68446b2829235f8a2f5b78e7d461498e0744`.
- Shared Java/Python carriers are byte-identical and cover create, edit/edit
  conflict, selected resolution, exact acknowledgment and permanent deletion
  in both directions without retaining deleted content.
- Fedora offline suite: 331/331 PASS; five application-process launch tests
  excluded by the explicit no-launch boundary.
- Immutable archive:
  `/home/reason/Temporary/ReasonNotes-Sync-v2-Candidates/desktop/ReasonNotes-Fedora-Sync-v2-3a6d684.tar.gz`;
  SHA-256 `750843eac45682721ba2bbae9ea5f05e55344d97a4e3b2e3f86fe354b2e018a4`.
- Exact future procedure is at
  `/home/reason/Temporary/ReasonNotes-Sync-v2-Candidates/desktop/LAUNCH_PROCEDURE.txt`.
- Isolation preflight passed with all runtime roots under the disposable
  physical-test tree and zero conflicting ReasonNotes processes.
- No launch, install, migration, KDE Connect transfer, or physical sync.
  Physical product acceptance and production cutover remain pending.

## 2026-10-25 checkpoint — simplified sync v2 Fedora Task 7 complete

- Incoming Task 6 checkpoint:
  `773cf53f1c851a9ef19b90877aacb0452adf4afe`.
- The existing JSON bundle now validates and transports `state-v2` and `ack-v2`
  alongside transition-only v1 revision/receipt items.
- `scan_inbox`, `sync_linux` and `sync_linux_confirmed` adapt automatically to
  `CurrentNoteStore`: state is applied durably before acknowledgments, exact
  acknowledgments clear pending changes, selection sends one latest state per
  note, and peer confirmation remains distinct from transfer acceptance.
- V2 status reads only current pending/conflict state. Old delivery ledgers and
  receipts do not affect current operations; failure of one note does not block
  independent state transfer, and failed/unreachable requests remain retryable.
- Durable source-occurrence markers prevent unchanged received files from
  repeatedly requeueing acknowledgments after restart while permitting actual
  redelivery to regenerate a lost acknowledgment. Migration separately seeds
  known v1 revision markers before retirement. Deleted-note fences reject
  stale live carriers without recurring stale-file errors.
- The CLI supports explicit `--current-state` v2 status/scan/sync operation;
  Fedora emits no new v1 revisions from this path but still imports valid v1
  revisions during transition.
- Verification: 96 focused tests pass (v2/current store/migration 31 and CLI,
  bundles, legacy sync interactions and offscreen Widgets compatibility 65).
  Disposable roots were kept in the plan-specific workspace, not `/tmp`.
- No launch, deployment, personal migration/data access, KDE Connect transfer,
  physical synchronization, Android action or UI redesign occurred.
- Product remains incomplete. Task 8 candidate integration and cross-platform
  offline acceptance is the potential next milestone and is not authorized by
  this checkpoint.

## 2026-10-25 checkpoint — simplified sync v2 Fedora Task 6 complete

- Incoming RED checkpoint:
  `009426769f0caeaf7f02ae97ad2a100e6c76247e`.
- `NoteService` now adapts the Task 5 current-state store for create/open/edit,
  listing/search, permanent deletion, complete conflict choice, pending state,
  delivery labels and the sync catalogue. Legacy repository behavior remains
  available until the separately authorized Task 7 transport conversion.
- `NotePresenter` and `WidgetsController` use service-level state/head/deletion
  queries rather than reaching into the legacy revision graph.
- Current-state conflict Widgets receive both complete versions; selecting one
  writes exactly one pending resolution and removes the losing candidate.
- Protected source contracts confirm the approved sidebar, material and editor
  implementation files are byte-identical to their accepted versions.
- Verification: required Task 6 slice 24/24; legacy presenter 21/21, controller
  6/6, selection 7/7 and main-window 10/10, each with a clean zero exit;
  compilation and `git diff --check` pass. A single interpreter combining the
  four Qt modules aborts only during teardown after reporting all assertions
  OK, so the modules were verified independently rather than counting that run.
- No application launch, deployment, personal data, migration, physical sync,
  KDE Connect action, Android action or visual redesign occurred.
- Product remains incomplete. Task 7 transport adaptation is the potential next
  milestone, but it is not authorized by this checkpoint.

## 2026-10-25 checkpoint — simplified sync v2 Fedora Task 5 complete

- Original goal: save/edit on Fedora and Android, explicit Sync transfer,
  complete two-version conflict choice, and permanent bidirectional deletion.
- Incoming checkpoint: Task 1 Fedora envelopes at
  `7de5e4678c671dcd6d6a8dc813b46d000f530ec7`.
- Completed milestone: Fedora current-state store and restartable one-time
  migration from immutable legacy history.
- `CurrentNoteStore` persists one live record and one coalesced pending state,
  exact acknowledgments, two complete conflict candidates, and content-free
  deletion fences using fsync plus atomic replacement.
- Deletion permanently removes current/conflict content and blocks stale live
  carriers. Independent deletions acknowledge without resurrection. A remote
  descendant clears the obsolete pending ancestor already known by that peer.
- Migration is read-only against the old repository until activation: it stages,
  reopens and validates exact current/conflict/deletion/pending state, atomically
  selects the sibling v2 directory, and only then atomically renames and retires
  the legacy root. Interrupted staging is rebuilt; interrupted retirement
  resumes without deriving partial history; malformed/missing/three-head
  histories fail closed with legacy data retained.
- Verification: 21/21 focused current-store, migration, and canonical-envelope
  tests pass using disposable repositories.
- Runtime/deployment: no application launch, production migration, personal
  note access, installation, KDE Connect transfer, or Android action occurred.
- Product remains incomplete. Potential next action is Fedora Task 6 service
  and approved Widgets adapters; it is not authorized by this checkpoint.

## 2026-10-23 JSON v1 Fedora candidate checkpoint

- Original goal: reliable bidirectional synchronization with visible progress,
  explicit failures, and success only after durable import confirmation.
- Authorized milestone: package the JSON-compatible desktop checkpoint in
  isolation, prove Android JSON v1/receipt compatibility offline, document the
  future isolated launch, and stop before launching or synchronization.
- Source: `forge/reasonnotes-completion` at
  `88def77e2bfe3c6b2b92897b5d134395a761ffd3`; no UI/protocol source change.
- Focused tests: `tests.test_transport_bundle tests.test_bundle_transport`,
  20/20 passed, including the exact Android-matching canonical Unicode fixture,
  full-carrier validation, revision+receipt import, duplicates, and confirmation.
- Artifact: `/home/reason/Temporary/ReasonNotes-JSON-v1-Candidates/desktop/ReasonNotes-Fedora-JSON-v1-88def77.tar.gz`,
  SHA-256 `41961dbb0945d2a0294374f92386650d3ec7342e6397db8aa3c2c4082953194e`.
- Isolation/launch: exact candidate-only HOME/XDG/repository/inbox/received
  command is in `docs/JSON_V1_CANDIDATE_PREPARATION_2026-10-23.md`; it was not
  executed. Confirm the dated Android KDE Connect device ID at the physical gate.
- Production, Android, KDE Connect configuration, and shared theme state were
  untouched.
- Remaining acceptance: separately authorized physical bidirectional JSON v1
  sync and durable confirmation, then separately authorized production cutover.
- One potential next action: owner-authorized physical candidate test; not
  authorized by this checkpoint.


No ownership transfer is currently requested. This is the compact continuation
point if another engineering shift becomes necessary.

## Objective and branch

- Branch: `forge/reasonnotes-completion`
- Incoming Qwen checkpoint:
  `9374dce9d75b3c87002b3debe50a6eaf071bae62`
- Objective: complete and safely deliver the native Qt Widgets/Kvantum
  ReasonNotes replacement with full note/sync compatibility. Product remains
  incomplete until visual acceptance, physical Android validation, and
  authorized production cutover all pass.

## Current evidence

- Owner-requested narrow correction after checkpoint `eea2304`: the real
  splitter handle remains draggable and persisted, but is now visually blank
  at rest and on hover; the dedicated title rule is removed. Fonts, Settings,
  materials, and backend behavior were not changed.
- Integrated suite: 243/243 passed in the isolated qt6ct/Kvantum environment;
  the four affected Widgets suites pass 34/34.
- Offline Android fixture: production and non-empty targets rejected; fixed
  Unicode/conflict/deletion notes reopen from immutable history; no transfer
  attempts occur during preparation.
- Exact source: built as a temporary immutable release with native Wayland
  helper; packaged check-launch and two-release candidate rollback passed.
- Existing format: a byte-for-byte temporary copy of current production data
  reopened as 187 revisions, 6 live notes, and 16 purge fences; immutable
  history remained unchanged.
- Actual Workspace 10 after the correction: native Wayland,
  `qt6ct-style -> kvantum`, blur active, no helper error, Kitty-equivalent
  mode, clean shutdown. The divider's rest/hover crops have zero differing
  pixels and the title-rule crop shows the requested removal. Evidence is in
  `docs/evidence/ui-corrections-2026-10-21/`.
- Production, installed candidate, phone, KDE Connect, and global desktop/theme
  state were not changed.

See `docs/UI_CORRECTIONS_VALIDATION_2026-10-21.md`,
`docs/RELEASE_CANDIDATE_VALIDATION_2026-10-21.md`, and
`docs/ANDROID_PHYSICAL_ACCEPTANCE.md` for exact hashes and procedures.

## Smallest next action

Reason must inspect and accept or reject the updated two-correction visual
evidence. Per the owner's explicit sequence, do not begin the documented
physical Android test until that review passes. Only after visual and device
acceptance should a separately authorized production migration/cutover
checkpoint be prepared. Do not touch the installed candidate, production
data/launcher, phone, or `main` before those gates.
