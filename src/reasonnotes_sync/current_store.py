"""Durable current-state storage for simplified synchronization v2."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import os
from pathlib import Path
import re
from threading import RLock
import tempfile
from uuid import UUID

from .state_envelope import StateAckEnvelope, StateEnvelope, StateEnvelopeError


_DEVICE = re.compile(r"[a-z0-9][a-z0-9._-]{0,63}")
_HASH = re.compile(r"[0-9a-f]{64}")


@dataclass(frozen=True, slots=True)
class ApplyOutcome:
    kind: str
    change_id: str


@dataclass(frozen=True, slots=True)
class Conflict:
    note_id: UUID
    candidates: tuple[StateEnvelope, ...]


class CurrentNoteStore:
    """One current record per note plus transient conflicts and pending work."""

    def __init__(self, root: Path, device_id: str):
        self.root = Path(root)
        self.device_id = device_id
        self.current_dir = self.root / "current"
        self.conflicts_dir = self.root / "conflicts"
        self.deleted_dir = self.root / "deleted"
        self.pending_dir = self.root / "pending"
        self.outgoing_acks_dir = self.root / "outgoing-acks"
        self.processed_exchange_dir = self.root / "processed-exchange"
        self._lock = RLock()

    @classmethod
    def open(cls, root: Path, device_id: str = "linux") -> "CurrentNoteStore":
        if _DEVICE.fullmatch(device_id) is None:
            raise ValueError("invalid device ID")
        store = cls(Path(root), device_id)
        store._ensure_layout()
        store._recover_interrupted_pending()
        store._finish_durable_deletions()
        store._validate_all()
        return store

    def list(self) -> tuple[StateEnvelope, ...]:
        with self._lock:
            return tuple(sorted(self._read_states(self.current_dir), key=lambda state: str(state.note_id)))

    def get(self, note_id: UUID) -> StateEnvelope | None:
        with self._lock:
            path = self._state_path(self.current_dir, note_id)
            return self._read_state(path) if path.is_file() else None

    def head_ids(self, note_id: UUID) -> tuple[str, ...]:
        with self._lock:
            conflict = self.conflict(note_id)
            if conflict is not None:
                return tuple(sorted(candidate.change_id for candidate in conflict.candidates))
            state = self.get(note_id)
            return () if state is None else (state.change_id,)

    def save_local(
        self, note_id: UUID, title: str, body: str, modified_utc: datetime
    ) -> StateEnvelope:
        with self._lock:
            if self._fence_path(note_id).is_file():
                raise RuntimeError("deleted note cannot be edited")
            if self.conflict(note_id) is not None:
                raise RuntimeError("conflict must be resolved first")
            existing = self.get(note_id)
            parents = self._local_parents(note_id, existing)
            state = StateEnvelope.upsert(
                note_id, parents, self.device_id, modified_utc, title, body
            )
            self._commit_local(state)
            return state

    def apply(self, incoming: StateEnvelope) -> ApplyOutcome:
        with self._lock:
            fence = self._read_optional(self._fence_path(incoming.note_id))
            if fence is not None:
                if incoming.operation == "delete":
                    self._queue_ack(incoming)
                    return ApplyOutcome("duplicate", incoming.change_id)
                return ApplyOutcome("rejected-deleted", incoming.change_id)

            if incoming.operation == "delete":
                self._persist_deletion(incoming, outgoing=False)
                self._queue_ack(incoming)
                return ApplyOutcome("deleted", incoming.change_id)

            local = self.get(incoming.note_id)
            if local is None:
                self._atomic_write(self._state_path(self.current_dir, incoming.note_id), incoming.to_bytes())
                self._queue_ack(incoming)
                return ApplyOutcome("applied", incoming.change_id)
            if local.change_id == incoming.change_id:
                self._queue_ack(incoming)
                return ApplyOutcome("duplicate", incoming.change_id)
            if local.change_id in incoming.parent_change_ids:
                self._atomic_write(self._state_path(self.current_dir, incoming.note_id), incoming.to_bytes())
                pending = self._state_path(self.pending_dir, incoming.note_id)
                if pending.is_file() and self._read_state(pending).change_id == local.change_id:
                    self._remove(pending)
                self._clear_conflict(incoming.note_id)
                self._queue_ack(incoming)
                return ApplyOutcome("applied", incoming.change_id)
            if local.operation == "upsert" and local.parent_change_ids == incoming.parent_change_ids:
                self._write_conflict(local, incoming)
                self._queue_ack(incoming)
                return ApplyOutcome("conflict", incoming.change_id)
            self._write_conflict(local, incoming)
            self._queue_ack(incoming)
            return ApplyOutcome("conflict", incoming.change_id)

    def resolve(
        self, note_id: UUID, selected_change_id: str, modified_utc: datetime
    ) -> StateEnvelope:
        with self._lock:
            conflict = self.conflict(note_id)
            if conflict is None:
                raise RuntimeError("note is not conflicted")
            selected = next(
                (candidate for candidate in conflict.candidates if candidate.change_id == selected_change_id),
                None,
            )
            if selected is None:
                raise ValueError("unknown conflict candidate")
            resolution = StateEnvelope.upsert(
                note_id,
                tuple(sorted(candidate.change_id for candidate in conflict.candidates)),
                self.device_id,
                modified_utc,
                selected.title,
                selected.body,
            )
            self._commit_local(resolution)
            self._clear_conflict(note_id)
            return resolution

    def delete_local(self, note_id: UUID, modified_utc: datetime) -> StateEnvelope:
        with self._lock:
            conflict = self.conflict(note_id)
            if conflict is not None:
                parents = tuple(sorted(candidate.change_id for candidate in conflict.candidates))
            else:
                live = self.get(note_id)
                parents = self._local_parents(note_id, live)
            deletion = StateEnvelope.deletion(
                note_id, parents, self.device_id, modified_utc
            )
            self._persist_deletion(deletion, outgoing=True)
            return deletion

    def _local_parents(
        self, note_id: UUID, current: StateEnvelope | None
    ) -> tuple[str, ...]:
        pending = self._read_optional(self._state_path(self.pending_dir, note_id))
        if pending is not None:
            return pending.parent_change_ids
        return () if current is None else (current.change_id,)

    def pending_states(self) -> tuple[StateEnvelope, ...]:
        with self._lock:
            return tuple(sorted(self._read_states(self.pending_dir), key=lambda state: str(state.note_id)))

    def pending_acks(self) -> tuple[StateAckEnvelope, ...]:
        with self._lock:
            result = []
            for path in sorted(self.outgoing_acks_dir.glob("*.json")):
                if path.is_symlink() or not path.is_file():
                    raise RuntimeError(f"invalid acknowledgment path: {path}")
                result.append(StateAckEnvelope.from_bytes(path.read_bytes()))
            return tuple(result)

    def acknowledge(self, acknowledgment: str | StateAckEnvelope) -> bool:
        with self._lock:
            if isinstance(acknowledgment, StateAckEnvelope):
                if acknowledgment.destination_device != self.device_id:
                    raise ValueError("acknowledgment has wrong destination")
                for state in self.pending_states():
                    if state.change_id != acknowledgment.acknowledged_change_id:
                        continue
                    if state.note_id != acknowledgment.note_id:
                        raise ValueError("acknowledgment note does not match change")
                    self._remove(self._state_path(self.pending_dir, state.note_id))
                    return True
                return False
            if _HASH.fullmatch(acknowledgment) is None:
                raise ValueError("acknowledged change ID must be a lowercase SHA-256 value")
            for state in self.pending_states():
                if state.change_id == acknowledgment:
                    self._remove(self._state_path(self.pending_dir, state.note_id))
                    return True
            return False

    def mark_acks_requested(self, acknowledgments) -> None:
        with self._lock:
            for acknowledgment in acknowledgments:
                self._remove(self._ack_path(acknowledgment.acknowledged_change_id))

    def conflict(self, note_id: UUID) -> Conflict | None:
        with self._lock:
            directory = self.conflicts_dir / str(note_id)
            if not directory.is_dir() or directory.is_symlink():
                return None
            candidates = tuple(sorted(self._read_states(directory), key=lambda state: state.change_id))
            return None if not candidates else Conflict(note_id, candidates)

    def conflicts(self) -> tuple[Conflict, ...]:
        with self._lock:
            result = []
            for directory in sorted(self.conflicts_dir.iterdir()):
                if directory.is_symlink() or not directory.is_dir():
                    raise RuntimeError(f"invalid conflict path: {directory}")
                conflict = self.conflict(UUID(directory.name))
                if conflict is not None:
                    result.append(conflict)
            return tuple(result)

    def is_deleted(self, note_id: UUID) -> bool:
        return self._fence_path(note_id).is_file()

    def was_processed(self, kind: str, identity: str) -> bool:
        return self._processed_path(kind, identity).is_file()

    def mark_processed(self, kind: str, identity: str) -> None:
        path = self._processed_path(kind, identity)
        if path.is_file():
            return
        self._atomic_write(path, b"")

    def _write_migrated_current(self, state: StateEnvelope) -> None:
        if state.operation != "upsert":
            raise ValueError("migrated current state must be live")
        self._atomic_write(self._state_path(self.current_dir, state.note_id), state.to_bytes())
        self._atomic_write(self._state_path(self.pending_dir, state.note_id), state.to_bytes())

    def _write_migrated_conflict(self, candidates: tuple[StateEnvelope, StateEnvelope]) -> None:
        if (
            len(candidates) != 2
            or candidates[0].note_id != candidates[1].note_id
            or any(candidate.operation != "upsert" for candidate in candidates)
        ):
            raise ValueError("migration conflict must contain two live candidates")
        self._write_conflict(*candidates)

    def _write_migrated_deletion(self, deletion: StateEnvelope) -> None:
        if deletion.operation != "delete":
            raise ValueError("migrated fence must be a deletion")
        self._persist_deletion(deletion, outgoing=True)

    def _commit_local(self, state: StateEnvelope) -> None:
        staged = self._pending_temporary(state.note_id)
        self._atomic_write(staged, state.to_bytes())
        self._atomic_write(self._state_path(self.current_dir, state.note_id), state.to_bytes())
        self._move(staged, self._state_path(self.pending_dir, state.note_id))

    def _persist_deletion(self, deletion: StateEnvelope, *, outgoing: bool) -> None:
        staged = self._pending_temporary(deletion.note_id)
        if outgoing:
            self._atomic_write(staged, deletion.to_bytes())
        self._atomic_write(self._fence_path(deletion.note_id), deletion.to_bytes())
        self._erase_live_content(deletion.note_id)
        if outgoing:
            self._move(staged, self._state_path(self.pending_dir, deletion.note_id))
        else:
            self._remove(self._state_path(self.pending_dir, deletion.note_id))

    def _finish_durable_deletions(self) -> None:
        for fence in self._read_states(self.deleted_dir):
            self._erase_live_content(fence.note_id)

    def _erase_live_content(self, note_id: UUID) -> None:
        self._remove(self._state_path(self.current_dir, note_id))
        self._clear_conflict(note_id)
        pending = self._state_path(self.pending_dir, note_id)
        if pending.is_file() and self._read_state(pending).operation != "delete":
            self._remove(pending)

    def _write_conflict(self, left: StateEnvelope, right: StateEnvelope) -> None:
        if left.note_id != right.note_id:
            raise ValueError("conflict candidates must name one note")
        directory = self.conflicts_dir / str(left.note_id)
        directory.mkdir(parents=True, exist_ok=True)
        self._fsync_directory(directory.parent)
        self._atomic_write(directory / f"{left.change_id}.json", left.to_bytes())
        self._atomic_write(directory / f"{right.change_id}.json", right.to_bytes())

    def _clear_conflict(self, note_id: UUID) -> None:
        directory = self.conflicts_dir / str(note_id)
        if not directory.exists():
            return
        if directory.is_symlink() or not directory.is_dir():
            raise RuntimeError("invalid conflict directory")
        for path in directory.iterdir():
            if path.is_symlink() or not path.is_file():
                raise RuntimeError("invalid conflict candidate path")
            path.unlink()
        directory.rmdir()
        self._fsync_directory(self.conflicts_dir)

    def _queue_ack(self, incoming: StateEnvelope) -> None:
        path = self._ack_path(incoming.change_id)
        if path.is_file():
            return
        now = datetime.now(timezone.utc).replace(microsecond=0)
        acknowledgment = StateAckEnvelope.create(
            incoming.note_id,
            incoming.change_id,
            self.device_id,
            incoming.origin_device,
            now,
        )
        self._atomic_write(path, acknowledgment.to_bytes())

    def _recover_interrupted_pending(self) -> None:
        for path in sorted(self.pending_dir.glob("*.pending.tmp")):
            state = self._read_state(path)
            current = self.get(state.note_id)
            if current == state:
                self._move(path, self._state_path(self.pending_dir, state.note_id))
            else:
                self._remove(path)

    def _validate_all(self) -> None:
        self.list()
        self.pending_states()
        self.pending_acks()
        for fence in self._read_states(self.deleted_dir):
            if fence.operation != "delete":
                raise RuntimeError("deletion fence is not a deletion")
        for conflict in self.conflicts():
            if len(conflict.candidates) != 2:
                raise RuntimeError("conflict must contain exactly two candidates")
            if any(candidate.note_id != conflict.note_id for candidate in conflict.candidates):
                raise RuntimeError("conflict candidate note does not match directory")

    def _read_states(self, directory: Path) -> tuple[StateEnvelope, ...]:
        result = []
        for path in sorted(directory.glob("*.json")):
            if path.is_symlink() or not path.is_file():
                raise RuntimeError(f"invalid state path: {path}")
            state = self._read_state(path)
            if directory in (self.current_dir, self.pending_dir, self.deleted_dir):
                if path.stem != str(state.note_id):
                    raise RuntimeError("state filename disagrees with note ID")
            elif path.stem != state.change_id:
                raise RuntimeError("conflict filename disagrees with change ID")
            result.append(state)
        return tuple(result)

    @staticmethod
    def _read_state(path: Path) -> StateEnvelope:
        try:
            return StateEnvelope.from_bytes(path.read_bytes())
        except (OSError, StateEnvelopeError) as error:
            raise RuntimeError(f"cannot read state: {path}") from error

    def _read_optional(self, path: Path) -> StateEnvelope | None:
        return self._read_state(path) if path.is_file() else None

    def _ensure_layout(self) -> None:
        if self.root.is_symlink():
            raise RuntimeError("current store root must not be a symbolic link")
        self.root.mkdir(parents=True, exist_ok=True)
        for directory in (
            self.current_dir,
            self.conflicts_dir,
            self.deleted_dir,
            self.pending_dir,
            self.outgoing_acks_dir,
            self.processed_exchange_dir,
        ):
            if directory.is_symlink():
                raise RuntimeError("current store directory must not be a symbolic link")
            directory.mkdir(exist_ok=True)

    @staticmethod
    def _fsync_directory(directory: Path) -> None:
        descriptor = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)

    def _atomic_write(self, path: Path, data: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
        )
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
            self._fsync_directory(path.parent)
        finally:
            temporary.unlink(missing_ok=True)

    def _move(self, source: Path, target: Path) -> None:
        os.replace(source, target)
        self._fsync_directory(target.parent)

    def _remove(self, path: Path) -> None:
        try:
            path.unlink()
        except FileNotFoundError:
            return
        self._fsync_directory(path.parent)

    @staticmethod
    def _state_path(directory: Path, note_id: UUID) -> Path:
        return directory / f"{note_id}.json"

    def _fence_path(self, note_id: UUID) -> Path:
        return self._state_path(self.deleted_dir, note_id)

    def _pending_temporary(self, note_id: UUID) -> Path:
        return self.pending_dir / f"{note_id}.pending.tmp"

    def _ack_path(self, change_id: str) -> Path:
        return self.outgoing_acks_dir / f"{change_id}.json"

    def _processed_path(self, kind: str, identity: str) -> Path:
        if kind not in ("ack", "legacy", "state") or _HASH.fullmatch(identity) is None:
            raise ValueError("invalid processed exchange identity")
        return self.processed_exchange_dir / f"{kind}-{identity}"
