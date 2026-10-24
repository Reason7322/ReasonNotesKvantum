from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from uuid import UUID

from reasonnotes_sync.delivery import DeliveryLedger, DeliveryState
from reasonnotes_sync.envelope import Revision
from reasonnotes_sync.kdeconnect_linux import TransferRequest
from reasonnotes_sync.receipt import ReceiptEnvelope
from reasonnotes_sync.repository import Repository
from reasonnotes_sync.sync import scan_inbox, sync_linux, sync_linux_confirmed


NOTE_A = UUID("aaaaaaaa-1111-4111-8111-111111111111")
NOTE_B = UUID("bbbbbbbb-2222-4222-8222-222222222222")
T0 = datetime(2026, 10, 21, 9, 0, 0, tzinfo=timezone.utc)
DEVICE_ID = "52548cf9710c43cab2fa73ed4671aea9"


class FakeAdapter:
    device_id = DEVICE_ID

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


class ControlledTime:
    def __init__(self, on_sleep=None):
        self.value = 0.0
        self.on_sleep = on_sleep
        self.sleeps = 0

    def monotonic(self):
        return self.value

    def sleep(self, seconds):
        self.value += seconds
        self.sleeps += 1
        if self.on_sleep is not None:
            self.on_sleep(self.sleeps)


class ConfirmedSyncTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        base = Path(self.temporary.name)
        self.root = base / "repository"
        self.inbox = base / "inbox"
        self.inbox.mkdir()
        self.repository = Repository.open(
            self.root,
            local_device="linux",
            target_device="android",
        )

    def write_receipt(self, revision, seconds=1):
        receipt = ReceiptEnvelope.create(
            revision.note_id,
            revision.revision_id,
            "android",
            "linux",
            T0 + timedelta(seconds=seconds),
        )
        (self.inbox / receipt.transport_filename()).write_bytes(receipt.serialize())
        return receipt

    def run_confirmed(self, adapter, clock, **changes):
        values = {
            "timeout_seconds": 2.0,
            "poll_interval_seconds": 0.5,
            "monotonic": clock.monotonic,
            "sleeper": clock.sleep,
        }
        values.update(changes)
        return sync_linux_confirmed(
            self.repository,
            self.inbox,
            adapter,
            **values,
        )

    def test_success_requires_durable_receipts_for_exact_requested_revisions(self):
        selected = self.repository.create_revision(NOTE_A, "A", "linux", T0)
        unselected = self.repository.create_revision(NOTE_B, "B", "linux", T0)
        adapter = FakeAdapter()
        clock = ControlledTime(
            lambda count: self.write_receipt(selected) if count == 1 else None
        )

        report = self.run_confirmed(
            adapter,
            clock,
            selected_note_ids=(NOTE_A,),
        )

        self.assertEqual(report.requested, (selected.revision_id,))
        self.assertEqual(report.confirmations, (selected.revision_id,))
        self.assertEqual(report.errors, ())
        self.assertEqual(
            DeliveryLedger(self.root).entry(selected.revision_id, "android").state,
            DeliveryState.CONFIRMED,
        )
        self.assertEqual(
            DeliveryLedger(self.root).entry(unselected.revision_id, "android").state,
            DeliveryState.PENDING,
        )

    def test_request_acceptance_without_receipt_times_out_as_error(self):
        revision = self.repository.create_revision(NOTE_A, "A", "linux", T0)
        clock = ControlledTime()

        report = self.run_confirmed(FakeAdapter(), clock, timeout_seconds=1.0)

        self.assertEqual(report.requested, (revision.revision_id,))
        self.assertEqual(report.confirmations, ())
        self.assertTrue(any("timed out" in error.casefold() for error in report.errors))
        self.assertEqual(
            DeliveryLedger(self.root).entry(revision.revision_id, "android").state,
            DeliveryState.TRANSFER_REQUESTED,
        )

    def test_partial_confirmation_then_disconnect_is_error(self):
        first = self.repository.create_revision(NOTE_A, "A", "linux", T0)
        second = self.repository.create_revision(NOTE_B, "B", "linux", T0)
        adapter = FakeAdapter()

        def disconnect_after_first_poll(count):
            if count == 1:
                self.write_receipt(first)
                adapter.is_reachable = False

        clock = ControlledTime(disconnect_after_first_poll)
        report = self.run_confirmed(adapter, clock)

        self.assertEqual(set(report.requested), {first.revision_id, second.revision_id})
        self.assertEqual(report.confirmations, (first.revision_id,))
        self.assertTrue(any("disconnected" in error.casefold() for error in report.errors))
        self.assertEqual(
            DeliveryLedger(self.root).entry(second.revision_id, "android").state,
            DeliveryState.TRANSFER_REQUESTED,
        )

    def test_initial_unreachable_or_rejected_request_returns_error_immediately(self):
        self.repository.create_revision(NOTE_A, "A", "linux", T0)

        unreachable = self.run_confirmed(FakeAdapter(reachable=False), ControlledTime())
        self.assertTrue(any("unavailable" in error.casefold() for error in unreachable.errors))
        self.assertEqual(unreachable.requested, ())

        rejected = self.run_confirmed(FakeAdapter(accepted=False), ControlledTime())
        self.assertTrue(any("rejected" in error.casefold() for error in rejected.errors))
        self.assertEqual(rejected.requested, ())

    def test_empty_and_already_confirmed_scopes_are_neutral_no_ops(self):
        empty = self.run_confirmed(FakeAdapter(), ControlledTime())
        self.assertEqual(empty.requested, ())
        self.assertEqual(empty.errors, ())

        revision = self.repository.create_revision(NOTE_A, "A", "linux", T0)
        sync_linux(self.repository, self.inbox, FakeAdapter())
        self.write_receipt(revision)
        scan_inbox(self.repository, self.inbox, "linux")

        confirmed = self.run_confirmed(FakeAdapter(), ControlledTime())
        self.assertEqual(confirmed.requested, ())
        self.assertEqual(confirmed.errors, ())

    def test_retry_limit_is_an_error_instead_of_a_silent_no_op(self):
        revision = self.repository.create_revision(NOTE_A, "A", "linux", T0)
        for _ in range(3):
            sync_linux(
                self.repository,
                self.inbox,
                FakeAdapter(),
                retry_unconfirmed=True,
            )
        self.assertEqual(
            DeliveryLedger(self.root).entry(revision.revision_id, "android").state,
            DeliveryState.NEEDS_ATTENTION,
        )

        report = self.run_confirmed(FakeAdapter(), ControlledTime())

        self.assertEqual(report.requested, ())
        self.assertTrue(
            any("needs attention" in error.casefold() for error in report.errors),
            report.errors,
        )

    def test_successful_current_import_is_not_failed_by_unrelated_exhausted_history(self):
        exhausted = self.repository.create_revision(NOTE_A, "Old local", "linux", T0)
        for _ in range(3):
            sync_linux(self.repository, self.inbox, FakeAdapter(), retry_unconfirmed=True)
        self.assertEqual(
            DeliveryLedger(self.root).entry(exhausted.revision_id, "android").state,
            DeliveryState.NEEDS_ATTENTION,
        )
        remote = Revision.create(
            NOTE_B, (), "android", T0 + timedelta(seconds=10), False,
            "Remote current operation",
        )
        (self.inbox / "remote-current.md").write_bytes(remote.serialize())

        report = self.run_confirmed(FakeAdapter(), ControlledTime())

        self.assertEqual((remote.revision_id,), report.imports)
        self.assertEqual(1, len(report.receipt_requested))
        self.assertEqual((), report.errors)


if __name__ == "__main__":
    unittest.main()
