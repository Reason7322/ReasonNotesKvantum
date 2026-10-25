# Forge -> Qwen directional handoff

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
  selects the sibling v2 directory, and only then retires the legacy root.
  Interrupted staging is rebuilt; malformed/missing/three-head histories fail
  closed with legacy data retained.
- Verification: 19/19 focused current-store, migration, and canonical-envelope
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
