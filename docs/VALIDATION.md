# Validation evidence

Date: 2026-10-18 (Europe/Warsaw)

This document separates source checks, automated tests, built artifacts,
actual graphical runtime evidence, and acceptance that remains with the owner.

## Source and provenance

- Destination bootstrap: `8f8ad43678f0a17856b6f22f77e8ada58c91f323`.
- Imported source baseline:
  `873dcd524179abc39ae708b055c76f2798af1e48`.
- The original source worktree still reported that exact SHA and no changes.
- The destination `main` worktree still reported the bootstrap SHA and no
  changes. All implementation is on `forge/qtwidgets-rewrite`.
- No Kvantum SVG, `.kvconfig`, application palette, QSS, or application theme
  selector is present in the Widgets implementation.

## Automated tests

Command:

```sh
QT_QPA_PLATFORM=offscreen PYTHONPATH=src \
  /usr/bin/python3 -m unittest discover -s tests -v
```

Result after whole-branch review fixes: **217 tests passed** in 5.462 seconds.
Coverage includes imported
backend regressions and native Widgets bootstrap, models/controller, editor,
sidebar selection, localization, Sync, Conflict, lifecycle, installer, and
Wayland-blur behavior. Python emitted a three-object uncollectable
`ResourceWarning` at interpreter shutdown after the successful PySide test run;
no test failed.

The fresh whole-branch review identified six Important interaction/safety
defects and no Critical defects. Each Important issue received a regression
that was observed failing before the fix: editor caret/undo retention, native
Sync checkboxes, native Ctrl/Shift selection, stale deletion confirmation,
candidate activation target validation, and canonical production-path checks
under an overridden XDG data home. All were green in the 217-test final run.

The purge protocol tests opened only loopback sockets and used disposable
repositories. Candidate installer tests used temporary homes with production
marker files and proved those files were unchanged.

## Build and launch

The native helper built successfully with:

```sh
/usr/bin/python3 scripts/build-wayland-blur.py --target linux-app/native
```

Built helper SHA-256:
`724dad85b3f2d5c3c71fbb8d0acc0ec76460e8c429b0bb97103c38ecb92f55cc`.

The versioned installer was exercised under
`/tmp/reasonnotes-kvantum-install-FETEfX`, including a compiled helper and a
successful installed-launcher `--check-launch`. No home candidate or production
installation was changed during that temporary exercise.

After review fixes, implementation commit
`83f9b339518459259370da9569730ec1d504c22d` was installed through the same
installer at the candidate-only paths and passed both offscreen
`--check-launch` and an actual bounded Wayland probe. The installed candidate
launcher SHA-256 was
`dce194190973cb08a37cbc04dffe85c1dea5dd55add6b1144c5ca6f95da4acda`.
The production launcher hash remained
`05406228cadb43bcb6ad37be63d057d645c90e286a5ba8632c64d28c10e66eca`
before and after installation.

## Actual Hyprland/Wayland runtime

The source candidate was displayed on the active Hyprland session for a bounded
probe using explicit disposable repository, inbox, received, XDG data, and XDG
config paths under `/tmp/reasonnotes-kvantum-wayland-Q5LLdI`.

Observed process evidence:

```text
RUNTIME_STYLE=kvantum
RUNTIME_PLATFORM=wayland
RUNTIME_BLUR_ACTIVE=1
RUNTIME_BLUR_ERROR=
RUNTIME_DATA_ROOT=/tmp/reasonnotes-kvantum-wayland-Q5LLdI/data3/ReasonNotesKvantum-candidate
RUNTIME_PURGE_RELAY=disabled-for-probe
```

Hyprland independently reported a native (non-XWayland) client class
`org.reasonnotes.ReasonNotesKvantum`. A composited capture was inspected at
`/tmp/reasonnotes-kvantum-wayland-Q5LLdI/runtime-fixed.png`, SHA-256
`043465b67b79b4ec102d4e1463aa2495f8cac597a51ae8b9c52e132942b4bb53`.
The capture visibly showed the system material and compositor-blurred backdrop,
native controls, the permanent sidebar, and the corrected wide editor column.
This is actual runtime evidence, not a claim that the app is identical to
Dolphin and not a substitute for owner visual acceptance.

The bounded probe disabled the foreground purge listener to avoid colliding
with any running production instance. Relay authentication, lifecycle, purge,
and teardown are covered by isolated socket and runtime tests.

The exact installed candidate was also probed after packaging and reported
`wayland`, `kvantum`, blur active, no blur error, and candidate data root
`/home/reason/.local/share/ReasonNotesKvantum-candidate`.

## System-style evidence

- Qt version observed: 6.11.2.
- Installed plugin:
  `/usr/lib64/qt6/plugins/styles/libkvantum.so`.
- Plugin SHA-256:
  `927508d712efda8b2c0c9bc9a5ef9f9028b4328fcf65de46306910a3b190aa9a`.
- The application calls `QStyleFactory.create("kvantum")` and fails clearly if
  the installed style is unavailable. It never selects or changes a Kvantum
  theme, so the system's current theme is used on each launch.

## Production isolation

- Production launcher observed, not modified:
  `/home/reason/.local/bin/reasonnotes`, SHA-256
  `05406228cadb43bcb6ad37be63d057d645c90e286a5ba8632c64d28c10e66eca`.
- No command targeted the production release, note repository, settings,
  desktop entry, Kvantum configuration, Hyprland configuration, or Android
  private data.
- Candidate defaults to `ReasonNotesKvantum-candidate`, rejects production data
  paths, uses distinct QSettings/application IDs, and has a distinct launcher
  and desktop-entry template.

## Not yet owner-accepted

- Subjective visual approval, including comparison with the owner's preferred
  Dolphin appearance.
- Physical Android interoperability and device-side UX using disposable test
  notes. No device mutation was attempted during engineering validation.
- Production installation, live-data migration, launcher switch, or rollback
  rehearsal. These remain explicitly gated by owner approval.

## Integrated release-candidate refresh — 2026-10-21

The Qwen Mission 03/05/06 UI checkpoint was integrated on
`forge/reasonnotes-completion`. The complete isolated suite now passes 243/243.
An exact temporary immutable release passed packaged launch, native helper,
two-release rollback, native Workspace 10 runtime, and existing-format
compatibility against a byte-for-byte temporary copy of current production
data. The installed candidate and production remained unchanged.

See `RELEASE_CANDIDATE_VALIDATION_2026-10-21.md` for artifact hashes and
full-resolution captures, and `ANDROID_PHYSICAL_ACCEPTANCE.md` for the
remaining owner-authorized device sequence.

## Owner-requested UI corrections — 2026-10-21

The subsequent bounded pass makes the sidebar splitter visually blank in all
states while retaining its real drag target and persisted width, and removes
the dedicated rule below the title. The complete isolated suite remains
243/243 green. The exact temporary package ran on native Wayland with
`qt6ct-style`, active blur, no helper error, Kitty-equivalent material, and a
clean exit. Rest/hover divider crops had zero differing pixels.

See `UI_CORRECTIONS_VALIDATION_2026-10-21.md` for the code identity, test
evidence, production-isolation hashes, and full-resolution captures. Owner
visual acceptance remains pending; Android testing and production cutover were
not performed.
