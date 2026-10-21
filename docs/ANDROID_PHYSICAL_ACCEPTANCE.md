# Physical Android acceptance

ReasonNotesKvantum's Linux/Android protocol has automated compatibility
coverage, but those tests cannot prove Android storage access, KDE Connect
delivery, intent routing, or convergence on the physical phone. This document
defines the remaining owner-authorized test without using production notes.

## Prepare an isolated fixture

From the exact candidate source checkout:

```sh
python3 scripts/prepare-android-acceptance.py \
  /tmp/reasonnotes-android-acceptance-YYYYMMDD
```

The target must be new or empty. The utility refuses any path within
`~/.local/share/ReasonNotes`, creates no KDE Connect process, and records
`"transport_activity": false` in its manifest. It creates three fixed test
notes:

- `unicode-round-trip` verifies Polish text, punctuation, and UTF-8;
- `conflict` is edited independently on Linux and Android while disconnected;
- `deletion` is delivered and confirmed before testing peer purge.

The generated `android-acceptance-manifest.json` is the authoritative list of
paths, note IDs, and original body hashes. Keep it with the test evidence.

## Owner-authorized physical sequence

This sequence deliberately requires a separate approval because it sends
test files to the paired phone and changes the Android app's private test
state. Before starting, record the exact candidate Git SHA, Android app
version, phone device ID, and KDE Connect reachability.

1. Launch the accepted candidate with `--root`, `--inbox`, and
   `--received-dir` set to the three manifest paths, add the known test-phone
   `--device-id`, and use `--kitty-window-material` only if that renderer has
   received owner visual approval. Do not use production data paths.
2. Select only `unicode-round-trip` and synchronize. On Android, import it,
   verify every character, edit it, and send it back. Stage only the returned
   ReasonNotes envelope in the fixture's `inbox`, press F5, and verify the edit
   and receipt state on Linux without restarting.
3. Synchronize `conflict`, then take both devices offline from each other.
   Edit the same note differently on Linux and Android. Restore connectivity,
   return the Android revision, press F5, and verify both full previews appear.
   Exercise Skip once, then make an explicit keep choice. Confirm stale choices
   cannot overwrite a subsequently imported head and that recoverable history
   remains present.
4. Synchronize `deletion` and wait for Android import plus the returned durable
   confirmation. Delete it on Linux and verify immediate local removal. Reopen
   both apps after reconnection and verify peer purge prevents an old transfer
   from resurrecting the note.
5. Restart the Linux candidate. Verify all resolved content, receipt state,
   pending state, purge fence, and language preference survive. Repeat the main
   navigation check in Polish and English.

KDE Connect may place returned files in its configured download directory.
For this acceptance run, copy only the identified test envelope into the
fixture `inbox`; do not repoint global KDE Connect settings and do not scan a
production ReasonNotes repository.

## Evidence and pass criteria

Record the manifest, Linux Git SHA, Android version, transferred filenames,
timestamps, screenshots of the receipt/conflict states, and the final contents
of the fixture repository. A transfer request alone is not a pass. Each phase
must distinguish:

1. transfer requested by Linux;
2. KDE Connect reported delivery completion;
3. Android durably imported the revision;
4. Linux received the application-level receipt and marked it confirmed.

The test passes only if Unicode, selective delivery, bounded retry state,
conflict resolution, deletion propagation, and restart persistence all work on
the physical phone without touching production notes.

## Cleanup and rollback

Close the test candidate, remove only the three identified fixture notes from
the Android test app after evidence is saved, and retain or delete the
`/tmp/reasonnotes-android-acceptance-*` directory as an ordinary disposable
fixture. No production rollback is necessary because this procedure does not
change the installed production application, launcher, or repository.
