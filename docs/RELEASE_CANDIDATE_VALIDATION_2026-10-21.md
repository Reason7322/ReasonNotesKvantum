# Release candidate validation — 2026-10-21

## Scope

This pass validated the integrated Qwen UI checkpoint plus the Forge offline
Android-acceptance preparation work as an isolated, versioned package. It did
not install a user candidate, touch production data, contact Android, or make
the Kitty-equivalent renderer the default.

- Forge source commit packaged: `646abce5870b24310239e7feb13141ee2d08b9c2`
- Source tree: `dec96e0b2c5ea936c661fa6e7b6b2624afb7fad5`
- Qwen UI checkpoint retained in its ancestry:
  `9374dce9d75b3c87002b3debe50a6eaf071bae62`
- Temporary validation root:
  `/tmp/reasonnotes-release-validation.eMLfrk`
- Synthetic-note fixture:
  `/tmp/reasonnotes-android-acceptance.G5zpif`

## Built and packaged

`scripts/install-candidate.py` created an immutable release under the temporary
home and compiled the native Wayland helper. Recursive comparison confirmed
that the packaged `src/` and `linux-app/` trees match the source checkout,
excluding only the newly compiled helper.

Artifact SHA-256 values:

| Artifact | SHA-256 |
| --- | --- |
| `libreasonnotes_wayland_blur.so` | `e7bb3e6269419810f884c8aa1294a9eba5ddb39e60d071e295cb54538a3e02c4` |
| temporary candidate launcher | `7e88dcbca49fbc5846f0ad8e66d5255b5df977bbe274db668bd4e19cb186d04c` |
| temporary desktop entry | `84947f7cb1975405cab317530faf640e5765416dda1194a60f34fae5ea0aea19` |

The packaged launcher passed `--check-launch` with an isolated home,
configuration directory, and XDG data directory. It created only
`ReasonNotesKvantum-candidate` data. No bundled Kvantum configuration or theme
was found; the only packaged SVGs are ReasonNotes icons.

Candidate rollback was exercised between version
`646abce5870b24310239e7feb13141ee2d08b9c2` and a second temporary
`rollback-probe` release. Both immutable release directories remained present,
and the candidate-only `current` link returned to the SHA-named release.

## Existing-format compatibility on a copy

The live production data tree was copied read-only into the temporary
validation root. Before opening it, the relative-path/content manifest matched
the source tree exactly at
`d47802fa402edd0905cb28508ce806442e4e11f4345eeeecaa334807c5544890`.
The packaged launcher then completed `--check-launch` against the copied
repository. It reopened 187 immutable revisions as 6 live notes with 16 purge
fences. The copied immutable-history manifest remained
`4351cd3f527f8a8285f8db84e05a8e7f625a274e3bf01da63bd3ed171f35abc9`
before and after. No titles or note bodies were emitted into evidence.

This proves current on-disk format compatibility and non-destructive history
reconciliation on a copy. It does not authorize migration or prove the future
production launcher switch, which remains a separately controlled operation.

## Actual Hyprland/Wayland runtime

Workspace 10 on `DP-2` was empty before launch. The exact packaged modules ran
with copied qt6ct/Kvantum configuration, explicit disposable note paths,
`--no-auto-receive`, `--kitty-window-material`, and bounded runtime probes.
The active Workspace 1 was restored after the captures and Workspace 10 was
empty afterward.

Each launch reported:

```text
RUNTIME_STYLE=qt6ct-style
RUNTIME_PLATFORM=wayland
RUNTIME_BLUR_ACTIVE=1
RUNTIME_BLUR_ERROR=
RUNTIME_WINDOW_MATERIAL=kitty-equivalent
RUNTIME_PURGE_RELAY=disabled-for-probe
```

A separate native Wayland style probe against the same package reported:

```text
RUNTIME_STYLE_CHAIN=qt6ct-style -> kvantum
RUNTIME_PLATFORM=wayland
```

Hyprland reported class `org.reasonnotes.ReasonNotesKvantum`, `xwayland=false`,
position `[0,46]`, and size `[2048,1106]` logical pixels. All three application
probes exited with status 0; no blur-helper or teardown error was reported.

## Visual evidence and observation

All captures are full-resolution 2560×1440 composited screenshots:

- [empty editor](evidence/release-candidate-2026-10-21/editor.png), SHA-256
  `6974cd09e8a90cfaa315953ca6205b67f040328d3f9b8ce24ee532422a789b59`
- [selected Unicode note](evidence/release-candidate-2026-10-21/selected-note.png),
  SHA-256
  `18029e550dbc3ead020e3c1405514dc1ee6a89b053b1027ab3c988e61039b281`
- [Settings](evidence/release-candidate-2026-10-21/settings.png), SHA-256
  `c6729669191d98046f1e7f6bb9313cd800e34a14d925f191cf04964d7d9e4de2`
- [splitter hover](evidence/release-candidate-2026-10-21/splitter-hover.png),
  SHA-256
  `d0072084d3f887005d8739e53af98499f49204eba8ea11ebdb32306a8ac8e5bb`

Full-resolution inspection found:

- the approved ReasonNotes hierarchy remains intact;
- the selected note preserves Polish Unicode and the solid `#2C3539` writing
  sheet, while the surrounding window retains Kitty-equivalent glass;
- the stronger card rim cleanly separates the opaque editor from the glass;
- Settings remains integrated in the permanent sidebar with no back button;
- the splitter is visually clear at rest and shows the three-dot grip on hover
  while retaining the native resize cursor;
- no horizontal quantization bands or pane-sized rectangular paint artifacts
  were visible inside the opaque writing surface.

The composited wallpaper still contributes broad variation to the translucent
surrounding window, as established by the earlier controlled diagnostics. This
capture is evidence for the owner's judgment, not subjective visual approval.

## Production isolation

The production launcher SHA-256 remained
`05406228cadb43bcb6ad37be63d057d645c90e286a5ba8632c64d28c10e66eca`.
A content-hash manifest over all 404 production data files remained
`f1e05071589cecb60ff9d35e76bb1a826d9f65d63482b2dfff1c57e0cf78a58e`
before and after packaging/runtime validation. No installed candidate,
production release, desktop entry, live Qt/Hyprland configuration, KDE Connect
state, or Android state was changed.

## Remaining acceptance gates

The product is still incomplete. Reason must visually accept the captured UI
and explicitly decide whether the Kitty-equivalent renderer becomes the
product default. The prepared fixture must then pass physical Android
interoperability, followed by separately authorized production migration,
cutover, and rollback verification.
