"""Canonical current-state and acknowledgment records for sync v2."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import re
from uuid import UUID


HASH = re.compile(r"[0-9a-f]{64}")
DEVICE = re.compile(r"[a-z0-9][a-z0-9._-]{0,63}")
STATE_FORMAT = "reasonnotes-state-v2"
ACK_FORMAT = "reasonnotes-ack-v2"


class StateEnvelopeError(ValueError):
    pass


def _time(value: datetime) -> str:
    if not isinstance(value, datetime) or value.utcoffset() != timezone.utc.utcoffset(value) or value.microsecond:
        raise StateEnvelopeError("time must use whole UTC seconds")
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_time(value: object) -> datetime:
    if not isinstance(value, str):
        raise StateEnvelopeError("time must be a string")
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError as error:
        raise StateEnvelopeError("invalid UTC timestamp") from error
    if _time(parsed) != value:
        raise StateEnvelopeError("timestamp is not canonical")
    return parsed


def _hash(value: str, label: str) -> str:
    if not isinstance(value, str) or HASH.fullmatch(value) is None:
        raise StateEnvelopeError(f"{label} must be a lowercase SHA-256 value")
    return value


def _device(value: str) -> str:
    if not isinstance(value, str) or DEVICE.fullmatch(value) is None:
        raise StateEnvelopeError("invalid device ID")
    return value


def _parents(values) -> tuple[str, ...]:
    result = tuple(sorted(_hash(value, "parent change ID") for value in values))
    if len(result) > 2 or len(set(result)) != len(result):
        raise StateEnvelopeError("state must have zero to two unique parents")
    return result


def _bytes(value: dict) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")


def _load(data: bytes) -> dict:
    if not isinstance(data, bytes):
        raise StateEnvelopeError("envelope must be bytes")
    try:
        value = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise StateEnvelopeError("envelope is not valid JSON") from error
    if type(value) is not dict:
        raise StateEnvelopeError("envelope must be an object")
    return value


@dataclass(frozen=True, slots=True)
class StateEnvelope:
    note_id: UUID
    operation: str
    change_id: str
    parent_change_ids: tuple[str, ...]
    origin_device: str
    modified_utc: datetime
    title: str | None = None
    body: str | None = None

    @classmethod
    def upsert(cls, note_id, parents, origin_device, modified_utc, title, body):
        return cls._create(note_id, "upsert", parents, origin_device, modified_utc, title, body)

    @classmethod
    def deletion(cls, note_id, parents, origin_device, modified_utc):
        return cls._create(note_id, "delete", parents, origin_device, modified_utc, None, None)

    @classmethod
    def _create(cls, note_id, operation, parents, origin_device, modified_utc, title, body):
        if not isinstance(note_id, UUID):
            raise StateEnvelopeError("note ID must be a UUID")
        canonical_parents = _parents(parents)
        origin_device = _device(origin_device)
        if operation == "upsert" and (not isinstance(title, str) or not isinstance(body, str)):
            raise StateEnvelopeError("upsert content must be strings")
        unsigned = cls._value(note_id, operation, canonical_parents, origin_device,
                              modified_utc, title, body, None)
        change_id = hashlib.sha256(_bytes(unsigned)).hexdigest()
        return cls(note_id, operation, change_id, canonical_parents, origin_device,
                   modified_utc, title, body)

    @staticmethod
    def _value(note_id, operation, parents, origin, modified, title, body, change_id):
        value = {
            "format": STATE_FORMAT,
            "modified_utc": _time(modified),
            "note_id": str(note_id),
            "operation": operation,
            "origin_device": origin,
            "parent_change_ids": list(parents),
        }
        if operation == "upsert":
            value["body"] = body
            value["title"] = title
        if change_id is not None:
            value["change_id"] = change_id
        return value

    def to_bytes(self) -> bytes:
        return _bytes(self._value(self.note_id, self.operation, self.parent_change_ids,
                                  self.origin_device, self.modified_utc, self.title,
                                  self.body, self.change_id))

    @classmethod
    def from_bytes(cls, data: bytes):
        value = _load(data)
        operation = value.get("operation")
        expected = ({"body", "change_id", "format", "modified_utc", "note_id", "operation",
                     "origin_device", "parent_change_ids", "title"} if operation == "upsert" else
                    {"change_id", "format", "modified_utc", "note_id", "operation",
                     "origin_device", "parent_change_ids"})
        if set(value) != expected or value.get("format") != STATE_FORMAT:
            raise StateEnvelopeError("state schema is not canonical")
        try:
            note_id = UUID(value["note_id"])
        except (ValueError, TypeError) as error:
            raise StateEnvelopeError("invalid note UUID") from error
        if str(note_id) != value["note_id"] or type(value["parent_change_ids"]) is not list:
            raise StateEnvelopeError("state identity is not canonical")
        parents = _parents(value["parent_change_ids"])
        change_id = _hash(value["change_id"], "change ID")
        origin = _device(value["origin_device"])
        modified = _parse_time(value["modified_utc"])
        title = value.get("title")
        body = value.get("body")
        if operation not in ("upsert", "delete") or (operation == "upsert" and
                (not isinstance(title, str) or not isinstance(body, str))):
            raise StateEnvelopeError("invalid state operation or content")
        expected_id = hashlib.sha256(_bytes(cls._value(
            note_id, operation, parents, origin, modified, title, body, None))).hexdigest()
        result = cls(note_id, operation, change_id, parents, origin, modified, title, body)
        if change_id != expected_id or result.to_bytes() != data:
            raise StateEnvelopeError("state hash or canonical bytes mismatch")
        return result


@dataclass(frozen=True, slots=True)
class StateAckEnvelope:
    note_id: UUID
    acknowledged_change_id: str
    ack_id: str
    acknowledging_device: str
    destination_device: str
    imported_utc: datetime

    @staticmethod
    def _value(note_id, change_id, acknowledging, destination, imported, ack_id):
        value = {
            "acknowledged_change_id": change_id,
            "acknowledging_device": acknowledging,
            "destination_device": destination,
            "format": ACK_FORMAT,
            "imported_utc": _time(imported),
            "note_id": str(note_id),
        }
        if ack_id is not None:
            value["ack_id"] = ack_id
        return value

    @classmethod
    def create(cls, note_id, change_id, acknowledging_device, destination_device, imported_utc):
        change_id = _hash(change_id, "acknowledged change ID")
        acknowledging_device = _device(acknowledging_device)
        destination_device = _device(destination_device)
        if acknowledging_device == destination_device:
            raise StateEnvelopeError("acknowledgment devices must differ")
        unsigned = cls._value(note_id, change_id, acknowledging_device,
                              destination_device, imported_utc, None)
        return cls(note_id, change_id, hashlib.sha256(_bytes(unsigned)).hexdigest(),
                   acknowledging_device, destination_device, imported_utc)

    def to_bytes(self):
        return _bytes(self._value(self.note_id, self.acknowledged_change_id,
                                  self.acknowledging_device, self.destination_device,
                                  self.imported_utc, self.ack_id))

    @classmethod
    def from_bytes(cls, data):
        value = _load(data)
        if set(value) != {"ack_id", "acknowledged_change_id", "acknowledging_device",
                          "destination_device", "format", "imported_utc", "note_id"} or value.get("format") != ACK_FORMAT:
            raise StateEnvelopeError("ack schema is not canonical")
        try:
            note_id = UUID(value["note_id"])
        except (ValueError, TypeError) as error:
            raise StateEnvelopeError("invalid ack note UUID") from error
        result = cls.create(note_id, value["acknowledged_change_id"],
                            value["acknowledging_device"], value["destination_device"],
                            _parse_time(value["imported_utc"]))
        if result.ack_id != _hash(value["ack_id"], "acknowledgment ID") or result.to_bytes() != data:
            raise StateEnvelopeError("ack hash or canonical bytes mismatch")
        return result
