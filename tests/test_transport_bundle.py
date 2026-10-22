from datetime import datetime, timezone
import hashlib
import json
from unittest.mock import patch
import unittest
from uuid import UUID

from reasonnotes_sync.envelope import Revision
from reasonnotes_sync.receipt import ReceiptEnvelope
from reasonnotes_sync.transport_bundle import (
    BundleItem,
    TransportBundleError,
    build_bundle,
    read_transport_bundle,
)


NOTE = UUID("11111111-1111-4111-8111-111111111111")
REVISION_ID = "6d7ca32a49c9a246fb7808ba06c541c1b3dacc7add6a874cf5aefb375e94025a"
RECEIPT_ID = "5656b6c8e23ef55a998b960d770762d522381fd99fad86d5b595664aeed3e0f1"
EXPECTED_NAME = (
    "reasonnotes-bundle-v1-"
    "0374b8899e50de963b797ef5d45cabe850c72dcbbacd24f45808c474093a1f3b.json"
)
EXPECTED_TEXT = (
    '{"format":"reasonnotes-transport-bundle","items":['
    '{"envelope":"---\\nreasonnotes-receipt-format: 1\\nreceipt-id: '
    '5656b6c8e23ef55a998b960d770762d522381fd99fad86d5b595664aeed3e0f1\\n'
    'note-id: 11111111-1111-4111-8111-111111111111\\nrevision-id: '
    '6d7ca32a49c9a246fb7808ba06c541c1b3dacc7add6a874cf5aefb375e94025a\\n'
    'acknowledging-device: android\\ndestination-device: linux\\n'
    'imported-utc: 2026-10-22T03:04:06Z\\n---\\n","id":"'
    '5656b6c8e23ef55a998b960d770762d522381fd99fad86d5b595664aeed3e0f1",'
    '"kind":"receipt"},{"envelope":"---\\nreasonnotes-format: 1\\n'
    'note-id: 11111111-1111-4111-8111-111111111111\\nrevision-id: '
    '6d7ca32a49c9a246fb7808ba06c541c1b3dacc7add6a874cf5aefb375e94025a\\n'
    'parents: \\norigin-device: linux\\nmodified-utc: 2026-10-22T03:04:05Z\\n'
    'deleted: false\\nbody-sha256: '
    '1787b3e8ee79c0e1bf558994dbb836d8875d5763818dff36125f17f4a9b6a36b\\n'
    '---\\n# Zażółć 📝\\n\\nLine \\"two\\" \\\\ slash","id":"'
    '6d7ca32a49c9a246fb7808ba06c541c1b3dacc7add6a874cf5aefb375e94025a",'
    '"kind":"revision"}],"version":1}'
)


class TransportBundleTests(unittest.TestCase):
    def setUp(self):
        self.revision = Revision.create(
            NOTE,
            (),
            "linux",
            datetime(2026, 10, 22, 3, 4, 5, tzinfo=timezone.utc),
            False,
            '# Zażółć 📝\n\nLine "two" \\ slash',
        )
        self.receipt = ReceiptEnvelope.create(
            NOTE,
            self.revision.revision_id,
            "android",
            "linux",
            datetime(2026, 10, 22, 3, 4, 6, tzinfo=timezone.utc),
        )
        self.items = (
            BundleItem("revision", self.revision.revision_id, self.revision.serialize()),
            BundleItem("receipt", self.receipt.receipt_id, self.receipt.serialize()),
        )

    def test_literal_unicode_fixture_is_canonical_and_cross_language_stable(self):
        self.assertEqual(self.revision.revision_id, REVISION_ID)
        self.assertEqual(self.receipt.receipt_id, RECEIPT_ID)

        name, payload = build_bundle(self.items)

        self.assertEqual(name, EXPECTED_NAME)
        self.assertEqual(payload, EXPECTED_TEXT.encode("utf-8"))
        self.assertEqual(len(payload), 978)

    def test_read_validates_all_items_then_returns_legacy_names_and_bytes(self):
        name, payload = build_bundle(self.items)

        result = read_transport_bundle(payload, name)

        self.assertEqual(
            result,
            (
                (f"{self.receipt.receipt_id}.receipt.md", self.receipt.serialize()),
                (f"{self.revision.revision_id}.md", self.revision.serialize()),
            ),
        )

    def test_duplicate_identity_is_rejected(self):
        with self.assertRaisesRegex(TransportBundleError, "duplicate"):
            build_bundle((self.items[0], self.items[0]))

    def test_noncanonical_key_order_is_rejected_even_with_matching_filename_hash(self):
        _, payload = build_bundle((self.items[0],))
        value = json.loads(payload)
        noncanonical = json.dumps(
            {"version": value["version"], "format": value["format"], "items": value["items"]},
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        name = f"reasonnotes-bundle-v1-{hashlib.sha256(noncanonical).hexdigest()}.json"

        with self.assertRaisesRegex(TransportBundleError, "canonical"):
            read_transport_bundle(noncanonical, name)

    def test_identity_mismatch_rejects_complete_payload(self):
        _, payload = build_bundle(self.items)
        value = json.loads(payload)
        value["items"][1]["id"] = RECEIPT_ID
        invalid = json.dumps(
            value, ensure_ascii=False, separators=(",", ":"), sort_keys=True
        ).encode("utf-8")
        name = f"reasonnotes-bundle-v1-{hashlib.sha256(invalid).hexdigest()}.json"

        with self.assertRaisesRegex(TransportBundleError, "identity"):
            read_transport_bundle(invalid, name)

    def test_malformed_utf8_and_wrong_filename_hash_are_rejected(self):
        with self.assertRaisesRegex(TransportBundleError, "UTF-8"):
            read_transport_bundle(b"\xff", "reasonnotes-bundle-v1-" + "0" * 64 + ".json")

        name, payload = build_bundle((self.items[0],))
        with self.assertRaisesRegex(TransportBundleError, "hash"):
            read_transport_bundle(payload + b" ", name)

    def test_count_and_payload_limits_apply_to_create_and_read(self):
        with patch("reasonnotes_sync.transport_bundle.MAX_ITEMS", 1):
            with self.assertRaisesRegex(TransportBundleError, "items"):
                build_bundle(self.items)

        name, payload = build_bundle((self.items[0],))
        with patch("reasonnotes_sync.transport_bundle.MAX_PAYLOAD_BYTES", len(payload) - 1):
            with self.assertRaisesRegex(TransportBundleError, "payload"):
                read_transport_bundle(payload, name)


if __name__ == "__main__":
    unittest.main()
