# Native RPM Cutover Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Install the accepted `cdf6323` ReasonNotes desktop application as the sole RPM-managed desktop version while preserving all note data.

**Architecture:** Package an exact Git archive of the accepted commit and add only RPM-owned launcher/integration files around it. Back up all note stores, promote the accepted store to a stable live path, install and verify the RPM, then retire obsolete manual app paths.

**Tech Stack:** RPM spec/rpmbuild, Python 3.14, PySide6 6.11, Qt 6/Kvantum, Wayland client helper, KDE Connect.

**Spec:** `docs/superpowers/specs/2026-10-27-native-rpm-cutover-design.md`

## Global Constraints

- Runtime application source is exactly commit `cdf63233d2956718e5353ed58ad230dad07aad91`.
- Do not touch or synchronize Android.
- Back up and verify all note data before live cutover.
- Delete obsolete application installations only after package verification.
- Retain one launcher and one desktop entry.

## Review Focus

- XDG data paths containing spaces must remain correctly quoted by the launcher.
- Missing `XDG_DATA_HOME` must resolve to `$HOME/.local/share/reasonnotes`.
- The source archive must resolve to the accepted full commit, not current HEAD.
- RPM dependencies must name Fedora packages that provide the existing runtime.
- Cleanup must target only the inventoried ReasonNotes application paths.

---

### Task 1: Reproducible RPM definition

**Files:**
- Create: `packaging/rpm/reasonnotes.spec`
- Create: `packaging/rpm/reasonnotes`
- Create: `packaging/rpm/org.reasonnotes.ReasonNotesKvantum.desktop`
- Create: `scripts/build-rpm.py`
- Test: `tests/test_rpm_packaging.py`

**Interfaces:**
- Consumes: exact source commit and existing `scripts/build-wayland-blur.py`.
- Produces: `dist/rpm/reasonnotes-0.1.0-1.cdf6323*.x86_64.rpm`.

- [ ] Write packaging tests for exact source revision, launcher path quoting,
  system integration paths, required dependencies, and output naming.
- [ ] Run the focused test and confirm it fails because RPM files are absent.
- [ ] Add the launcher, desktop entry, RPM spec, and deterministic build driver.
- [ ] Run the focused packaging test and confirm it passes.
- [ ] Commit the reproducible package definition.

### Task 2: Build and inspect the RPM

**Files:**
- Build output: `dist/rpm/*.rpm`

**Interfaces:**
- Consumes: Task 1 build driver.
- Produces: a locally installable Fedora x86_64 RPM and package metadata report.

- [ ] Install only the missing `rpm-build` build tool.
- [ ] Build the RPM from the exact accepted Git archive.
- [ ] Verify package NEVRA, payload paths, dependencies, source revision marker,
  desktop file, and RPM signature/digest integrity.

### Task 3: Back up and promote accepted data

**Files:**
- Create: `/ssd-storage/Backups/ReasonNotes/<timestamp>/`
- Create: `/home/reason/.local/share/reasonnotes/repository/`

**Interfaces:**
- Consumes: three inventoried note stores and the accepted physical-test store.
- Produces: verified backup plus a live store matching the accepted store.

- [ ] Copy all note stores into a dated backup without changing the sources.
- [ ] Generate and independently verify a SHA-256 manifest and file counts.
- [ ] Stage and atomically promote the accepted repository to the new live path.
- [ ] Verify live and accepted repository manifests match.

### Task 4: Install, verify, and retire older apps

**Files:**
- Install: `/usr/bin/reasonnotes`, `%{_libdir}/reasonnotes/`, and system desktop/icon files.
- Retire: exact inventoried paths under `~/.local/bin`, `~/.local/opt`, and `~/.local/share/applications`.

**Interfaces:**
- Consumes: Task 2 RPM and Task 3 live repository.
- Produces: one installed ReasonNotes application with recoverable data.

- [ ] Install the local RPM with DNF.
- [ ] Verify RPM ownership/digests and run `reasonnotes --check-launch`.
- [ ] Reverify the six live note IDs and repository integrity.
- [ ] Move only the inventoried obsolete application paths to desktop trash.
- [ ] Refresh desktop metadata and verify one launcher, one desktop entry, no
  obsolete installed paths, and a clean application process state.

