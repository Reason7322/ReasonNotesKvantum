# Cutover and rollback

No production cutover has been performed. The current installed ReasonNotes,
its launcher, desktop entry, release tree, settings, and note repository remain
the authoritative production system until the owner gives explicit approval.

## Candidate rollback

Candidate releases are versioned and retained. To select an earlier candidate:

```sh
/usr/bin/python3 scripts/install-candidate.py --activate <installed-version>
```

This changes only the candidate `current` symlink. It does not touch production.

## Future production cutover (approval required)

After engineering validation and owner visual acceptance, prepare a separate
cutover checkpoint. Before changing any launcher:

1. Record the exact accepted Git SHA and installed candidate release.
2. Back up the existing production launcher and desktop entry byte-for-byte.
3. Back up production settings and note data without migrating or cleaning it.
4. Verify format compatibility using a copy of the production repository.
5. Switch only the intended production launcher after explicit owner approval.
6. Retain the former production release and backups until the owner accepts the
   migrated application in normal use.

Rollback is the inverse launcher/desktop-entry restoration from those exact
backups. Restore the old application while leaving user data intact unless a
separately reviewed data rollback is required. Never delete newer history as
part of an application rollback.
