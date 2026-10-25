import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

from reasonnotes_app.service import (
    NoteNotFoundError,
    NoteService,
    StaleConflictChoice,
)
from reasonnotes_sync.conflicts import resolve_conflict
from reasonnotes_sync.current_store import CurrentNoteStore
from reasonnotes_sync.envelope import Revision
from reasonnotes_sync.repository import ConflictRequired, Repository
from reasonnotes_sync.state_envelope import StateEnvelope


NOTE_A = UUID("11111111-1111-4111-8111-111111111111")
NOTE_B = UUID("22222222-2222-4222-8222-222222222222")
NOTE_C = UUID("33333333-3333-4333-8333-333333333333")
START = datetime(2026, 10, 14, 8, 0, tzinfo=timezone.utc)


class AdvancingClock:
    def __init__(self, start: datetime = START):
        self.current = start

    def __call__(self) -> datetime:
        result = self.current
        self.current += timedelta(seconds=1)
        return result


class InterleavingClock(AdvancingClock):
    def __init__(self, start: datetime = START):
        super().__init__(start)
        self.callback = None

    def arm(self, callback) -> None:
        self.callback = callback

    def __call__(self) -> datetime:
        if self.callback is not None:
            callback = self.callback
            self.callback = None
            callback()
        return super().__call__()


class NoteServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.repository = Repository.open(self.root)
        self.ids = iter((NOTE_A, NOTE_B, NOTE_C))
        self.service = NoteService(
            self.repository,
            origin_device="linux",
            clock=AdvancingClock(),
            note_id_factory=lambda: next(self.ids),
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_create_edit_delete_uses_repository_history(self) -> None:
        note_id = self.service.create_note("\n##   First note\nInitial body")

        self.assertEqual(NOTE_A, note_id)
        self.assertEqual("\n##   First note\nInitial body", self.service.open_note(note_id))
        self.assertEqual("First note", self.service.list_notes()[0].title)

        edited = self.service.save_note(note_id, "# Renamed\nEdited body")
        self.assertEqual("# Renamed\nEdited body", self.service.open_note(note_id))
        self.assertEqual(1, len(edited.parents))

        self.service.delete_note(note_id)
        self.assertFalse(self.repository.is_purged(note_id))
        self.assertEqual([], self.service.list_notes())
        with self.assertRaises(NoteNotFoundError):
            self.service.open_note(note_id)
        self.assertEqual(3, len(self.repository.revisions()))
        deletion = self.repository.graph().heads(note_id)[0]
        self.assertTrue(deletion.deleted)
        self.assertEqual((edited.revision_id,), deletion.parents)

    def test_search_is_unicode_aware_case_insensitive_and_excludes_deleted(self) -> None:
        german = self.service.create_note("# Straße\nA useful note")
        accented = self.service.create_note("# Other\nCafe\u0301 details")
        deleted = self.service.create_note("# STRASSE deleted")
        self.service.delete_note(deleted)

        self.assertEqual([german], [item.note_id for item in self.service.list_notes("STRASSE")])
        self.assertEqual([accented], [item.note_id for item in self.service.list_notes("CAFÉ")])
        self.assertNotIn(deleted, [item.note_id for item in self.service.list_notes()])

    def test_unchanged_autosaves_do_not_create_revisions(self) -> None:
        note_id = self.service.create_note("Same body")
        original = self.repository.graph().heads(note_id)[0]

        first = self.service.save_note(note_id, "Same body")
        second = self.service.save_note(note_id, "Same body")

        self.assertEqual(original.revision_id, first.revision_id)
        self.assertEqual(original.revision_id, second.revision_id)
        self.assertEqual(1, len(self.repository.revisions()))

    def test_save_rejects_remote_edit_that_arrived_after_note_was_displayed(self) -> None:
        note_id = self.service.create_note("Displayed body")
        displayed = self.repository.graph().heads(note_id)[0]
        self.assertEqual("Displayed body", self.service.open_note(note_id))
        remote = Revision.create(
            note_id=note_id,
            parents=(displayed.revision_id,),
            origin_device="android",
            modified_utc=START + timedelta(seconds=30),
            deleted=False,
            body="Remote edit",
        )
        self.repository.import_bytes(remote.serialize(), "remote-edit.md")

        with self.assertRaises(ConflictRequired):
            self.service.save_note(note_id, "Stale local draft")

        self.assertEqual((remote.revision_id,), self.repository.graph().status(note_id).head_ids)
        self.assertEqual("Remote edit", self.service.open_note(note_id))
        self.assertEqual(2, len(self.repository.revisions()))

    def test_open_binds_body_and_edit_base_to_same_history_revision(self) -> None:
        note_id = self.service.create_note("# Old title\nOld body")
        old = self.repository.graph().heads(note_id)[0]
        remote = Revision.create(
            note_id=note_id,
            parents=(old.revision_id,),
            origin_device="android",
            modified_utc=START + timedelta(seconds=30),
            deleted=False,
            body="# Remote title\nRemote body",
        )
        self.repository._write_history(remote)

        self.assertEqual("# Remote title\nRemote body", self.service.open_note(note_id))
        self.assertEqual("Remote title", self.service.list_notes()[0].title)
        saved = self.service.save_note(
            note_id,
            "# Remote title\nRemote body edited locally",
        )

        self.assertEqual((remote.revision_id,), saved.parents)
        self.assertEqual(3, len(self.repository.revisions()))

    def test_delete_and_independent_remote_edit_become_explicit_conflict(self) -> None:
        note_id = self.service.create_note("Displayed body")
        displayed = self.repository.graph().heads(note_id)[0]
        remote_edit = Revision.create(
            note_id=note_id,
            parents=(displayed.revision_id,),
            origin_device="android",
            modified_utc=START + timedelta(seconds=30),
            deleted=False,
            body="Remote edit",
        )
        self.service.delete_note(note_id)
        outcome = self.repository.import_bytes(remote_edit.serialize(), "remote.md")
        self.assertEqual("imported", outcome.kind)
        self.assertEqual(3, len(self.repository.revisions()))
        self.assertTrue(self.repository.graph().status(note_id).conflicted)
        candidates = self.service.conflict(note_id)
        self.assertEqual({True, False}, {candidate.deleted for candidate in candidates})

    def test_empty_live_note_is_untitled_not_conflicted(self) -> None:
        note_id = self.service.create_note("")

        summary = self.service.list_notes()[0]

        self.assertEqual(note_id, summary.note_id)
        self.assertEqual("Untitled", summary.title)
        self.assertFalse(summary.conflicted)

    def test_conflict_blocks_edit_and_can_be_explicitly_resolved(self) -> None:
        note_id = self.service.create_note("Base")
        base = self.repository.graph().heads(note_id)[0]
        linux = self.service.save_note(note_id, "Linux edit")
        android = Revision.create(
            note_id=note_id,
            parents=(base.revision_id,),
            origin_device="android",
            modified_utc=START + timedelta(seconds=30),
            deleted=False,
            body="Android edit",
        )
        self.repository.import_bytes(android.serialize(), "android-edit.md")

        with self.assertRaises(ConflictRequired):
            self.service.save_note(note_id, "Unsafe overwrite")

        candidates = self.service.conflict(note_id)
        self.assertEqual(
            {linux.revision_id, android.revision_id},
            {candidate.revision_id for candidate in candidates},
        )

        resolution = self.service.resolve(
            note_id,
            "keep-android",
            revision_id=android.revision_id,
        )

        self.assertIsNotNone(resolution)
        self.assertEqual("Android edit", self.service.open_note(note_id))
        self.assertEqual(
            {linux.revision_id, android.revision_id},
            set(resolution.parents),
        )
        self.assertFalse(self.repository.graph().status(note_id).conflicted)

    def test_resolution_rejects_choice_when_conflict_changed_after_inspection(self) -> None:
        note_id = self.service.create_note("Base")
        base = self.repository.graph().heads(note_id)[0]
        self.service.save_note(note_id, "Linux edit")
        android = Revision.create(
            note_id=note_id,
            parents=(base.revision_id,),
            origin_device="android",
            modified_utc=START + timedelta(seconds=30),
            deleted=False,
            body="Android edit",
        )
        self.repository.import_bytes(android.serialize(), "android-edit.md")
        self.service.conflict(note_id)

        later = Revision.create(
            note_id=note_id,
            parents=(base.revision_id,),
            origin_device="android-secondary",
            modified_utc=START + timedelta(seconds=31),
            deleted=False,
            body="Later edit",
        )
        self.repository.import_bytes(later.serialize(), "later-edit.md")
        revision_count = len(self.repository.revisions())

        with self.assertRaises(StaleConflictChoice):
            self.service.resolve(
                note_id,
                "keep-android",
                revision_id=android.revision_id,
            )
        self.assertEqual(revision_count, len(self.repository.revisions()))
        self.assertTrue(self.repository.graph().status(note_id).conflicted)

    def test_resolution_requires_current_conflict_inspection(self) -> None:
        note_id = self.service.create_note("Base")
        base = self.repository.graph().heads(note_id)[0]
        self.service.save_note(note_id, "Linux edit")
        android = Revision.create(
            note_id=note_id,
            parents=(base.revision_id,),
            origin_device="android",
            modified_utc=START + timedelta(seconds=30),
            deleted=False,
            body="Android edit",
        )
        self.repository.import_bytes(android.serialize(), "android-edit.md")

        with self.assertRaises(StaleConflictChoice):
            self.service.resolve(
                note_id,
                "keep-android",
                revision_id=android.revision_id,
            )

    def test_resolution_rejects_conflict_resolved_elsewhere_after_inspection(self) -> None:
        note_id = self.service.create_note("Base")
        base = self.repository.graph().heads(note_id)[0]
        linux = self.service.save_note(note_id, "Linux edit")
        android = Revision.create(
            note_id=note_id,
            parents=(base.revision_id,),
            origin_device="android",
            modified_utc=START + timedelta(seconds=30),
            deleted=False,
            body="Android edit",
        )
        self.repository.import_bytes(android.serialize(), "android-edit.md")
        self.service.conflict(note_id)
        resolve_conflict(
            self.repository,
            note_id,
            "keep-linux",
            "linux",
            START + timedelta(seconds=31),
            revision_id=linux.revision_id,
        )
        revision_count = len(self.repository.revisions())

        with self.assertRaises(StaleConflictChoice):
            self.service.resolve(
                note_id,
                "keep-android",
                revision_id=android.revision_id,
            )
        self.assertEqual(revision_count, len(self.repository.revisions()))

    def test_restart_recovers_revision_written_only_to_history(self) -> None:
        note_id = self.service.create_note("Before interruption")
        current = self.repository.graph().heads(note_id)[0]
        interrupted = Revision.create(
            note_id=note_id,
            parents=(current.revision_id,),
            origin_device="linux",
            modified_utc=START + timedelta(seconds=60),
            deleted=False,
            body="# Recovered\nAfter interruption",
        )
        history_path = (
            self.repository.history_dir
            / str(note_id)
            / f"{interrupted.revision_id}.md"
        )
        history_path.write_bytes(interrupted.serialize())

        reopened = Repository.open(self.root)
        service = NoteService(reopened, origin_device="linux")

        self.assertEqual("# Recovered\nAfter interruption", service.open_note(note_id))
        summaries = service.list_notes()
        self.assertEqual("Recovered", summaries[0].title)
        self.assertEqual(interrupted.modified_utc, summaries[0].modified_utc)

    def test_conflicted_note_with_a_deleted_head_remains_visible_for_resolution(self) -> None:
        note_id = self.service.create_note("# Keep me")
        base = self.repository.graph().heads(note_id)[0]
        self.service.save_note(note_id, "# Edited")
        deletion = Revision.create(
            note_id=note_id,
            parents=(base.revision_id,),
            origin_device="android",
            modified_utc=START + timedelta(seconds=30),
            deleted=True,
            body="",
        )
        self.repository.import_bytes(deletion.serialize(), "android-delete.md")

        summaries = self.service.list_notes()

        self.assertEqual([note_id], [item.note_id for item in summaries])
        self.assertTrue(summaries[0].conflicted)


class CurrentNoteServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.base = Path(self.tempdir.name)
        self.store = CurrentNoteStore.open(self.base / "reasonnotes-v2", "linux")
        self.ids = iter((NOTE_A, NOTE_B, NOTE_C))
        self.service = NoteService(
            self.store,
            origin_device="linux",
            clock=AdvancingClock(),
            note_id_factory=lambda: next(self.ids),
        )

    def test_listing_reads_current_records_and_ignores_historical_files(self):
        first = self.service.create_note("# First\n\nCurrent body")
        second = self.service.create_note("# Second\n\nAnother body")
        history = self.base / "legacy" / "history"
        history.mkdir(parents=True)
        for index in range(400):
            (history / f"historical-{index}.md").write_text("obsolete", encoding="utf-8")

        summaries = self.service.list_notes()

        self.assertEqual({first, second}, {summary.note_id for summary in summaries})
        self.assertEqual({"First", "Second"}, {summary.title for summary in summaries})
        self.assertEqual([first], [summary.note_id for summary in self.service.list_notes("CURRENT")])

    def test_repeated_and_unchanged_saves_keep_only_latest_pending_state(self):
        note_id = self.service.create_note("# First\n\nOne")
        first = self.store.get(note_id)
        self.service.open_note(note_id)

        second = self.service.save_note(note_id, "# First\n\nTwo")
        unchanged = self.service.save_note(note_id, "# First\n\nTwo")

        self.assertEqual(second, unchanged)
        self.assertNotEqual(first.change_id, second.change_id)
        self.assertEqual((second,), self.store.pending_states())

    def test_conflict_exposes_both_complete_versions_and_erases_loser_after_choice(self):
        note_id = self.service.create_note("# Base\n\noriginal")
        base = self.store.get(note_id)
        self.store.acknowledge(base.change_id)
        self.service.open_note(note_id)
        local = self.service.save_note(note_id, "# Local\n\nlinux complete body")
        remote = StateEnvelope.upsert(
            note_id,
            (base.change_id,),
            "android",
            START + timedelta(seconds=30),
            "Remote",
            "android complete body",
        )
        self.assertEqual("conflict", self.store.apply(remote).kind)

        candidates = self.service.conflict(note_id)

        self.assertEqual(
            {"# Local\n\nlinux complete body", "# Remote\n\nandroid complete body"},
            {candidate.body for candidate in candidates},
        )
        resolved = self.service.resolve(
            note_id, "keep-android", revision_id=remote.change_id
        )
        self.assertEqual("# Remote\n\nandroid complete body", self.service.open_note(note_id))
        self.assertEqual(remote.change_id, resolved.parent_change_ids[1] if resolved.parent_change_ids[1] == remote.change_id else resolved.parent_change_ids[0])
        stored_bytes = b"".join(
            path.read_bytes()
            for path in self.store.root.rglob("*")
            if path.is_file()
        )
        self.assertNotIn(b"linux complete body", stored_bytes)

    def test_delete_permanently_erases_note_content(self):
        note_id = self.service.create_note("# Secret\n\nprivate body")

        self.service.delete_note(note_id)

        self.assertEqual([], self.service.list_notes())
        with self.assertRaises(NoteNotFoundError):
            self.service.open_note(note_id)
        self.assertTrue(self.store.is_deleted(note_id))
        stored_bytes = b"".join(
            path.read_bytes()
            for path in self.store.root.rglob("*")
            if path.is_file()
        )
        self.assertNotIn(b"Secret", stored_bytes)
        self.assertNotIn(b"private body", stored_bytes)


if __name__ == "__main__":
    unittest.main()
