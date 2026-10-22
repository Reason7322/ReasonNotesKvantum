"""Send only newly queued, verified destination import acknowledgments.

Never sends note content and never automatically retries already requested
receipts. KDE Connect availability and transfer request are not proof of
receipt at the Android endpoint.
"""

from __future__ import annotations

from datetime import datetime, timezone

from .receipt import ReceiptStore
from .transport_bundle import BundleItem, TransportBundleError, write_bundle


def return_pending_receipts(repository, adapter, *, clock=None):
    """Return (requested_count, warnings) after a successful incoming scan."""
    if repository.target_device is None:
        raise ValueError("destination peer is not configured")
    store = ReceiptStore(repository.root)
    eligible = store.eligible(repository.target_device)
    if not eligible:
        return 0, ()
    if not adapter.reachable():
        return 0, ("KDE Connect phone is not reachable for receipts",)
    now = clock or (lambda: datetime.now(timezone.utc).replace(microsecond=0))
    try:
        items = tuple(
            BundleItem(
                "receipt",
                receipt_id,
                store.outbox_path(receipt_id).read_bytes(),
            )
            for receipt_id in eligible
        )
        path = write_bundle(repository.root / "transport" / "outbox", items)
        result = adapter.request_transfer(path)
        if not result.accepted:
            return 0, ("Receipt return bundle request failed",)
        observed = now()
        for receipt_id in eligible:
            store.record_requested(
                receipt_id,
                repository.target_device,
                observed,
            )
        return len(eligible), ()
    except (OSError, ValueError, RuntimeError, TransportBundleError):
        return 0, ("Receipt return bundle unavailable",)
