# Fedora to Android physical synchronization preparation — 2026-10-23

## Result and boundary

The approved Widgets source is prepared for one separately authorized JSON v1
round trip. Nothing was launched, transmitted, installed, or changed on the
phone during this milestone. Production notes, immutable history, delivery
ledgers, settings, and KDE Connect configuration were not reset or migrated.

## Protocol and peer evidence

Current source descends from the proven desktop JSON v1 checkpoint
`88def77e2bfe3c6b2b92897b5d134395a761ffd3`. There are no changes after that
checkpoint under `src/reasonnotes_sync/` or `linux-app/reasonnotes_widgets.py`;
the Widgets launcher still routes selected sync through
`sync_linux_confirmed()`. Existing focused compatibility evidence passed 20/20
and covers canonical Unicode JSON v1 carriers, Android fixture byte parity,
revision plus receipt import, duplicate handling, and durable confirmation.

The intended installed Android peer artifact remains:

- APK: `/home/reason/Temporary/ReasonNotes-JSON-v1-Candidates/android/ReasonNotes-Android-JSON-v1-with-launcher.apk`
- SHA-256: `feb2312efa2195ed739b7d434b809bc169106bfaae7287d8039a7878f832b5fa`
- Package: `org.reasonnotes.probe`, version `0.1` (`versionCode 1`)
- Signing certificate SHA-256:
  `d30a8083a422ed86f1b177b3d5c56d1d51db1a926f8c3d15807609c860eaa147`

The 08:13 post-install Android screenshots remain in the prior physical-test
evidence directory. Current KDE Connect read-only discovery reports peer
`52548cf9710c43cab2fa73ed4671aea9`, `POCO X6 5G`, as paired and available.
ADB currently reports no attached device, so the installed APK cannot be
cryptographically re-read from the phone in this preparation milestone. Do
not reinstall it; live package identity remains a pre-transfer confirmation
item if ADB becomes available.

## Earlier generated-file writes

Observed filesystem times establish this sequence:

- 08:17–08:19: the explicitly isolated physical-test runtime wrote only below
  `/home/reason/Temporary/ReasonNotes-JSON-v1-Physical-Test/desktop-runtime/`;
- 08:28 and 08:44: production gained purge markers and regenerated index/note
  views;
- 08:37 and 09:24: the installed-candidate repository changed independently.

These times disprove a claim that the explicitly isolated runtime itself was
observed writing production at startup, but they do not identify the later
processes or exact launch commands. Causation therefore remains unknown. The
current preparation addresses the relevant failure modes with two independent
gates: bootstrap now protects the login account's production tree even when
HOME is substituted, and `verify-candidate-isolation.py` rejects resolved
aliases, broad parents, inherited HOME/XDG roots, and conflicting installed or
production processes.

## Persistent disposable fixture

Root:
`/home/reason/Temporary/ReasonNotes-JSON-v1-Roundtrip-2026-10-23-Final/`

Fixture manifest:
`fixture/android-acceptance-manifest.json`

Manifest SHA-256:
`51dcf6f9c77f7580ad14ce14b2ac90378f870a94ca8d8b02ac82e46d66bc2ba8`

The manifest records `transport_activity: false`. The first physical test must
select only:

- role: `first-roundtrip`
- note ID: `12da1570-821e-5365-b9d1-abc49e22e590`
- initial body SHA-256:
  `79a3d9463b642f67d23745471ad25cb2b27cf342a55e227886eec3411abce1c1`
- initial revision ID:
  `cc6ba71f4061dc5572fee5995fae197bf535d9110efc21e8eb8edb2c85156a90`

Preflight confirms one pending delivery entry with zero attempts and zero JSON
carriers. No transfer has been requested.

Focused offline verification passed 66 tests across JSON v1 carrier parity,
bundle import, durable receipts, sync orchestration, fixture preparation,
Widgets bootstrap, and candidate isolation/install safeguards. Tests used
`TMPDIR=/home/reason/Temporary/ReasonNotes-Test-Tmp`; no deliberate test
artifacts were placed under `/tmp`.

This final fixture contains no conflict or deletion notes. Historical fixture
IDs were deliberately not reused because they already appear in earlier purge
evidence and could produce a false no-import result.

## Mandatory pre-launch gate

From the exact reported Forge checkpoint, first verify HEAD, current peer, and
isolation. Do not continue if another ReasonNotes process is running or any
resolved path differs:

```zsh
cd /home/reason/Codex-Projects/ReasonNotesKvantum/.worktrees/forge-reasonnotes-completion
git rev-parse HEAD

roundtrip=/home/reason/Temporary/ReasonNotes-JSON-v1-Roundtrip-2026-10-23-Final

env \
  HOME="$roundtrip/runtime/home" \
  XDG_CONFIG_HOME="$roundtrip/runtime/config" \
  XDG_DATA_HOME="$roundtrip/runtime/data" \
  XDG_CACHE_HOME="$roundtrip/runtime/cache" \
  XDG_STATE_HOME="$roundtrip/runtime/state" \
  PYTHONPATH=src \
  /usr/bin/python3 scripts/verify-candidate-isolation.py \
  --repository "$roundtrip/fixture/repository" \
  --inbox "$roundtrip/fixture/inbox" \
  --received-dir "$roundtrip/fixture/received"

XDG_RUNTIME_DIR=/run/user/1000 \
DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus \
kdeconnect-cli --list-available --id-name-only
```

Expected peer: `52548cf9710c43cab2fa73ed4671aea9 POCO X6 5G`.

## Separately authorized launch command

Do not run this during preparation. After Reason authorizes the physical test:

```zsh
roundtrip=/home/reason/Temporary/ReasonNotes-JSON-v1-Roundtrip-2026-10-23-Final
project=/home/reason/Codex-Projects/ReasonNotesKvantum/.worktrees/forge-reasonnotes-completion

cd "$project"
env \
  HOME="$roundtrip/runtime/home" \
  XDG_CONFIG_HOME="$roundtrip/runtime/config" \
  XDG_DATA_HOME="$roundtrip/runtime/data" \
  XDG_CACHE_HOME="$roundtrip/runtime/cache" \
  XDG_STATE_HOME="$roundtrip/runtime/state" \
  XDG_DATA_DIRS="/home/reason/.local/share:/usr/local/share:/usr/share" \
  QT_QPA_PLATFORM=wayland \
  QT_QPA_PLATFORMTHEME=qt6ct \
  PYTHONPATH="$project/src" \
  /usr/bin/python3 "$project/linux-app/reasonnotes_widgets.py" \
  --root "$roundtrip/fixture/repository" \
  --inbox "$roundtrip/fixture/inbox" \
  --received-dir "$roundtrip/fixture/received" \
  --device-id 52548cf9710c43cab2fa73ed4671aea9 \
  --target-device android \
  --no-auto-receive
```

## First physical round trip

1. Confirm the window shows only the one disposable fixture note and no
   personal notes. Stop immediately if this is false.
2. Open Sync, choose selected-notes mode, clear selection, and select only note
   `12da1570-821e-5365-b9d1-abc49e22e590` (`first-roundtrip`).
3. Start Sync once. Record separately: request time, generated JSON carrier
   filename/hash, and KDE Connect request result. Request acceptance is not
   synchronization success.
4. On Android, verify the Unicode note imports durably and survives leaving and
   reopening the note. Record the imported revision ID. Confirm Android emits
   its durable receipt.
5. Edit that same disposable note on Android with an unmistakable line, save,
   and send the Android JSON carrier back through KDE Connect.
6. Place only that identified returned carrier in the fixture `received/` or
   `inbox/`, then press F5 once. Record Fedora import, revision ID, body, queued
   receipt, and receipt-return request separately.
7. On Android, import Fedora's returned durable receipt. Return Android's
   receipt for the edited revision to Fedora, press F5, and require the Fedora
   delivery ledger to reach confirmed state. Restart checks, conflicts, and
   deletion propagation remain later acceptance phases.

Stop on any personal-note visibility, production-path change, false success,
missing durable receipt, unexplained carrier, or process/isolation mismatch.
