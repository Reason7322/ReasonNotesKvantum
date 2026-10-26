from datetime import datetime, timedelta, timezone
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from uuid import UUID

from reasonnotes_sync.current_store import CurrentNoteStore
from reasonnotes_sync.state_envelope import StateAckEnvelope, StateEnvelope
from reasonnotes_sync.sync import scan_inbox
from reasonnotes_sync.transport_bundle import (
    BundleItem,
    build_bundle,
    read_transport_bundle,
)


NOTE = UUID("dddddddd-4444-4444-8444-dddddddddddd")
SECOND = UUID("eeeeeeee-5555-4555-8555-eeeeeeeeeeee")
T0 = datetime(2026, 10, 25, 18, 0, tzinfo=timezone.utc)
FIXTURES = Path(__file__).parent / "fixtures" / "sync-v2-cross-platform"


def transcript():
    created = StateEnvelope.upsert(NOTE, (), "android", T0, "Shared", "base")
    fedora_edit = StateEnvelope.upsert(
        NOTE,
        (created.change_id,),
        "linux",
        T0 + timedelta(minutes=1),
        "Shared",
        "Fedora edit",
    )
    android_edit = StateEnvelope.upsert(
        NOTE,
        (created.change_id,),
        "android",
        T0 + timedelta(minutes=2),
        "Shared",
        "Android edit",
    )
    resolution = StateEnvelope.upsert(
        NOTE,
        (fedora_edit.change_id, android_edit.change_id),
        "linux",
        T0 + timedelta(minutes=3),
        "Shared",
        "Android edit",
    )
    deletion = StateEnvelope.deletion(
        NOTE,
        (resolution.change_id,),
        "android",
        T0 + timedelta(minutes=4),
    )
    acknowledgment = StateAckEnvelope.create(
        NOTE,
        deletion.change_id,
        "linux",
        "android",
        T0 + timedelta(minutes=5),
    )
    secondary_create = StateEnvelope.upsert(
        SECOND,
        (),
        "android",
        T0 + timedelta(minutes=6),
        "Erase both",
        "Never retain",
    )
    fedora_deletion = StateEnvelope.deletion(
        SECOND,
        (secondary_create.change_id,),
        "linux",
        T0 + timedelta(minutes=7),
    )
    return (
        created,
        fedora_edit,
        android_edit,
        resolution,
        deletion,
        acknowledgment,
        secondary_create,
        fedora_deletion,
    )


def carrier(kind, identity, envelope):
    return build_bundle((BundleItem(kind, identity, envelope),))[1]


def fixture_payloads():
    (
        created,
        fedora_edit,
        android_edit,
        resolution,
        deletion,
        acknowledgment,
        secondary_create,
        fedora_deletion,
    ) = transcript()
    return {
        "android-create.carrier.json": carrier(
            "state-v2", created.change_id, created.to_bytes()
        ),
        "fedora-edit.carrier.json": carrier(
            "state-v2", fedora_edit.change_id, fedora_edit.to_bytes()
        ),
        "android-conflict.carrier.json": carrier(
            "state-v2", android_edit.change_id, android_edit.to_bytes()
        ),
        "fedora-resolution.carrier.json": carrier(
            "state-v2", resolution.change_id, resolution.to_bytes()
        ),
        "android-delete.carrier.json": carrier(
            "state-v2", deletion.change_id, deletion.to_bytes()
        ),
        "fedora-ack.carrier.json": carrier(
            "ack-v2", acknowledgment.ack_id, acknowledgment.to_bytes()
        ),
        "android-secondary-create.carrier.json": carrier(
            "state-v2", secondary_create.change_id, secondary_create.to_bytes()
        ),
        "fedora-delete.carrier.json": carrier(
            "state-v2", fedora_deletion.change_id, fedora_deletion.to_bytes()
        ),
    }


def canonical_name(payload: bytes) -> str:
    return f"reasonnotes-bundle-v1-{hashlib.sha256(payload).hexdigest()}.json"


class CrossPlatformV2AcceptanceTests(unittest.TestCase):
    def test_platform_generated_carriers_match_canonical_fixture_bytes(self):
        for name, expected in fixture_payloads().items():
            with self.subTest(name=name):
                self.assertEqual(expected, (FIXTURES / name).read_bytes())
                members = read_transport_bundle(expected, canonical_name(expected))
                self.assertEqual(1, len(members))

    def test_android_carriers_create_conflict_while_deletion_remains_local_only(self):
        (
            created,
            fedora_edit,
            android_edit,
            resolution,
            deletion,
            _acknowledgment,
            secondary_create,
            fedora_deletion,
        ) = transcript()
        with TemporaryDirectory() as folder:
            root = Path(folder)
            store = CurrentNoteStore.open(root / "store", "linux")
            inbox = root / "inbox"
            inbox.mkdir()

            def import_fixture(name):
                payload = (FIXTURES / name).read_bytes()
                (inbox / canonical_name(payload)).write_bytes(payload)
                return scan_inbox(store, inbox, "linux")

            self.assertEqual(
                (created.change_id,), import_fixture("android-create.carrier.json").imported
            )
            local = store.save_local(
                NOTE, "Shared", "Fedora edit", T0 + timedelta(minutes=1)
            )
            self.assertEqual(fedora_edit, local)
            conflict_report = import_fixture("android-conflict.carrier.json")
            self.assertEqual((str(NOTE),), conflict_report.conflicts)
            self.assertEqual(
                {fedora_edit, android_edit}, set(store.conflict(NOTE).candidates)
            )
            resolved = store.resolve(
                NOTE, android_edit.change_id, T0 + timedelta(minutes=3)
            )
            self.assertEqual(resolution, resolved)

            deleted = import_fixture("android-delete.carrier.json")
            self.assertEqual((), deleted.imported)
            self.assertEqual((deletion.change_id,), deleted.duplicates)
            self.assertFalse(store.is_deleted(NOTE))
            self.assertEqual(resolution, store.get(NOTE))
            self.assertIsNone(store.conflict(NOTE))

            store.delete_local(NOTE)
            self.assertIsNone(store.get(NOTE))

            self.assertEqual(
                (secondary_create.change_id,),
                import_fixture("android-secondary-create.carrier.json").imported,
            )
            store.delete_local(SECOND)
            self.assertFalse(store.is_deleted(SECOND))
            self.assertIsNone(store.get(SECOND))

            late = scan_inbox(store, inbox, "linux")
            self.assertEqual((), late.errors)
            self.assertFalse(store.is_deleted(NOTE))
            self.assertIsNone(store.get(NOTE))
            combined = b"".join(
                path.read_bytes()
                for path in (root / "store").rglob("*")
                if path.is_file()
            )
            self.assertNotIn(b"Fedora edit", combined)
            self.assertNotIn(b"Android edit", combined)
            self.assertNotIn(b"Shared", combined)
            self.assertNotIn(b"Erase both", combined)
            self.assertNotIn(b"Never retain", combined)

    def test_fedora_ack_fixture_names_exact_android_deletion(self):
        values = transcript()
        deletion, acknowledgment = values[4], values[5]
        payload = (FIXTURES / "fedora-ack.carrier.json").read_bytes()
        (_name, data), = read_transport_bundle(payload, canonical_name(payload))

        parsed = StateAckEnvelope.from_bytes(data)

        self.assertEqual(acknowledgment, parsed)
        self.assertEqual(deletion.change_id, parsed.acknowledged_change_id)
        self.assertEqual("android", parsed.destination_device)


if __name__ == "__main__":
    unittest.main()
