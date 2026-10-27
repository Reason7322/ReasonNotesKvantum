# ReasonNotes Public Release and Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish the accepted Fedora and Android ReasonNotes 0.1 applications under MIT and remove only verified obsolete Fedora installations/data.

**Architecture:** Keep the existing platform repositories, fast-forward their default branches to the accepted release branches, and host one canonical `v0.1.0` release in `Reason7322/ReasonNotes`. Reuse accepted binaries byte-for-byte, stage them in ignored workspace, and verify publication and cleanup against exact hashes and protected-path snapshots.

**Tech Stack:** Git, GitHub CLI, RPM, Android APK/Gradle metadata, Markdown, Fedora desktop integration, SHA-256.

**Spec:** `docs/superpowers/specs/2026-10-27-public-release-and-cleanup-design.md`

## Global Constraints

- Do not change application logic, synchronization behavior, installed RPM, Android installation, live notes, or the verified backup.
- Do not rewrite history, force-push, migrate repositories, launch applications, or build replacement binaries.
- Publish only after both exact histories pass the focused private-data and credential scan.
- Preserve all unrelated Trash content; resolve every cleanup target explicitly.
- Use Fedora source `cdf63233d2956718e5353ed58ad230dad07aad91`, RPM SHA-256 `ef734264722788d6222312c9608bf6ab2866411942477fad871cc9ae9f26bb11`, Android source `98b094f`, and APK SHA-256 `d0aef58c05567a928e4aad35ee2535988aeb01582458b64e7ee8cf1fce3d27d8`.

## Review Focus

- A public visitor lands on `main` and can find both platform sources and the canonical release.
- Release assets retain the accepted hashes after rename/upload/download.
- The MIT change does not overwrite Lucide, Gradle, AndroidX, Gson, Qt, KDE Connect, or other third-party terms.
- Cleanup cannot traverse into the lowercase live data root, backup, or unrelated Trash entries.
- The live sync ledger may differ from the recovery baseline and must remain unchanged across cleanup.

---

### Task 1: Publication materials and licensing

**Files:**
- Create: `LICENSE`, `THIRD_PARTY_NOTICES.md`, `docs/RELEASE_0.1.0.md` in both repositories
- Modify: `README.md` in both repositories
- Modify: `packaging/rpm/reasonnotes.spec`, `tests/test_rpm_packaging.py` in the Fedora repository

**Interfaces:**
- Consumes: accepted source/artifact identities from the spec
- Produces: matching public project description, build/install instructions, license metadata, and release provenance

- [ ] Add a failing Fedora packaging assertion requiring `License: MIT` and removing private-package wording; run it and confirm the expected RED.
- [ ] Add the standard MIT license with `Copyright (c) 2026 Reason7322` to both repositories.
- [ ] Replace both READMEs with actual Fedora/Android features, manual KDE Connect flow, install/build instructions, requirements, limitations, cross-links, and release link; omit screenshots.
- [ ] Add third-party notices without relicensing dependencies or vendored assets.
- [ ] Add release provenance and accepted hashes; update the future Fedora spec metadata to MIT/public wording.
- [ ] Run focused documentation/license checks and the Fedora packaging test GREEN; commit each repository independently.

### Task 2: Verified Fedora cleanup

**Files:**
- Remove external paths only after resolving them against the spec and backup
- Modify: `PROJECT_STATUS.md` and `handoffs/FORGE_TO_QWEN.md` in the Fedora repository

**Interfaces:**
- Consumes: protected backup manifest and live-state snapshot
- Produces: one RPM-managed launcher, no legacy roots/icons/manual app files, unchanged live/backup hashes

- [ ] Capture hashes/counts for live repository state and verify the backup manifest and legacy-root backup equality.
- [ ] Move the two legacy data roots and redundant physical-test tree to Trash using exact paths.
- [ ] Remove only resolved ReasonNotes legacy installations, icons, bundles, screenshots, and their matching Trash metadata; do not touch unrelated entries.
- [ ] Refresh desktop/icon caches and verify one launcher/desktop entry, RPM integrity, six current notes, unchanged live sync state, and unchanged backup manifest.
- [ ] Record exact removed/protected paths and commit the Fedora status/handoff update.

### Task 3: Dual-remote source publication

**Files:**
- No additional product files

**Interfaces:**
- Consumes: clean release commits from Tasks 1-2
- Produces: matching local/handoff/GitHub release-branch and `main` SHAs

- [ ] Repeat focused object-database scans for credentials, sensitive filenames, and literal active-note content.
- [ ] Push each release branch to `handoff` and `github`; verify full remote SHAs.
- [ ] Fast-forward each local and remote `main` to its release commit; verify full local/handoff/GitHub SHAs without force.
- [ ] Change both GitHub repositories to public and verify visibility/default branches via GitHub and unauthenticated HTTP.

### Task 4: Canonical binary release

**Files:**
- Create ignored staging copies of the accepted RPM/APK and `SHA256SUMS`

**Interfaces:**
- Consumes: accepted binaries and published source commits
- Produces: public `v0.1.0` release with three verified assets

- [ ] Copy the accepted APK under the public filename and the accepted RPM into ignored staging; verify hashes and APK/RPM identity.
- [ ] Create `v0.1.0` on the Android/umbrella release commit with notes linking both exact source commits.
- [ ] Upload the RPM, APK, and `SHA256SUMS`; verify names, sizes, API digests where available, and downloaded SHA-256 values.
- [ ] Verify public repository, source, release, and direct download URLs without relying on authenticated-only access.

### Task 5: Final release checkpoint

**Files:**
- Modify: `PROJECT_STATUS.md`, `handoffs/FORGE_TO_QWEN.md` in both repositories

**Interfaces:**
- Consumes: verified public URLs, artifact hashes, cleanup results, and remote SHAs
- Produces: final operational record and dual-remote checkpoint

- [ ] Record public URLs, release asset identities, exact removed/protected paths, source commits, and verification evidence in both repositories.
- [ ] Run final documentation, artifact, public-access, backup/live-data, RPM, launcher, and clean-worktree checks.
- [ ] Commit and push the final documentation-only checkpoints to both remotes and fast-forward both public `main` branches.
- [ ] Independently verify every full local/handoff/GitHub SHA and stop.
