from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from uuid import UUID

from reasonnotes_sync.current_store import CurrentNoteStore
from reasonnotes_sync.state_envelope import StateAckEnvelope, StateEnvelope


NOTE = UUID("11111111-1111-4111-8111-111111111111")
OTHER = UUID("22222222-2222-4222-8222-222222222222")
NOW = datetime(2026, 10, 24, 13, 0, tzinfo=timezone.utc)


class CurrentNoteStoreTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "reasonnotes-v2"

    def open(self):
        return CurrentNoteStore.open(self.root, "linux")

    def test_local_edits_are_durable_and_coalesce_to_one_pending_state(self):
        store = self.open()
        first = store.save_local(NOTE, "One", "body one", NOW)
        second = store.save_local(NOTE, "Two", "body two", NOW + timedelta(seconds=1))

        reopened = self.open()

        self.assertEqual(second, reopened.get(NOTE))
        self.assertEqual((second,), reopened.pending_states())
        self.assertEqual(first.parent_change_ids, second.parent_change_ids)

    def test_repeated_pending_autosaves_remain_one_bounded_descendant(self):
        base = StateEnvelope.upsert(NOTE, (), "android", NOW, "Base", "A")
        store = self.open()
        self.assertEqual("applied", store.apply(base).kind)
        middle = store.save_local(NOTE, "Middle", "B", NOW + timedelta(seconds=1))
        latest = store.save_local(NOTE, "Latest", "C", NOW + timedelta(seconds=2))

        self.assertEqual((base.change_id,), middle.parent_change_ids)
        self.assertEqual((base.change_id,), latest.parent_change_ids)

        peer_root = Path(self.temporary.name) / "peer-v2"
        peer = CurrentNoteStore.open(peer_root, "android")
        peer_base = peer.save_local(NOTE, "Base", "A", NOW)
        peer.acknowledge(peer_base.change_id)
        self.assertEqual(base, peer_base)
        self.assertEqual("applied", peer.apply(latest).kind)
        self.assertEqual(latest, peer.get(NOTE))

        deletion = store.delete_local(NOTE, NOW + timedelta(seconds=3))
        self.assertEqual((base.change_id,), deletion.parent_change_ids)

    def test_valid_unknown_ancestry_becomes_explicit_conflict(self):
        store = self.open()
        local = store.save_local(NOTE, "Local", "complete local", NOW)
        store.acknowledge(local.change_id)
        remote = StateEnvelope.upsert(
            NOTE, ("a" * 64,), "android", NOW + timedelta(seconds=1),
            "Remote", "complete remote"
        )

        self.assertEqual("conflict", store.apply(remote).kind)
        self.assertEqual(2, len(store.conflict(NOTE).candidates))

    def test_concurrent_edits_preserve_both_complete_versions_until_resolution(self):
        store = self.open()
        base = store.save_local(NOTE, "Base", "original", NOW)
        store.acknowledge(base.change_id)
        local = store.save_local(NOTE, "Local", "linux body", NOW + timedelta(seconds=1))
        remote = StateEnvelope.upsert(
            NOTE,
            (base.change_id,),
            "android",
            NOW + timedelta(seconds=2),
            "Remote",
            "android body",
        )

        self.assertEqual("conflict", store.apply(remote).kind)
        conflict = store.conflict(NOTE)
        self.assertIsNotNone(conflict)
        self.assertEqual(
            {local.change_id, remote.change_id},
            {candidate.change_id for candidate in conflict.candidates},
        )

        resolved = store.resolve(NOTE, remote.change_id, NOW + timedelta(seconds=3))

        self.assertEqual("android body", resolved.body)
        self.assertEqual(tuple(sorted((local.change_id, remote.change_id))), resolved.parent_change_ids)
        self.assertIsNone(store.conflict(NOTE))
        self.assertEqual((resolved,), store.pending_states())

    def test_deletion_erases_content_and_rejects_every_old_live_carrier(self):
        store = self.open()
        live = store.save_local(NOTE, "Secret title", "secret body", NOW)

        deletion = store.delete_local(NOTE, NOW + timedelta(seconds=1))

        self.assertIsNone(store.get(NOTE))
        self.assertEqual((deletion,), store.pending_states())
        self.assertEqual("rejected-deleted", store.apply(live).kind)
        contents = b"".join(
            path.read_bytes() for path in self.root.rglob("*") if path.is_file()
        )
        self.assertNotIn(b"Secret title", contents)
        self.assertNotIn(b"secret body", contents)

    def test_incoming_deletion_wins_over_local_edit_and_queues_ack(self):
        store = self.open()
        local = store.save_local(NOTE, "Local", "must disappear", NOW)
        incoming = StateEnvelope.deletion(
            NOTE, (local.change_id,), "android", NOW + timedelta(seconds=1)
        )

        self.assertEqual("deleted", store.apply(incoming).kind)

        self.assertIsNone(store.get(NOTE))
        self.assertEqual((), store.pending_states())
        acknowledgments = store.pending_acks()
        self.assertEqual(1, len(acknowledgments))
        self.assertEqual(incoming.change_id, acknowledgments[0].acknowledged_change_id)

    def test_independent_deletions_acknowledge_without_restoring_content(self):
        store = self.open()
        live = store.save_local(NOTE, "Private", "gone", NOW)
        local_deletion = store.delete_local(NOTE, NOW + timedelta(seconds=1))
        remote_deletion = StateEnvelope.deletion(
            NOTE, (live.change_id,), "android", NOW + timedelta(seconds=2)
        )

        self.assertEqual("duplicate", store.apply(remote_deletion).kind)

        self.assertIsNone(store.get(NOTE))
        self.assertEqual((local_deletion,), store.pending_states())
        self.assertEqual(
            (remote_deletion.change_id,),
            tuple(ack.acknowledged_change_id for ack in store.pending_acks()),
        )

    def test_remote_descendant_replaces_obsolete_local_pending_state(self):
        store = self.open()
        local = store.save_local(NOTE, "Local", "sent earlier", NOW)
        remote = StateEnvelope.upsert(
            NOTE,
            (local.change_id,),
            "android",
            NOW + timedelta(seconds=1),
            "Remote edit",
            "peer already imported local",
        )

        self.assertEqual("applied", store.apply(remote).kind)

        self.assertEqual(remote, store.get(NOTE))
        self.assertEqual((), store.pending_states())

    def test_exact_acknowledgment_clears_only_matching_pending_state(self):
        store = self.open()
        first = store.save_local(NOTE, "One", "body", NOW)
        second = store.save_local(OTHER, "Two", "body", NOW)
        wrong = StateAckEnvelope.create(
            NOTE, "f" * 64, "android", "linux", NOW + timedelta(seconds=1)
        )

        self.assertFalse(store.acknowledge(wrong))
        self.assertEqual((first, second), store.pending_states())

        exact = StateAckEnvelope.create(
            NOTE, first.change_id, "android", "linux", NOW + timedelta(seconds=2)
        )
        self.assertTrue(store.acknowledge(exact))
        self.assertEqual((second,), store.pending_states())

    def test_open_repairs_current_committed_before_pending_move(self):
        store = self.open()
        state = StateEnvelope.upsert(NOTE, (), "linux", NOW, "Title", "Body")
        current = self.root / "current" / f"{NOTE}.json"
        staged = self.root / "pending" / f"{NOTE}.pending.tmp"
        current.write_bytes(state.to_bytes())
        staged.write_bytes(state.to_bytes())

        reopened = self.open()

        self.assertEqual(state, reopened.get(NOTE))
        self.assertEqual((state,), reopened.pending_states())
        self.assertFalse(staged.exists())

    def test_open_rejects_conflict_candidates_stored_under_another_note(self):
        self.open()
        directory = self.root / "conflicts" / str(NOTE)
        directory.mkdir()
        left = StateEnvelope.upsert(OTHER, (), "linux", NOW, "Left", "one")
        right = StateEnvelope.upsert(
            OTHER, (), "android", NOW + timedelta(seconds=1), "Right", "two"
        )
        (directory / f"{left.change_id}.json").write_bytes(left.to_bytes())
        (directory / f"{right.change_id}.json").write_bytes(right.to_bytes())

        with self.assertRaisesRegex(RuntimeError, "conflict candidate note"):
            self.open()


if __name__ == "__main__":
    unittest.main()
