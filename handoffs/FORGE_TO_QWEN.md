# Forge -> Qwen directional handoff

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
