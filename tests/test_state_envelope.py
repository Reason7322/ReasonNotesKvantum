from datetime import datetime, timezone
from pathlib import Path
import unittest
from uuid import UUID

from reasonnotes_sync.state_envelope import StateAckEnvelope, StateEnvelope, StateEnvelopeError


FIXTURES = Path(__file__).parent / "fixtures" / "sync-v2"
NOTE = UUID("11111111-1111-4111-8111-111111111111")
NOW = datetime(2026, 10, 24, 12, 30, tzinfo=timezone.utc)


def fixture(name: str) -> bytes:
    return (FIXTURES / name).read_bytes().removesuffix(b"\n")


class StateEnvelopeTest(unittest.TestCase):
    def test_java_fixtures_round_trip_byte_identically(self):
        self.assertEqual(StateEnvelope.from_bytes(fixture("upsert.json")).to_bytes(), fixture("upsert.json"))
        self.assertEqual(StateEnvelope.from_bytes(fixture("delete.json")).to_bytes(), fixture("delete.json"))
        self.assertEqual(StateAckEnvelope.from_bytes(fixture("ack.json")).to_bytes(), fixture("ack.json"))

    def test_deletion_contains_no_recoverable_content_and_tampering_fails(self):
        upsert = StateEnvelope.upsert(NOTE, (), "linux", NOW, "Title", "private body")
        deletion = StateEnvelope.deletion(NOTE, (upsert.change_id,), "linux", NOW)
        self.assertNotIn(b"private body", deletion.to_bytes())
        self.assertNotIn(b"title", deletion.to_bytes())
        with self.assertRaises(StateEnvelopeError):
            StateEnvelope.from_bytes(upsert.to_bytes().replace(b"private body", b"changed"))

    def test_acknowledgment_names_exact_change(self):
        ack = StateAckEnvelope.create(NOTE, "b" * 64, "android", "linux", NOW)
        self.assertEqual(ack.acknowledged_change_id, "b" * 64)
        self.assertEqual(StateAckEnvelope.from_bytes(ack.to_bytes()), ack)
