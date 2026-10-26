from datetime import datetime, timedelta, timezone
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from uuid import UUID

from reasonnotes_sync.current_store import CurrentNoteStore
from reasonnotes_sync.cli import main as cli_main
from reasonnotes_sync.delivery import DeliveryLedger
from reasonnotes_sync.envelope import Revision
from reasonnotes_sync.kdeconnect_linux import TransferRequest
from reasonnotes_sync.legacy_migration import migrate_legacy_repository
from reasonnotes_sync.repository import Repository
from reasonnotes_sync.state_envelope import StateAckEnvelope, StateEnvelope
from reasonnotes_sync.sync import (
    return_current_acknowledgments,
    scan_inbox,
    sync_linux,
    sync_linux_confirmed,
)
from reasonnotes_sync.transport_bundle import BundleItem, build_bundle


NOTE_A = UUID("aaaaaaaa-1111-4111-8111-aaaaaaaaaaaa")
NOTE_B = UUID("bbbbbbbb-2222-4222-8222-bbbbbbbbbbbb")
T0 = datetime(2026, 10, 25, 12, 0, tzinfo=timezone.utc)


class FakeAdapter:
    device_id = "physical-peer"

    def __init__(self, *, reachable=True, accepted=True):
        self.is_reachable = reachable
        self.accepted = accepted
        self.paths: list[Path] = []

    def reachable(self):
        return self.is_reachable

    def request_transfer(self, path):
        self.paths.append(Path(path))
        return TransferRequest(
            self.accepted,
            False,
            "request accepted" if self.accepted else "request rejected",
        )


def copy_carrier(path: Path, inbox: Path) -> Path:
    destination = inbox / path.name
    destination.write_bytes(path.read_bytes())
    return destination


def carrier_kinds(path: Path) -> tuple[str, ...]:
    return tuple(item["kind"] for item in json.loads(path.read_text())["items"])


class CurrentStateTransportTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.linux = CurrentNoteStore.open(self.base / "linux", "linux")
        self.android = CurrentNoteStore.open(self.base / "android", "android")
        self.linux_inbox = self.base / "linux-inbox"
        self.android_inbox = self.base / "android-inbox"
        self.linux_inbox.mkdir()
        self.android_inbox.mkdir()

    def transfer(self, sender, sender_inbox, receiver, receiver_inbox):
        adapter = FakeAdapter()
        report = sync_linux(sender, sender_inbox, adapter)
        self.assertEqual(1, len(adapter.paths))
        copy_carrier(adapter.paths[0], receiver_inbox)
        scan = scan_inbox(receiver, receiver_inbox, receiver.device_id)
        return report, scan

    def test_create_edit_round_trip_and_exact_acknowledgment_clearing(self):
        first = self.linux.save_local(NOTE_A, "First", "from Fedora", T0)

        sent, imported = self.transfer(
            self.linux, self.linux_inbox, self.android, self.android_inbox
        )

        self.assertEqual((first.change_id,), sent.requested)
        self.assertEqual((first.change_id,), imported.imported)
        self.assertEqual("from Fedora", self.android.get(NOTE_A).body)
        self.assertEqual(1, len(self.android.pending_acks()))

        returned, confirmed = self.transfer(
            self.android, self.android_inbox, self.linux, self.linux_inbox
        )
        self.assertEqual((first.change_id,), returned.requested)
        self.assertEqual((first.change_id,), confirmed.confirmed)
        self.assertEqual((), self.linux.pending_states())
        self.android = CurrentNoteStore.open(self.android.root, "android")
        scan_inbox(self.android, self.android_inbox, "android")
        self.assertEqual((), self.android.pending_acks())
        original = next(self.android_inbox.glob("reasonnotes-bundle-v1-*.json"))
        redelivery = original.with_name(f"{original.stem} (1).json")
        redelivery.write_bytes(original.read_bytes())
        scan_inbox(self.android, self.android_inbox, "android")
        self.assertEqual(1, len(self.android.pending_acks()))

        edited = self.android.save_local(
            NOTE_A, "First", "edited on Android", T0 + timedelta(seconds=2)
        )
        _sent, imported = self.transfer(
            self.android, self.android_inbox, self.linux, self.linux_inbox
        )
        self.assertEqual((edited.change_id,), imported.imported)
        self.assertEqual("edited on Android", self.linux.get(NOTE_A).body)

    def test_states_are_applied_before_acks_and_replays_are_idempotent(self):
        pending = self.linux.save_local(NOTE_A, "A", "pending", T0)
        incoming = StateEnvelope.upsert(
            NOTE_B, (), "android", T0 + timedelta(seconds=1), "B", "incoming"
        )
        acknowledgment = StateAckEnvelope.create(
            NOTE_A,
            pending.change_id,
            "android",
            "linux",
            T0 + timedelta(seconds=2),
        )
        name, payload = build_bundle(
            (
                BundleItem("ack-v2", acknowledgment.ack_id, acknowledgment.to_bytes()),
                BundleItem("state-v2", incoming.change_id, incoming.to_bytes()),
            )
        )
        path = self.linux_inbox / name
        path.write_bytes(payload)

        first = scan_inbox(self.linux, self.linux_inbox, "linux")
        replay = scan_inbox(self.linux, self.linux_inbox, "linux")

        self.assertEqual((incoming.change_id,), first.imported)
        self.assertEqual((pending.change_id,), first.confirmed)
        self.assertEqual("incoming", self.linux.get(NOTE_B).body)
        self.assertEqual((), self.linux.pending_states())
        self.assertEqual((), replay.imported)
        self.assertEqual((), replay.confirmed)
        self.assertEqual((), replay.errors)

    def test_peer_may_return_a_state_originally_authored_on_this_device(self):
        good = StateEnvelope.upsert(NOTE_A, (), "android", T0, "Good", "safe")
        returned = StateEnvelope.upsert(
            NOTE_B, (), "linux", T0, "Returned", "restore me"
        )
        name, payload = build_bundle(
            (
                BundleItem("state-v2", good.change_id, good.to_bytes()),
                BundleItem("state-v2", returned.change_id, returned.to_bytes()),
            )
        )
        (self.linux_inbox / name).write_bytes(payload)

        report = scan_inbox(self.linux, self.linux_inbox, "linux")

        self.assertEqual({good.change_id, returned.change_id}, set(report.imported))
        self.assertEqual("safe", self.linux.get(NOTE_A).body)
        self.assertEqual("restore me", self.linux.get(NOTE_B).body)
        self.assertEqual((), report.errors)

    def test_explicit_sync_restages_a_confirmed_unchanged_live_note(self):
        live = self.linux.save_local(NOTE_A, "A", "unchanged", T0)
        self.assertTrue(self.linux.acknowledge(live.change_id))
        self.assertEqual((), self.linux.pending_states())

        adapter = FakeAdapter()
        report = sync_linux(self.linux, self.linux_inbox, adapter)

        self.assertEqual((live.change_id,), report.requested)
        self.assertEqual((live,), self.linux.pending_states())

    def test_one_sync_from_surviving_device_restores_locally_deleted_receiver(self):
        live = self.linux.save_local(NOTE_A, "Private title", "private body", T0)
        _sent, imported = self.transfer(
            self.linux, self.linux_inbox, self.android, self.android_inbox
        )
        self.assertEqual((live.change_id,), imported.imported)
        self.transfer(self.android, self.android_inbox, self.linux, self.linux_inbox)
        self.assertEqual((), self.linux.pending_states())
        self.android.delete_local(NOTE_A)
        self.assertIsNone(self.android.get(NOTE_A))

        _sent, restored = self.transfer(
            self.linux, self.linux_inbox, self.android, self.android_inbox
        )

        self.assertEqual((live.change_id,), restored.imported)
        self.assertEqual("private body", self.android.get(NOTE_A).body)

    def test_if_both_devices_delete_locally_explicit_sync_sends_no_state(self):
        self.linux.save_local(NOTE_A, "A", "body", T0)
        self.transfer(self.linux, self.linux_inbox, self.android, self.android_inbox)
        self.linux.delete_local(NOTE_A)
        self.android.delete_local(NOTE_A)
        adapter = FakeAdapter()

        report = sync_linux(self.linux, self.linux_inbox, adapter)

        self.assertEqual((), report.requested)
        self.assertEqual([], adapter.paths)
        self.assertIsNone(self.linux.get(NOTE_A))
        self.assertIsNone(self.android.get(NOTE_A))

    def test_processed_historical_carrier_does_not_restore_locally_deleted_note(self):
        live = self.linux.save_local(NOTE_A, "A", "body", T0)
        _sent, imported = self.transfer(
            self.linux, self.linux_inbox, self.android, self.android_inbox
        )
        self.assertEqual((live.change_id,), imported.imported)
        self.android.delete_local(NOTE_A)

        rescanned = scan_inbox(self.android, self.android_inbox, "android")

        self.assertEqual((), rescanned.imported)
        self.assertEqual((), rescanned.errors)
        self.assertIsNone(self.android.get(NOTE_A))

    def test_incoming_legacy_deletion_is_ignored_without_error_or_ack(self):
        live = self.android.save_local(NOTE_A, "A", "body", T0)
        deletion = StateEnvelope.deletion(
            NOTE_A, (live.change_id,), "linux", T0 + timedelta(seconds=1)
        )
        name, payload = build_bundle((
            BundleItem("state-v2", deletion.change_id, deletion.to_bytes()),
        ))
        (self.android_inbox / name).write_bytes(payload)

        report = scan_inbox(self.android, self.android_inbox, "android")

        self.assertEqual((), report.errors)
        self.assertEqual((deletion.change_id,), report.duplicates)
        self.assertEqual((), self.android.pending_acks())
        self.assertEqual("body", self.android.get(NOTE_A).body)

    def test_automatic_ack_return_sends_only_receipts(self):
        incoming = StateEnvelope.upsert(
            NOTE_A, (), "android", T0, "A", "body"
        )
        self.assertEqual("applied", self.linux.apply(incoming).kind)
        adapter = FakeAdapter()

        requested, errors = return_current_acknowledgments(self.linux, adapter)

        self.assertEqual(1, len(requested))
        self.assertEqual((), errors)
        self.assertEqual(("ack-v2",), carrier_kinds(adapter.paths[0]))
        self.assertEqual((), self.linux.pending_acks())
        self.assertEqual((), self.linux.pending_states())

    def test_failed_automatic_ack_return_remains_retryable(self):
        incoming = StateEnvelope.upsert(
            NOTE_A, (), "android", T0, "A", "body"
        )
        self.linux.apply(incoming)

        requested, errors = return_current_acknowledgments(
            self.linux, FakeAdapter(accepted=False)
        )

        self.assertEqual((), requested)
        self.assertTrue(errors)
        self.assertEqual(1, len(self.linux.pending_acks()))

    def test_selection_sends_only_latest_selected_state_but_all_pending_acks(self):
        selected = self.linux.save_local(NOTE_A, "A", "old", T0)
        selected = self.linux.save_local(
            NOTE_A, "A", "latest", T0 + timedelta(seconds=1)
        )
        other = self.linux.save_local(NOTE_B, "B", "other", T0)
        incoming = StateEnvelope.upsert(
            UUID("cccccccc-3333-4333-8333-cccccccccccc"),
            (),
            "android",
            T0,
            "Incoming",
            "ack me",
        )
        self.linux.apply(incoming)
        adapter = FakeAdapter()

        report = sync_linux(
            self.linux,
            self.linux_inbox,
            adapter,
            selected_note_ids=(NOTE_A,),
        )

        self.assertEqual((selected.change_id,), report.requested)
        self.assertNotIn(other.change_id, report.requested)
        self.assertEqual((other.change_id,), tuple(
            state.change_id for state in self.linux.pending_states()
            if state.note_id == NOTE_B
        ))
        self.assertEqual(("ack-v2", "state-v2"), carrier_kinds(adapter.paths[0]))

    def test_old_v1_delivery_failures_do_not_affect_current_operation_status(self):
        old_id = "f" * 64
        ledger = DeliveryLedger(self.linux.root)
        ledger.register_local(old_id, "android")
        for second in range(3):
            ledger.record_requested(
                old_id,
                "android",
                T0 + timedelta(seconds=second),
                observer_device="linux",
            )
        current = self.linux.save_local(NOTE_A, "Current", "send me", T0)

        report = sync_linux(self.linux, self.linux_inbox, FakeAdapter())

        self.assertEqual((current.change_id,), report.requested)
        self.assertEqual((), report.errors)

    def test_unreachable_peer_keeps_each_note_retryable_and_selection_recovers_one(self):
        first = self.linux.save_local(NOTE_A, "A", "one", T0)
        second = self.linux.save_local(NOTE_B, "B", "two", T0)

        failed = sync_linux(
            self.linux, self.linux_inbox, FakeAdapter(reachable=False)
        )
        retried = sync_linux(
            self.linux,
            self.linux_inbox,
            FakeAdapter(),
            selected_note_ids=(NOTE_A,),
        )

        self.assertEqual((), failed.requested)
        self.assertTrue(any("unavailable" in error for error in failed.errors))
        self.assertEqual((first.change_id,), retried.requested)
        self.assertIn(second.change_id, retried.pending)

    def test_acknowledgment_for_wrong_note_does_not_clear_pending_change(self):
        current = self.linux.save_local(NOTE_A, "A", "body", T0)
        wrong = StateAckEnvelope.create(
            NOTE_B,
            current.change_id,
            "android",
            "linux",
            T0 + timedelta(seconds=1),
        )
        name, payload = build_bundle((
            BundleItem("ack-v2", wrong.ack_id, wrong.to_bytes()),
        ))
        (self.linux_inbox / name).write_bytes(payload)

        report = scan_inbox(self.linux, self.linux_inbox, "linux")

        self.assertEqual((current,), self.linux.pending_states())
        self.assertEqual((), report.confirmed)
        self.assertTrue(any("does not match" in error for error in report.errors))

    def test_confirmed_sync_waits_for_exact_v2_ack(self):
        current = self.linux.save_local(NOTE_A, "A", "body", T0)
        adapter = FakeAdapter()
        elapsed = [0.0]

        def monotonic():
            return elapsed[0]

        def sleep(seconds):
            elapsed[0] += seconds
            acknowledgment = StateAckEnvelope.create(
                NOTE_A,
                current.change_id,
                "android",
                "linux",
                T0 + timedelta(seconds=1),
            )
            name, payload = build_bundle((
                BundleItem("ack-v2", acknowledgment.ack_id, acknowledgment.to_bytes()),
            ))
            (self.linux_inbox / name).write_bytes(payload)

        report = sync_linux_confirmed(
            self.linux,
            self.linux_inbox,
            adapter,
            timeout_seconds=1.0,
            poll_interval_seconds=0.1,
            monotonic=monotonic,
            sleeper=sleep,
        )

        self.assertEqual((current.change_id,), report.requested)
        self.assertEqual((current.change_id,), report.confirmations)
        self.assertEqual((), report.errors)

    def test_cli_explicit_current_state_mode_uses_v2_without_legacy_status(self):
        current = self.linux.save_local(NOTE_A, "A", "body", T0)
        stdout = StringIO()

        result = cli_main(
            [
                "--root",
                str(self.linux.root),
                "--current-state",
                "sync",
                "--inbox",
                str(self.linux_inbox),
                "--device-id",
                "physical-peer",
            ],
            stdout=stdout,
            adapter_factory=lambda _device: FakeAdapter(),
        )

        self.assertEqual(0, result)
        self.assertIn(f"transfer-requested={current.change_id}", stdout.getvalue())

    def test_valid_v1_revision_imports_but_outgoing_remains_v2_only(self):
        revision = Revision.create(
            NOTE_A,
            (),
            "android",
            T0,
            False,
            "# Legacy title\n\nLegacy body",
        )
        name, payload = build_bundle((
            BundleItem("revision", revision.revision_id, revision.serialize()),
        ))
        (self.linux_inbox / name).write_bytes(payload)

        imported = scan_inbox(self.linux, self.linux_inbox, "linux")
        adapter = FakeAdapter()
        sync_linux(self.linux, self.linux_inbox, adapter)

        self.assertEqual(1, len(imported.imported))
        self.assertEqual("Legacy title", self.linux.get(NOTE_A).title)
        self.assertEqual("Legacy body", self.linux.get(NOTE_A).body)
        self.assertNotIn("revision", carrier_kinds(adapter.paths[0]))
        self.assertIn("ack-v2", carrier_kinds(adapter.paths[0]))

    def test_cli_current_state_status_reads_only_current_and_pending_records(self):
        current = self.linux.save_local(NOTE_A, "A", "body", T0)
        DeliveryLedger(self.linux.root).register_local("e" * 64, "android")
        stdout = StringIO()

        result = cli_main(
            ["--root", str(self.linux.root), "--current-state", "status"],
            stdout=stdout,
        )

        self.assertEqual(0, result)
        self.assertIn(f"heads={current.change_id}", stdout.getvalue())
        self.assertIn(f"pending={current.change_id}", stdout.getvalue())
        self.assertNotIn("e" * 64, stdout.getvalue())

    def test_migration_marks_known_v1_history_so_old_exchange_files_are_not_replayed(self):
        legacy_root = self.base / "legacy"
        legacy = Repository.open(legacy_root)
        revision = legacy.create_revision(
            NOTE_A, "# Existing\n\nAlready migrated", "android", T0
        )
        name, payload = build_bundle((
            BundleItem("revision", revision.revision_id, revision.serialize()),
        ))
        old_inbox = self.base / "old-inbox"
        old_inbox.mkdir()
        (old_inbox / name).write_bytes(payload)
        active = self.base / "migrated-v2"

        migrate_legacy_repository(
            legacy_root, self.base / "migrated-v2.staging", active
        )
        migrated = CurrentNoteStore.open(active, "linux")
        report = scan_inbox(migrated, old_inbox, "linux")

        self.assertEqual((), report.imported)
        self.assertEqual((), report.errors)
        self.assertEqual((), migrated.pending_acks())


if __name__ == "__main__":
    unittest.main()
