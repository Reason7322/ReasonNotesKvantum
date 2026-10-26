# Local-only deletion design

## Intent

Deletion is a permanent local purge, not a synchronization event. Pressing
**Delete** removes the selected note and all ReasonNotes-managed material tied
to that note from the device where Delete was pressed. The peer is unaffected.
A later explicit push from a device that still has the note may recreate it on
the device where it was deleted.

These semantics are symmetrical on Fedora and Android.

## Local deletion

For every selected note, Delete immediately removes:

- current title and body;
- drafts and autosave state;
- conflict candidates;
- pending upserts and note-specific delivery state;
- queued acknowledgments tied to that note;
- current-store history and legacy application-managed history tied to that
  note;
- deletion records, tombstones, purge fences, and other note-specific metadata.

Delete creates no state envelope, deletion carrier, tombstone, acknowledgment,
retry entry, or peer-facing status. It does not contact KDE Connect. Restarting
the deleting application leaves the note absent and leaves no note-specific
application record behind.

## Explicit synchronization

Sync is push-based. The device initiating Sync sends the current live state of
the selected notes, or all current live notes in All notes mode, even when a
state has no unsent edit. Existing pending edits remain coalesced to their
latest complete state.

Consequences:

- If Android deleted Note A and Fedora still has A, Fedora must explicitly Sync
  A (or Sync all) to restore it on Android.
- Pressing Sync on Android cannot pull A from Fedora.
- A missing local note accepts the newly transferred live state as an ordinary
  import and may acknowledge that live-state import through the existing
  durable-confirmation mechanism.
- If both devices deleted A, neither sends it and it remains absent on both.
- Deletion itself never produces or expects an acknowledgment.

## Historical exchange artifacts

The generic processed-occurrence index remains because it contains no note ID,
title, body, history, or deletion fact. It records only that a particular file
occurrence was already scanned. Keeping it prevents historical carrier files
already present in an exchange directory from recreating a locally deleted
note.

A newly delivered carrier is a new occurrence. If it contains the peer's
current live Note A, normal receive scanning may restore A without another Sync
press on the receiving device. The required explicit action is the Sync press
on the device that still has A. Existing historical files are not current peer
state and must not be replayed merely because local deletion removed A.

## Conflict behavior

Local Delete removes any local conflict without notifying the peer. If the peer
later pushes its surviving live version, the missing device imports that single
version without conflict. Ordinary independent live edits still use the
existing complete two-version conflict chooser and are outside this deletion
change.

## Migration and compatibility

Existing v2 deletion fences and pending deletion envelopes are obsolete local
state. Migration removes them and associated note-specific content rather than
transmitting them. Incoming legacy or v2 deletion envelopes are ignored as
historical unsupported operations and do not delete local notes or generate
acknowledgments.

Both platforms continue to parse existing live-state and acknowledgment
records. No new carrier format, background service, cloud dependency, or
pairing mechanism is introduced.

## Verification

Isolated cross-platform tests must demonstrate:

1. Local Delete leaves no note-specific application files or serialized note
   content and emits no outgoing work.
2. Restart preserves local absence.
3. The peer remains unchanged.
4. Explicit Sync from the surviving peer restores the note.
5. Explicit Sync when both copies were locally deleted sends nothing and does
   not restore historical artifacts.
6. Previously processed historical carriers remain ignored.
7. One explicit Sync on the surviving device delivers a new live carrier that
   restores the receiving device without a second Sync press.
8. Existing live edit, acknowledgment, and conflict behavior remains intact.

Physical verification and deployment remain separate owner-authorized gates.
