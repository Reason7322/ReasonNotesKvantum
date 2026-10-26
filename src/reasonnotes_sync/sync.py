"""Scan-before-send Linux synchronization orchestration."""

from collections.abc import Collection
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import re
import time
from uuid import UUID

from .bundle import (
    BundleError,
    MAX_ARCHIVE_BYTES,
    is_bundle_name,
    read_bundle,
)
from .current_store import CurrentNoteStore
from .delivery import DeliveryLedger, DeliveryState
from .envelope import EnvelopeError, Revision
from .receipt import ReceiptEnvelope, ReceiptError, ReceiptStore
from .repository import Repository
from .state_envelope import StateAckEnvelope, StateEnvelope, StateEnvelopeError
from .transport_bundle import (
    BundleItem,
    MAX_PAYLOAD_BYTES,
    TransportBundleError,
    is_transport_bundle_name,
    read_transport_bundle,
    write_bundle,
)


_FORMAT_MARKER = b"---\nreasonnotes-format: 1\n"
_RECEIPT_FORMAT_MARKER = b"---\nreasonnotes-receipt-format: 1\n"


def _hash_name(value: str) -> bool:
    return len(value) == 64 and all(char in "0123456789abcdef" for char in value)


def _extensionless_kde_name(name: str) -> bool:
    # KDE Connect can receive multi-share FileProvider URIs with a numeric
    # transfer name rather than the original .md filename.
    return _hash_name(name) or (name.isascii() and name.isdigit() and 12 <= len(name) <= 16)


def _incoming_files(directory: Path, *, downloads: bool):
    """Yield likely received envelopes; do not touch unrelated downloaded files."""
    for path in sorted(directory.iterdir()):
        if not path.is_file() or path.is_symlink():
            continue
        name = path.name
        if path.suffix.lower() == ".md":
            stem = path.stem
            if downloads:
                # KDE Connect appends " (1)" when an existing filename collides.
                match = re.fullmatch(r"(.+) \(([1-9][0-9]*)\)", stem)
                if match:
                    stem = match.group(1)
                canonical_id = stem.removesuffix(".receipt")
                if not (_hash_name(canonical_id) or stem.startswith("reasonnotes-")):
                    continue
        elif path.suffix.lower() == ".zip":
            if not is_bundle_name(name):
                continue
        elif path.suffix.lower() == ".json":
            if not is_transport_bundle_name(name):
                continue
        elif not (not path.suffix and _extensionless_kde_name(name)):
            continue
        yield path


@dataclass(frozen=True, slots=True)
class ScanReport:
    imported: tuple[str, ...]
    duplicates: tuple[str, ...]
    confirmed: tuple[str, ...]
    duplicate_receipts: tuple[str, ...]
    receipts_queued: tuple[str, ...]
    quarantined: tuple[str, ...]
    conflicts: tuple[str, ...]
    errors: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SyncReport:
    imports: tuple[str, ...]
    confirmations: tuple[str, ...]
    conflicts: tuple[str, ...]
    pending: tuple[str, ...]
    requested: tuple[str, ...]
    receipt_pending: tuple[str, ...]
    receipt_requested: tuple[str, ...]
    errors: tuple[str, ...]


def scan_inbox(
    repository: Repository | CurrentNoteStore,
    inbox: Path,
    local_device: str,
    received_dir: Path | None = None,
) -> ScanReport:
    if isinstance(repository, CurrentNoteStore):
        return _scan_current_inbox(
            repository, inbox, local_device, received_dir=received_dir
        )
    imported = []
    duplicates = []
    confirmed = []
    duplicate_receipts = []
    receipts_queued = []
    quarantined = []
    errors = []
    ledger = DeliveryLedger(repository.root)
    receipt_store = ReceiptStore(repository.root)
    # Download bundles often contain many already imported notes and receipts.
    # Snapshot known identities once instead of repeatedly re-reading every
    # revision and ledger entry for each member of each archive. Fresh imports
    # are added below so later entries in this same scan still see them.
    known_revision_ids = {revision.revision_id for revision in repository.revisions()}
    known_delivery_keys = {
        (entry.revision_id, entry.target_device) for entry in ledger.entries()
    }
    queued_receipt_keys = {
        (entry.revision_id, entry.target_device)
        for entry in receipt_store.entries()
    }
    reconciliation = receipt_store.reconcile_confirmations(
        repository,
        ledger,
        local_device=local_device,
    )
    confirmed.extend(reconciliation.confirmed)
    errors.extend(reconciliation.errors)
    inbox = Path(inbox)
    if not inbox.is_dir():
        return ScanReport(
            (),
            (),
            tuple(confirmed),
            (),
            (),
            (),
            (),
            tuple((*errors, f"inbox is not a directory: {inbox}")),
        )
    directories = [(inbox, False)]
    if received_dir is not None and Path(received_dir).resolve() != inbox.resolve():
        directories.append((Path(received_dir), True))
    candidates = []
    for directory, is_downloads in directories:
        if not directory.is_dir():
            errors.append(f"received directory is not a directory: {directory}")
            continue
        candidates.extend(_incoming_files(directory, downloads=is_downloads))

    incoming = []
    for path in candidates:
        try:
            if path.suffix.lower() == ".zip" and path.stat().st_size > MAX_ARCHIVE_BYTES:
                raise BundleError("bundle exceeds archive size limit")
            if path.suffix.lower() == ".json" and path.stat().st_size > MAX_PAYLOAD_BYTES:
                raise TransportBundleError("bundle payload exceeds size limit")
            data = path.read_bytes()
            if is_bundle_name(path.name):
                members = read_bundle(data, path.name)
            elif is_transport_bundle_name(path.name):
                members = read_transport_bundle(data, path.name)
            else:
                members = ((path.name, data),)
            incoming.extend((f"{path}!{name}", name, item) for name, item in members)
        except (OSError, BundleError, TransportBundleError) as error:
            errors.append(f"{path}: {error}")

    for source, source_name, data in incoming:
        if data.startswith(_RECEIPT_FORMAT_MARKER):
            try:
                receipt = ReceiptEnvelope.parse(data)
                # KDE Connect's global Downloads folder can contain genuine
                # acknowledgments for other, isolated repositories. They
                # cannot confirm anything in this library. Ignore only
                # canonical receipts for revisions not registered here.
                if (
                    received_dir is not None
                    and receipt.revision_id not in known_revision_ids
                    and (
                        receipt.revision_id, receipt.acknowledging_device
                    ) not in known_delivery_keys
                ):
                    continue
                outcome = receipt_store.accept(
                    data,
                    repository,
                    ledger,
                    local_device=local_device,
                    source_name=source_name,
                )
            except ReceiptError as error:
                errors.append(f"{source}: {error}")
                continue
            if outcome.kind == "confirmed":
                confirmed.append(outcome.revision_id)
            else:
                duplicate_receipts.append(outcome.receipt_id)
            continue
        if not data.startswith(_FORMAT_MARKER):
            continue
        outcome = repository.import_bytes(data, source_name)
        if outcome.kind == "purged":
            # Stale KDE Connect files may remain in Downloads. No import,
            # receipt or quarantine is permitted to resurrect their content.
            continue
        if outcome.kind == "imported" and outcome.revision_id:
            imported.append(outcome.revision_id)
        elif outcome.kind == "duplicate" and outcome.revision_id:
            duplicates.append(outcome.revision_id)
        else:
            quarantined.append(source_name)
            errors.append(f"{source}: {outcome.detail}")
            continue
        if outcome.revision_id:
            # import_bytes validated the envelope and checked the persistent
            # bytes on duplicates. Avoid re-reading all on-disk revisions to
            # obtain a revision object already available in this payload.
            revision = Revision.parse(data)
            known_revision_ids.add(revision.revision_id)
            if revision.origin_device != local_device:
                key = (revision.revision_id, revision.origin_device)
                already_queued = key in queued_receipt_keys
                receipt = receipt_store.queue(
                    revision,
                    local_device,
                    datetime.now(timezone.utc).replace(microsecond=0),
                )
                queued_receipt_keys.add(key)
                if not already_queued:
                    receipts_queued.append(receipt.receipt_id)
    graph = repository.graph()
    conflicts = tuple(
        sorted(
            str(note_id)
            for note_id in {revision.note_id for revision in repository.revisions()}
            if graph.status(note_id).conflicted
        )
    )
    return ScanReport(
        tuple(imported),
        tuple(duplicates),
        tuple(dict.fromkeys(confirmed)),
        tuple(duplicate_receipts),
        tuple(receipts_queued),
        tuple(quarantined),
        conflicts,
        tuple(errors),
    )


def _legacy_state(revision: Revision) -> StateEnvelope:
    if revision.deleted:
        return StateEnvelope.deletion(
            revision.note_id,
            revision.parents,
            revision.origin_device,
            revision.modified_utc,
        )
    title, body = _split_legacy_document(revision.body)
    return StateEnvelope.upsert(
        revision.note_id,
        revision.parents,
        revision.origin_device,
        revision.modified_utc,
        title,
        body,
    )


def _split_legacy_document(document: str) -> tuple[str, str]:
    offset = 0
    for line in document.splitlines(keepends=True):
        heading = line.rstrip("\r\n")
        ending = line[len(heading):]
        if heading.strip():
            remainder = document[offset + len(line):]
            if ending and remainder.startswith(ending):
                remainder = remainder[len(ending):]
            return heading.strip().lstrip("#").strip() or "Untitled", remainder
        offset += len(line)
    return "Untitled", document


def _current_candidates(
    inbox: Path, received_dir: Path | None
) -> tuple[list[tuple[str, str, str, bytes]], list[str]]:
    errors: list[str] = []
    inbox = Path(inbox)
    if not inbox.is_dir():
        return [], [f"inbox is not a directory: {inbox}"]
    directories = [(inbox, False)]
    if received_dir is not None and Path(received_dir).resolve() != inbox.resolve():
        directories.append((Path(received_dir), True))
    paths = []
    for directory, downloads in directories:
        if not directory.is_dir():
            errors.append(f"received directory is not a directory: {directory}")
            continue
        paths.extend(_incoming_files(directory, downloads=downloads))
    incoming: list[tuple[str, str, str, bytes]] = []
    for path in paths:
        try:
            if path.suffix.lower() == ".zip" and path.stat().st_size > MAX_ARCHIVE_BYTES:
                raise BundleError("bundle exceeds archive size limit")
            if path.suffix.lower() == ".json" and path.stat().st_size > MAX_PAYLOAD_BYTES:
                raise TransportBundleError("bundle payload exceeds size limit")
            data = path.read_bytes()
            if is_bundle_name(path.name):
                members = read_bundle(data, path.name)
            elif is_transport_bundle_name(path.name):
                members = read_transport_bundle(data, path.name)
            else:
                members = ((path.name, data),)
            metadata = path.stat()
            for name, item in members:
                source = f"{path}!{name}"
                occurrence = hashlib.sha256(
                    (
                        f"{path.resolve(strict=False)}\0{metadata.st_mtime_ns}\0"
                        f"{metadata.st_size}\0{name}"
                    ).encode("utf-8")
                ).hexdigest()
                incoming.append((source, occurrence, name, item))
        except (OSError, BundleError, TransportBundleError) as error:
            errors.append(f"{path}: {error}")
    return incoming, errors


def _scan_current_inbox(
    store: CurrentNoteStore,
    inbox: Path,
    local_device: str,
    *,
    received_dir: Path | None = None,
) -> ScanReport:
    imported: list[str] = []
    duplicates: list[str] = []
    confirmed: list[str] = []
    duplicate_acks: list[str] = []
    quarantined: list[str] = []
    incoming, errors = _current_candidates(inbox, received_dir)
    acknowledgments_before = {ack.ack_id for ack in store.pending_acks()}

    # Bundles sort acknowledgment kinds before state kinds. Durable state must
    # nevertheless be applied first so a carrier can never confirm before its
    # independent note mutations have been persisted.
    for source, occurrence, source_name, data in incoming:
        legacy = data.startswith(_FORMAT_MARKER)
        try:
            if legacy:
                state = _legacy_state(Revision.parse(data))
            else:
                state = StateEnvelope.from_bytes(data)
        except (EnvelopeError, StateEnvelopeError):
            continue
        try:
            if (
                store.was_processed("state", occurrence)
                or legacy and store.was_processed("legacy", state.change_id)
            ):
                continue
            if state.origin_device == local_device:
                raise StateEnvelopeError("state originated on this device")
            outcome = store.apply(state)
            if outcome.kind in ("applied", "deleted", "conflict"):
                imported.append(state.change_id)
            elif outcome.kind in ("duplicate", "rejected-deleted", "ignored-deletion"):
                duplicates.append(state.change_id)
            else:
                errors.append(f"{source}: {outcome.kind}")
                continue
            store.mark_processed("state", occurrence)
            continue
        except (OSError, RuntimeError, StateEnvelopeError, ValueError) as error:
            quarantined.append(source_name)
            errors.append(f"{source}: {error}")

    for source, occurrence, source_name, data in incoming:
        try:
            acknowledgment = StateAckEnvelope.from_bytes(data)
        except StateEnvelopeError:
            continue
        try:
            if store.was_processed("ack", occurrence):
                continue
            if store.acknowledge(acknowledgment):
                confirmed.append(acknowledgment.acknowledged_change_id)
            else:
                duplicate_acks.append(acknowledgment.ack_id)
            store.mark_processed("ack", occurrence)
        except (OSError, RuntimeError, StateEnvelopeError, ValueError) as error:
            quarantined.append(source_name)
            errors.append(f"{source}: {error}")

    acknowledgments_after = tuple(
        ack.ack_id
        for ack in store.pending_acks()
        if ack.ack_id not in acknowledgments_before
    )
    conflicts = tuple(sorted(str(conflict.note_id) for conflict in store.conflicts()))
    return ScanReport(
        tuple(dict.fromkeys(imported)),
        tuple(dict.fromkeys(duplicates)),
        tuple(dict.fromkeys(confirmed)),
        tuple(dict.fromkeys(duplicate_acks)),
        acknowledgments_after,
        tuple(dict.fromkeys(quarantined)),
        conflicts,
        tuple(dict.fromkeys(errors)),
    )


def sync_linux(
    repository: Repository | CurrentNoteStore,
    inbox: Path,
    adapter,
    retry_unconfirmed: bool = False,
    force_ids=(),
    force_receipt_ids=(),
    selected_note_ids: Collection[UUID] | None = None,
    received_dir: Path | None = None,
) -> SyncReport:
    if isinstance(repository, CurrentNoteStore):
        return _sync_current(
            repository,
            inbox,
            adapter,
            selected_note_ids=selected_note_ids,
            received_dir=received_dir,
        )
    local_device = repository.local_device or "linux"
    target_device = repository.target_device
    if target_device is None:
        raise ValueError("repository must configure a target device for sync")
    scan = scan_inbox(repository, inbox, local_device, received_dir=received_dir)
    ledger = DeliveryLedger(repository.root)
    forced_revision_ids = tuple(force_ids)
    all_eligible = ledger.eligible(
        target_device,
        retry_unconfirmed=retry_unconfirmed,
        force_ids=forced_revision_ids,
    )
    selected = (
        None
        if selected_note_ids is None or forced_revision_ids
        else frozenset(selected_note_ids)
    )
    if selected is not None and any(not isinstance(note_id, UUID) for note_id in selected):
        raise ValueError("selected note IDs must be UUID values")
    missing_revisions = tuple(
        revision_id
        for revision_id in all_eligible
        if repository.revision(revision_id) is None
    )
    eligible = tuple(
        revision_id
        for revision_id in all_eligible
        if (
            (revision := repository.revision(revision_id)) is not None
            and (selected is None or revision.note_id in selected)
        )
    )
    receipt_store = ReceiptStore(repository.root)
    eligible_receipts = receipt_store.eligible(
        target_device,
        retry_unconfirmed=retry_unconfirmed,
        force_ids=force_receipt_ids,
    )
    requested = []
    receipt_requested = []
    errors = [
        *scan.errors,
        *(
            f"outbox revision missing from history: {revision_id}"
            for revision_id in missing_revisions
        ),
    ]
    if (eligible or eligible_receipts) and not adapter.reachable():
        errors.append(f"KDE Connect device unavailable: {adapter.device_id}")
    elif eligible or eligible_receipts:
        items = []
        for revision_id in eligible:
            revision = repository.revision(revision_id)
            assert revision is not None
            path = (
                repository.history_dir
                / str(revision.note_id)
                / f"{revision.revision_id}.md"
            )
            items.append(BundleItem("revision", revision_id, path.read_bytes()))
        for receipt_id in eligible_receipts:
            try:
                path = receipt_store.outbox_path(receipt_id)
            except ReceiptError as error:
                errors.append(f"receipt {receipt_id}: {error}")
                continue
            items.append(BundleItem("receipt", receipt_id, path.read_bytes()))
        if items:
            try:
                path = write_bundle(
                    repository.root / "transport" / "outbox", items
                )
                result = adapter.request_transfer(path)
            except (OSError, ValueError, RuntimeError, TransportBundleError) as error:
                errors.append(f"transport bundle unavailable: {error}")
            else:
                if not result.accepted:
                    errors.append(f"transport bundle: {result.detail}")
                else:
                    observed = datetime.now(timezone.utc).replace(microsecond=0)
                    for item in items:
                        if item.kind == "revision":
                            ledger.record_requested(
                                item.identity,
                                target_device,
                                observed,
                                observer_device=local_device,
                            )
                            requested.append(item.identity)
                        else:
                            receipt_store.record_requested(
                                item.identity, target_device, observed
                            )
                            receipt_requested.append(item.identity)
    pending = tuple(
        entry.revision_id
        for entry in ledger.entries(target_device)
        if entry.state == DeliveryState.PENDING
    )
    receipt_pending = tuple(
        entry.receipt_id
        for entry in receipt_store.entries(target_device)
        if entry.state == DeliveryState.PENDING
    )
    return SyncReport(
        imports=scan.imported,
        confirmations=scan.confirmed,
        conflicts=scan.conflicts,
        pending=pending,
        requested=tuple(requested),
        receipt_pending=receipt_pending,
        receipt_requested=tuple(receipt_requested),
        errors=tuple(errors),
    )


def _sync_current(
    store: CurrentNoteStore,
    inbox: Path,
    adapter,
    *,
    selected_note_ids: Collection[UUID] | None,
    received_dir: Path | None,
) -> SyncReport:
    selected = None if selected_note_ids is None else frozenset(selected_note_ids)
    if selected is not None and any(not isinstance(note_id, UUID) for note_id in selected):
        raise ValueError("selected note IDs must be UUID values")
    scan = _scan_current_inbox(
        store, inbox, store.device_id, received_dir=received_dir
    )
    store.stage_live_for_sync(selected)
    states = tuple(
        state
        for state in store.pending_states()
        if (selected is None or state.note_id in selected)
        and store.conflict(state.note_id) is None
    )
    acknowledgments = store.pending_acks()
    items = tuple(
        [BundleItem("state-v2", state.change_id, state.to_bytes()) for state in states]
        + [BundleItem("ack-v2", ack.ack_id, ack.to_bytes()) for ack in acknowledgments]
    )
    requested: list[str] = []
    acknowledgment_requested: list[str] = []
    errors = list(scan.errors)
    if items and not adapter.reachable():
        errors.append(f"KDE Connect device unavailable: {adapter.device_id}")
    elif items:
        try:
            path = write_bundle(store.root / "transport" / "outbox", items)
            result = adapter.request_transfer(path)
        except (OSError, ValueError, RuntimeError, TransportBundleError) as error:
            errors.append(f"transport bundle unavailable: {error}")
        else:
            if not result.accepted:
                errors.append(f"transport bundle: {result.detail}")
            else:
                requested.extend(state.change_id for state in states)
                acknowledgment_requested.extend(ack.ack_id for ack in acknowledgments)
                store.mark_acks_requested(acknowledgments)
    conflicted = tuple(
        conflict.note_id
        for conflict in store.conflicts()
        if selected is None or conflict.note_id in selected
    )
    if conflicted:
        errors.append(
            "Conflict requires choice: "
            + ",".join(str(note_id) for note_id in sorted(conflicted))
        )
    return SyncReport(
        imports=scan.imported,
        confirmations=scan.confirmed,
        conflicts=scan.conflicts,
        pending=tuple(state.change_id for state in store.pending_states()),
        requested=tuple(requested),
        receipt_pending=tuple(ack.ack_id for ack in store.pending_acks()),
        receipt_requested=tuple(acknowledgment_requested),
        errors=tuple(dict.fromkeys(errors)),
    )


def sync_linux_confirmed(
    repository: Repository | CurrentNoteStore,
    inbox: Path,
    adapter,
    *,
    selected_note_ids: Collection[UUID] | None = None,
    received_dir: Path | None = None,
    timeout_seconds: float = 120.0,
    poll_interval_seconds: float = 0.5,
    monotonic=time.monotonic,
    sleeper=time.sleep,
) -> SyncReport:
    """Request a bounded transfer and wait for durable phone receipts.

    ``sync_linux`` remains the one-shot protocol primitive. This wrapper is
    intended for the interactive desktop action, where request acceptance is
    only an intermediate state and success requires the existing receipt path
    to confirm every revision requested by this invocation.
    """
    if timeout_seconds <= 0:
        raise ValueError("confirmation timeout must be positive")
    if poll_interval_seconds <= 0:
        raise ValueError("confirmation poll interval must be positive")

    if isinstance(repository, CurrentNoteStore):
        return _sync_current_confirmed(
            repository,
            inbox,
            adapter,
            selected_note_ids=selected_note_ids,
            received_dir=received_dir,
            timeout_seconds=timeout_seconds,
            poll_interval_seconds=poll_interval_seconds,
            monotonic=monotonic,
            sleeper=sleeper,
        )

    initial = sync_linux(
        repository,
        inbox,
        adapter,
        retry_unconfirmed=True,
        selected_note_ids=selected_note_ids,
        received_dir=received_dir,
    )
    imports = list(initial.imports)
    confirmations = list(initial.confirmations)
    conflicts = list(initial.conflicts)
    errors = list(initial.errors)
    target_device = repository.target_device
    assert target_device is not None
    ledger = DeliveryLedger(repository.root)
    receipt_store = ReceiptStore(repository.root)

    def unique(values):
        return tuple(dict.fromkeys(values))

    def report() -> SyncReport:
        pending = tuple(
            entry.revision_id
            for entry in ledger.entries(target_device)
            if entry.state == DeliveryState.PENDING
        )
        receipt_pending = tuple(
            entry.receipt_id
            for entry in receipt_store.entries(target_device)
            if entry.state == DeliveryState.PENDING
        )
        return SyncReport(
            imports=unique(imports),
            confirmations=unique(confirmations),
            conflicts=unique(conflicts),
            pending=pending,
            requested=initial.requested,
            receipt_pending=receipt_pending,
            receipt_requested=initial.receipt_requested,
            errors=unique(errors),
        )

    if errors:
        return report()

    requested = tuple(initial.requested)
    if not requested:
        selected = None if selected_note_ids is None else frozenset(selected_note_ids)
        blocked = []
        for entry in ledger.entries(target_device):
            if entry.state == DeliveryState.CONFIRMED:
                continue
            revision = repository.revision(entry.revision_id)
            if revision is not None and (
                selected is None or revision.note_id in selected
            ):
                blocked.append(entry)
        current_progress = bool(
            imports or confirmations or initial.receipt_requested
        )
        if blocked and not current_progress:
            errors.append(
                "Synchronization needs attention: bounded transfer request "
                f"limit reached for {len(blocked)} selected revision(s)"
            )
        return report()

    deadline = monotonic() + timeout_seconds
    requested_set = frozenset(requested)
    while True:
        scan = scan_inbox(
            repository,
            inbox,
            repository.local_device or "linux",
            received_dir=received_dir,
        )
        imports.extend(scan.imported)
        confirmations.extend(scan.confirmed)
        conflicts[:] = scan.conflicts
        errors.extend(scan.errors)

        confirmed_requested = tuple(
            revision_id
            for revision_id in requested
            if (
                (entry := ledger.entry(revision_id, target_device)) is not None
                and entry.state == DeliveryState.CONFIRMED
            )
        )
        confirmations.extend(confirmed_requested)
        missing = requested_set.difference(confirmed_requested)
        if not missing or errors:
            return report()
        if not adapter.reachable():
            errors.append(
                "KDE Connect device disconnected while waiting for phone "
                f"confirmation: {adapter.device_id}"
            )
            return report()

        now = monotonic()
        if now >= deadline:
            errors.append(
                "Timed out waiting for phone import confirmation: "
                f"{len(confirmed_requested)} of {len(requested)} requested "
                "revisions confirmed"
            )
            return report()
        sleeper(min(poll_interval_seconds, deadline - now))


def _sync_current_confirmed(
    store: CurrentNoteStore,
    inbox: Path,
    adapter,
    *,
    selected_note_ids: Collection[UUID] | None,
    received_dir: Path | None,
    timeout_seconds: float,
    poll_interval_seconds: float,
    monotonic,
    sleeper,
) -> SyncReport:
    initial = _sync_current(
        store,
        inbox,
        adapter,
        selected_note_ids=selected_note_ids,
        received_dir=received_dir,
    )
    imports = list(initial.imports)
    confirmations = list(initial.confirmations)
    conflicts = list(initial.conflicts)
    errors = list(initial.errors)
    requested = tuple(initial.requested)

    def report() -> SyncReport:
        return SyncReport(
            imports=tuple(dict.fromkeys(imports)),
            confirmations=tuple(dict.fromkeys(confirmations)),
            conflicts=tuple(dict.fromkeys(conflicts)),
            pending=tuple(state.change_id for state in store.pending_states()),
            requested=requested,
            receipt_pending=tuple(ack.ack_id for ack in store.pending_acks()),
            receipt_requested=initial.receipt_requested,
            errors=tuple(dict.fromkeys(errors)),
        )

    if not requested:
        return report()
    deadline = monotonic() + timeout_seconds
    requested_set = frozenset(requested)
    while True:
        scan = _scan_current_inbox(
            store, inbox, store.device_id, received_dir=received_dir
        )
        imports.extend(scan.imported)
        confirmations.extend(scan.confirmed)
        conflicts[:] = scan.conflicts
        errors.extend(scan.errors)
        if requested_set.issubset(confirmations):
            return report()
        if not adapter.reachable():
            errors.append(
                "KDE Connect device disconnected while waiting for peer confirmation: "
                f"{adapter.device_id}"
            )
            return report()
        now = monotonic()
        if now >= deadline:
            count = len(requested_set.intersection(confirmations))
            errors.append(
                "Timed out waiting for peer import confirmation: "
                f"{count} of {len(requested)} requested changes confirmed"
            )
            return report()
        sleeper(min(poll_interval_seconds, deadline - now))
