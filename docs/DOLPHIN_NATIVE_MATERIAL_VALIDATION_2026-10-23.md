# Dolphin-native material candidate validation — 2026-10-23

## Result

A separately staged Qt Widgets candidate is ready for controlled visual review.
It was not installed or launched interactively. The owner-supplied Dolphin
comparison remains the visual authority, and owner acceptance is pending.

The working installed baseline remains
`/home/reason/.local/bin/reasonnotes-kvantum-candidate`, whose launcher SHA-256
is `dce194190973cb08a37cbc04dffe85c1dea5dd55add6b1144c5ca6f95da4acda`.
It resolves to the existing `88def77e2bfe3c6b2b92897b5d134395a761ffd3`
release and was not replaced.

## Source and correction

Candidate implementation source is commit
`95923d8dc66d73b63eda94bd7ffc970ce1a53b1d` on
`forge/reasonnotes-completion`.

- The default top-level, navigation rail, cards, and search surrounds delegate
  their surfaces to the active `QStyle` via `PE_Widget`.
- The editor no longer assigns `#2C3539` or any replacement color. Title,
  body, search, and list surfaces retain native widget palettes and frames.
- The sidebar splitter no longer receives a transparent palette or a custom
  paint-suppression proxy; Kvantum owns its separation and interaction states.
- Bootstrap preserves a valid `qt6ct-style -> kvantum` chain. If no Kvantum
  leaf exists and Kvantum cannot be loaded, startup fails explicitly without
  installing an application fallback palette.
- Legacy custom material code remains diagnostic-only and is not selected by
  the packaged default.

No literal color, fixed opacity, invented tint, or fallback palette is applied
by the new default surface path.

## Focused verification

The following focused integrated command passed 58 tests:

```sh
PYTHONPATH=src /usr/bin/python3 -m unittest \
  tests.test_candidate_install tests.test_widgets_bootstrap \
  tests.test_widgets_native_material tests.test_widgets_visual_polish \
  tests.test_widgets_main_window -v
```

Coverage includes native material delegation, active/inactive/disabled editor
palette behavior, editing/focus/autosave/layout behavior, real
`qt6ct-style -> kvantum` preservation, explicit missing-Kvantum failure,
canonical and symlink path checks, broad-parent rejection, inherited HOME/XDG
checks, concurrent-process rejection, and sentinel-protected check-launch
writes. The complete historical suite was not rerun because the change is
bounded to styling, bootstrap validation, and candidate isolation.

The native Wayland helper built successfully while staging. A staged offscreen
probe reported:

```text
STYLE_CHAIN=qt6ct-style -> kvantum
WINDOW_MATERIAL=native-kvantum
OFFSCREEN_IMAGE_SAVED=1
```

The offscreen render is
`/home/reason/Temporary/ReasonNotes-Dolphin-Native-Candidate/evidence/offscreen-native-material.png`
(SHA-256 `76933dc0c81af040327b225fa841352447fe872a05c02d79b6f7bae75af60efe`).
It shows a coherent style-owned editor/sidebar render, but it cannot prove
compositor behavior or whether the real-Wayland desktop-coordinate patches are
reduced. That requires a matched Dolphin comparison after separate launch
authorization.

## Candidate identity

- Root: `/home/reason/Temporary/ReasonNotes-Dolphin-Native-Candidate/`
- Current immutable release:
  `/home/reason/Temporary/ReasonNotes-Dolphin-Native-Candidate/app/releases/95923d8dc66d73b63eda94bd7ffc970ce1a53b1d/`
- Launcher:
  `/home/reason/Temporary/ReasonNotes-Dolphin-Native-Candidate/bin/reasonnotes-dolphin-native`
- Archive:
  `/home/reason/Temporary/ReasonNotes-Dolphin-Native-Candidate-95923d8.tar.gz`
- Archive SHA-256:
  `32c798b5a7a087e9f10bd50a434c9f439abf7984ee0000a480e2a03617073bd6`
- Launcher SHA-256:
  `3b8040cd55d432d69ef568b8a9bd72e6195539cd3700c140118c61b038bf49f9`
- Native helper SHA-256:
  `e7bb3e6269419810f884c8aa1294a9eba5ddb39e60d071e295cb54538a3e02c4`

The copied qt6ct and Kvantum configuration is read-only beneath the candidate
root. No global theme setting was changed.

## Isolation evidence and future launch gate

The earlier production generated-view writes are not assigned an unproven
cause. This milestone instead guards every future launch against their relevant
failure modes: resolved path overlap, symlink aliasing, broad parent paths,
inherited HOME/XDG roots, and concurrent production or installed-candidate
processes. The staged verifier reported all disposable paths exactly and zero
conflicting ReasonNotes processes before the noninteractive check-launch.

The noninteractive staged `--check-launch` completed with status 0 using only:

- HOME/XDG roots under `environment/`;
- repository, inbox, and received roots under `test-data/`.

Before and after this milestone, production data (482 files) had manifest hash
`b2cae708e55222eae6d90e37387cbdb07f8ac1c6569fa1c21d01f0b17ba761a1`,
and installed-candidate data (177 files) had manifest hash
`cee5374cf8f469b1ffb0fd889332919434a21ebaaa811964d4b596daf49878d5`.
The production launcher remained
`05406228cadb43bcb6ad37be63d057d645c90e286a5ba8632c64d28c10e66eca`.

For a separately authorized live review, run the verifier first with the same
environment and paths. Only if it exits 0, use this command:

```sh
env \
  HOME=/home/reason/Temporary/ReasonNotes-Dolphin-Native-Candidate/environment/home \
  XDG_CONFIG_HOME=/home/reason/Temporary/ReasonNotes-Dolphin-Native-Candidate/environment/config \
  XDG_DATA_HOME=/home/reason/Temporary/ReasonNotes-Dolphin-Native-Candidate/environment/data \
  XDG_CACHE_HOME=/home/reason/Temporary/ReasonNotes-Dolphin-Native-Candidate/environment/cache \
  XDG_STATE_HOME=/home/reason/Temporary/ReasonNotes-Dolphin-Native-Candidate/environment/state \
  QT_QPA_PLATFORM=wayland QT_QPA_PLATFORMTHEME=qt6ct \
  /home/reason/Temporary/ReasonNotes-Dolphin-Native-Candidate/bin/reasonnotes-dolphin-native \
  --root /home/reason/Temporary/ReasonNotes-Dolphin-Native-Candidate/test-data/repository \
  --inbox /home/reason/Temporary/ReasonNotes-Dolphin-Native-Candidate/test-data/inbox \
  --received-dir /home/reason/Temporary/ReasonNotes-Dolphin-Native-Candidate/test-data/received \
  --no-auto-receive
```

No live launch was performed in this milestone.

## Remaining acceptance and tradeoff

Native Kvantum owns more of the surface, so the former application-controlled
translucent depth is intentionally reduced in favor of Dolphin integration.
Only a controlled real-Wayland side-by-side can determine whether this tradeoff
is visually acceptable and whether the large compositor-visible patches are
materially reduced. Android synchronization and durable receipt acceptance
remain unfinished and were not touched.
