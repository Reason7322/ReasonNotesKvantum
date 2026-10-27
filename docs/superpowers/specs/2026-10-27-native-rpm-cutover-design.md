# Native RPM Cutover Design

## Intent

Make the owner-accepted desktop application at Git commit
`cdf63233d2956718e5353ed58ad230dad07aad91` the only installed ReasonNotes
desktop application. The result is one RPM-managed launcher and desktop entry,
using the six-note store accepted during physical Android/Fedora testing.

## Constraints

- The RPM payload must use the application source from exactly `cdf6323`.
- Do not modify or synchronize the Android app.
- Preserve note data before cutover and verify the backup by manifest.
- Do not merge older stores into the accepted store.
- Remove the two manual application release trees, their launchers, and their
  duplicate desktop entries only after the RPM and live data are verified.
- Do not retain an installed candidate alongside the production app.

## Approach

Build a Fedora x86_64 RPM whose runtime payload is produced from a Git archive
of `cdf6323`. The package owns `/usr/bin/reasonnotes`, an application tree under
`%{_libdir}/reasonnotes`, one system desktop entry, and one system icon. A small
launcher supplies a stable user data path under
`$XDG_DATA_HOME/reasonnotes`; this preserves the accepted application code and
uses its supported explicit-path interface.

Before installation, create a dated backup containing all three existing note
stores and a SHA-256 manifest. Promote a byte-for-byte copy of the accepted
physical-test repository to the new live data path. Install and verify the RPM,
run its non-visual launch check, compare live note IDs and file hashes with the
accepted store, then move the obsolete manual application paths to the desktop
trash. The data backup remains outside the installed application paths.

## Alternatives considered

- Keep the candidate beside production: rejected because the owner wants one
  version only.
- Rewrite the accepted source into a new production mode: rejected because it
  would no longer be the exact accepted application payload.
- Reuse the legacy production store directly: rejected because the accepted
  synchronized current-state store is the proven final state.

## Success criteria

- `rpm -q reasonnotes` reports the package built from `cdf6323`.
- `/usr/bin/reasonnotes` and exactly one ReasonNotes desktop entry are active.
- The live repository matches the accepted repository before first launch.
- `reasonnotes --check-launch` exits successfully.
- No old manual launcher, release tree, or candidate desktop entry remains in
  its former location.
- The verified data backup and built RPM are retained and reported.

