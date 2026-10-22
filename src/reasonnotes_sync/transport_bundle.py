"""Canonical single-payload transport for unchanged ReasonNotes envelopes."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

from .envelope import EnvelopeError, Revision
from .receipt import ReceiptEnvelope, ReceiptError


FORMAT = "reasonnotes-transport-bundle"
VERSION = 1
NAME = re.compile(
    r"reasonnotes-bundle-v1-([0-9a-f]{64})(?: \(([1-9][0-9]*)\))?\.json"
)
IDENTITY = re.compile(r"[0-9a-f]{64}")
MAX_ITEMS = 256
MAX_ENVELOPE_BYTES = 16 * 1024 * 1024
MAX_TOTAL_ENVELOPE_BYTES = 64 * 1024 * 1024
MAX_PAYLOAD_BYTES = 64 * 1024 * 1024


class TransportBundleError(ValueError):
    """A transport payload is not a valid canonical ReasonNotes bundle."""


@dataclass(frozen=True, slots=True)
class BundleItem:
    kind: str
    identity: str
    envelope: bytes


def is_transport_bundle_name(name: str) -> bool:
    return NAME.fullmatch(name) is not None


def _validated_item(item: BundleItem) -> tuple[BundleItem, str]:
    if item.kind not in ("receipt", "revision"):
        raise TransportBundleError("bundle item kind is unsupported")
    if IDENTITY.fullmatch(item.identity) is None:
        raise TransportBundleError("bundle item identity is invalid")
    if not isinstance(item.envelope, bytes):
        raise TransportBundleError("bundle envelope must be bytes")
    if len(item.envelope) > MAX_ENVELOPE_BYTES:
        raise TransportBundleError("bundle envelope exceeds size limit")
    try:
        text = item.envelope.decode("utf-8", errors="strict")
        if item.kind == "revision":
            parsed_identity = Revision.parse(item.envelope).revision_id
        else:
            parsed_identity = ReceiptEnvelope.parse(item.envelope).receipt_id
    except UnicodeDecodeError as error:
        raise TransportBundleError("bundle envelope is not UTF-8") from error
    except (EnvelopeError, ReceiptError) as error:
        raise TransportBundleError("bundle envelope is invalid") from error
    if parsed_identity != item.identity:
        raise TransportBundleError("bundle item identity differs from envelope")
    return item, text


def _canonical_payload(items: tuple[tuple[BundleItem, str], ...]) -> bytes:
    value = {
        "format": FORMAT,
        "items": [
            {
                "envelope": text,
                "id": item.identity,
                "kind": item.kind,
            }
            for item, text in items
        ],
        "version": VERSION,
    }
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def build_bundle(items) -> tuple[str, bytes]:
    source = tuple(items)
    if not 1 <= len(source) <= MAX_ITEMS:
        raise TransportBundleError("bundle items must contain 1 to 256 envelopes")
    validated = tuple(_validated_item(item) for item in source)
    keys = tuple((item.kind, item.identity) for item, _text in validated)
    if len(set(keys)) != len(keys):
        raise TransportBundleError("duplicate bundle item identity")
    total = sum(len(item.envelope) for item, _text in validated)
    if total > MAX_TOTAL_ENVELOPE_BYTES:
        raise TransportBundleError("bundle envelopes exceed total size limit")
    ordered = tuple(sorted(validated, key=lambda pair: (pair[0].kind, pair[0].identity)))
    payload = _canonical_payload(ordered)
    if len(payload) > MAX_PAYLOAD_BYTES:
        raise TransportBundleError("bundle payload exceeds size limit")
    digest = hashlib.sha256(payload).hexdigest()
    return f"reasonnotes-bundle-v1-{digest}.json", payload


def write_bundle(directory: Path, items) -> Path:
    name, payload = build_bundle(items)
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    if path.is_file() and path.read_bytes() == payload:
        return path
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{name}.", suffix=".tmp", dir=directory
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        return path
    finally:
        if temporary.exists():
            temporary.unlink()


def read_transport_bundle(data: bytes, name: str) -> tuple[tuple[str, bytes], ...]:
    match = NAME.fullmatch(name)
    if match is None:
        raise TransportBundleError("not a canonical ReasonNotes bundle filename")
    if len(data) > MAX_PAYLOAD_BYTES:
        raise TransportBundleError("bundle payload exceeds size limit")
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise TransportBundleError("bundle payload is not UTF-8") from error
    if hashlib.sha256(data).hexdigest() != match.group(1):
        raise TransportBundleError("bundle payload hash differs from filename")
    try:
        value = json.loads(text)
    except (json.JSONDecodeError, RecursionError) as error:
        raise TransportBundleError("bundle payload is not valid JSON") from error
    if type(value) is not dict or list(value) != ["format", "items", "version"]:
        raise TransportBundleError("bundle schema is not canonical")
    if value["format"] != FORMAT or type(value["version"]) is not int or value["version"] != VERSION:
        raise TransportBundleError("bundle format or version is unsupported")
    values = value["items"]
    if type(values) is not list or not 1 <= len(values) <= MAX_ITEMS:
        raise TransportBundleError("bundle items must contain 1 to 256 envelopes")

    validated = []
    total = 0
    for raw in values:
        if type(raw) is not dict or list(raw) != ["envelope", "id", "kind"]:
            raise TransportBundleError("bundle item schema is not canonical")
        if not all(type(raw[key]) is str for key in ("envelope", "id", "kind")):
            raise TransportBundleError("bundle item values must be strings")
        envelope = raw["envelope"].encode("utf-8")
        total += len(envelope)
        item = BundleItem(raw["kind"], raw["id"], envelope)
        validated.append(_validated_item(item))
    if total > MAX_TOTAL_ENVELOPE_BYTES:
        raise TransportBundleError("bundle envelopes exceed total size limit")
    keys = tuple((item.kind, item.identity) for item, _text in validated)
    if len(set(keys)) != len(keys):
        raise TransportBundleError("duplicate bundle item identity")
    ordered = tuple(sorted(validated, key=lambda pair: (pair[0].kind, pair[0].identity)))
    if tuple(validated) != ordered or _canonical_payload(ordered) != data:
        raise TransportBundleError("bundle payload is not canonical")
    return tuple(
        (
            f"{item.identity}.receipt.md" if item.kind == "receipt" else f"{item.identity}.md",
            item.envelope,
        )
        for item, _text in ordered
    )
