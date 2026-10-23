# JSON v1 Fedora candidate preparation — 2026-10-23

## Scope and provenance

This candidate was prepared from `forge/reasonnotes-completion` at source
checkpoint `88def77e2bfe3c6b2b92897b5d134395a761ffd3`. No desktop UI or protocol
source was changed. The installed production application, launcher,
configuration, notes, immutable history, synchronization state, KDE Connect
configuration, and global theme settings were not modified.

## Focused offline compatibility evidence

Command:

```sh
PYTHONPATH=src /usr/bin/python3 -m unittest \
  tests.test_transport_bundle tests.test_bundle_transport -v
```

Result: 20 tests passed. This includes the literal Unicode canonical JSON
fixture whose filename, payload bytes, revision ID, and receipt ID match the
modern Android `TransportBundleTest`; complete pre-mutation validation;
revision plus receipt import; duplicate handling; and durable confirmation
semantics. The legacy ZIP tests remain in the focused module as compatibility
coverage, but this candidate's canonical JSON v1 implementation is the
Android-compatible transport path.

## Prepared artifact

Build command:

```sh
/usr/bin/python3 scripts/install-candidate.py \
  --install-root /home/reason/Temporary/ReasonNotes-JSON-v1-Candidates/desktop/install \
  --launcher /home/reason/Temporary/ReasonNotes-JSON-v1-Candidates/desktop/bin/reasonnotes-json-v1-candidate \
  --desktop /home/reason/Temporary/ReasonNotes-JSON-v1-Candidates/desktop/share/applications/org.reasonnotes.ReasonNotesKvantum-json-v1.desktop \
  --version 88def77e2bfe3c6b2b92897b5d134395a761ffd3
```

The native Wayland helper compiled successfully. The immutable release is:

`/home/reason/Temporary/ReasonNotes-JSON-v1-Candidates/desktop/install/releases/88def77e2bfe3c6b2b92897b5d134395a761ffd3`

Portable archive:

`/home/reason/Temporary/ReasonNotes-JSON-v1-Candidates/desktop/ReasonNotes-Fedora-JSON-v1-88def77.tar.gz`

SHA-256: `41961dbb0945d2a0294374f92386650d3ec7342e6397db8aa3c2c4082953194e`.

## Future isolated launch procedure — not executed

The exact command is also preserved at
`/home/reason/Temporary/ReasonNotes-JSON-v1-Candidates/desktop/LAUNCH_PROCEDURE.txt`.

```sh
env \
  HOME=/home/reason/Temporary/ReasonNotes-JSON-v1-Candidates/desktop/runtime/home \
  XDG_CONFIG_HOME=/home/reason/Temporary/ReasonNotes-JSON-v1-Candidates/desktop/runtime/config \
  XDG_DATA_HOME=/home/reason/Temporary/ReasonNotes-JSON-v1-Candidates/desktop/runtime/data \
  XDG_CACHE_HOME=/home/reason/Temporary/ReasonNotes-JSON-v1-Candidates/desktop/runtime/cache \
  /home/reason/Temporary/ReasonNotes-JSON-v1-Candidates/desktop/bin/reasonnotes-json-v1-candidate \
  --root /home/reason/Temporary/ReasonNotes-JSON-v1-Candidates/desktop/runtime/notes/repository \
  --inbox /home/reason/Temporary/ReasonNotes-JSON-v1-Candidates/desktop/runtime/exchange/inbox \
  --received-dir /home/reason/Temporary/ReasonNotes-JSON-v1-Candidates/desktop/runtime/exchange/received \
  --device-id 52548cf9710c43cab2fa73ed4671aea9
```

All named HOME/XDG/note/exchange directories already exist under the
candidate-only persistent root. The Android KDE Connect device ID must be
confirmed at the separately authorized physical-test gate because it is a
dated identity. The candidate was not launched during this preparation.

## Remaining acceptance

Physical Fedora-to-Android and Android-to-Fedora transfer, durable import,
receipt confirmation, visible progress/failure behavior, and final production
cutover remain unverified and require separate owner authorization.
