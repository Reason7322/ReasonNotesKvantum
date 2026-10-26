"""Thin note application service over current-state or legacy storage."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal
import unicodedata
from uuid import UUID, uuid4

from reasonnotes_sync.conflicts import (
    ConflictChangedError,
    ConflictCandidate as LegacyConflictCandidate,
    list_conflict,
    resolve_conflict,
)
from reasonnotes_sync.current_store import CurrentNoteStore
from reasonnotes_sync.envelope import Revision
from reasonnotes_sync.repository import ConflictRequired, Repository
from reasonnotes_sync.state_envelope import StateEnvelope

from .note_document import split_note


class NoteNotFoundError(KeyError):
    """Raised when a note has no live working value."""


class StaleConflictChoice(RuntimeError):
    """Raised when a resolution was not based on the current conflict heads."""


@dataclass(frozen=True, slots=True)
class NoteSummary:
    note_id: UUID
    title: str
    preview: str
    conflicted: bool
    modified_utc: datetime


@dataclass(frozen=True, slots=True)
class ConflictCandidate:
    revision_id: str
    origin_device: str
    deleted: bool
    preview: str
    body: str


def _search_key(value: str) -> str:
    return unicodedata.normalize("NFKC", value).casefold()


def _title(body: str) -> str:
    for line in body.splitlines():
        if not line.strip():
            continue
        title = line.strip().lstrip("#").strip()
        return title or "Untitled"
    return "Untitled"


def _preview(body: str) -> str:
    return body.strip()[:240]


def _document(title: str, body: str) -> str:
    return f"# {title}\n\n{body}"


class NoteService:
    """Application operations over a :class:`Repository`.

    The repository remains the only durable state. Conflict snapshots are
    deliberately process-local safety tokens: after a restart or a changed
    head set, the caller must inspect the conflict again before resolving it.
    """

    def __init__(
        self,
        repository: Repository | CurrentNoteStore,
        *,
        origin_device: str = "linux",
        clock: Callable[[], datetime] | None = None,
        note_id_factory: Callable[[], UUID] = uuid4,
    ):
        self.repository = repository
        self.origin_device = origin_device
        self._clock = clock or (
            lambda: datetime.now(timezone.utc).replace(microsecond=0)
        )
        self._note_id_factory = note_id_factory
        self._conflict_snapshots: dict[UUID, tuple[str, ...]] = {}
        self._edit_bases: dict[UUID, str] = {}

    @property
    def current_state(self) -> bool:
        return isinstance(self.repository, CurrentNoteStore)

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is not None and value.utcoffset() is not None:
            value = value.astimezone(timezone.utc)
        return value.replace(microsecond=0)

    def _working_body(self, note_id: UUID) -> str | None:
        if self.current_state:
            state = self.repository.get(note_id)
            if state is not None:
                return _document(state.title or "Untitled", state.body or "")
            conflict = self.repository.conflict(note_id)
            if conflict is None:
                return None
            selected = min(
                conflict.candidates,
                key=lambda item: (
                    0 if item.origin_device == self.origin_device else 1,
                    item.origin_device,
                    item.change_id,
                ),
            )
            return _document(selected.title or "Untitled", selected.body or "")
        path = self.repository.notes_dir / f"{note_id}.md"
        try:
            return path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return None

    def _require_live_head(self, note_id: UUID) -> Revision:
        if self.current_state:
            if self.repository.conflict(note_id) is not None:
                raise ConflictRequired("explicit conflict resolution is required")
            state = self.repository.get(note_id)
            if state is None:
                raise NoteNotFoundError(str(note_id))
            return state
        status = self.repository.graph().status(note_id)
        if status.conflicted:
            raise ConflictRequired("explicit conflict resolution is required")
        if not status.head_ids:
            if status.pending_ids:
                raise ConflictRequired("cannot edit a note with incomplete ancestry")
            raise NoteNotFoundError(str(note_id))
        head = self.repository.revision(status.head_ids[0])
        if head is None or head.deleted:
            raise NoteNotFoundError(str(note_id))
        return head

    def list_notes(self, query: str = "") -> list[NoteSummary]:
        if self.current_state:
            query_key = _search_key(query)
            current = {state.note_id: state for state in self.repository.list()}
            conflicts = {item.note_id: item for item in self.repository.conflicts()}
            summaries = []
            for note_id in sorted(set(current) | set(conflicts), key=str):
                conflict = conflicts.get(note_id)
                candidates = () if conflict is None else conflict.candidates
                state = current.get(note_id)
                if state is None and candidates:
                    state = min(
                        candidates,
                        key=lambda item: (
                            0 if item.origin_device == self.origin_device else 1,
                            item.origin_device,
                            item.change_id,
                        ),
                    )
                if state is None:
                    continue
                searchable = "\n".join(
                    _document(item.title or "Untitled", item.body or "")
                    for item in (candidates or (state,))
                )
                if query_key and query_key not in _search_key(searchable):
                    continue
                summaries.append(NoteSummary(
                    note_id=note_id,
                    title=state.title or "Untitled",
                    preview=_preview(state.body or ""),
                    conflicted=conflict is not None,
                    modified_utc=max(
                        item.modified_utc for item in (candidates or (state,))
                    ),
                ))
            summaries.sort(
                key=lambda item: (item.modified_utc, str(item.note_id)), reverse=True
            )
            return summaries
        graph = self.repository.graph()
        note_ids = sorted({revision.note_id for revision in self.repository.revisions()}, key=str)
        query_key = _search_key(query)
        summaries: list[NoteSummary] = []

        for note_id in note_ids:
            status = graph.status(note_id)
            heads = graph.heads(note_id)
            if not heads:
                continue
            if len(heads) == 1 and heads[0].deleted:
                continue

            working_body = (
                heads[0].body
                if len(heads) == 1
                else self._working_body(note_id)
            )
            body = working_body if working_body is not None else ""
            searchable = "\n".join(
                [body, *(head.body for head in heads if not head.deleted)]
            )
            if query_key and query_key not in _search_key(searchable):
                continue

            summaries.append(
                NoteSummary(
                    note_id=note_id,
                    title=(
                        _title(body)
                        if working_body is not None
                        else "Conflict"
                    ),
                    preview=_preview(body),
                    conflicted=status.conflicted,
                    modified_utc=max(head.modified_utc for head in heads),
                )
            )

        summaries.sort(key=lambda item: (item.modified_utc, str(item.note_id)), reverse=True)
        return summaries

    def open_note(self, note_id: UUID) -> str:
        if self.current_state:
            body = self._working_body(note_id)
            if body is None:
                raise NoteNotFoundError(str(note_id))
            heads = self.head_ids(note_id)
            if len(heads) == 1:
                self._edit_bases[note_id] = heads[0]
            return body
        graph = self.repository.graph()
        status = graph.status(note_id)
        if len(status.head_ids) == 1:
            head = graph.heads(note_id)[0]
            if head.deleted:
                raise NoteNotFoundError(str(note_id))
            self._edit_bases[note_id] = head.revision_id
            return head.body
        elif not status.conflicted:
            raise NoteNotFoundError(str(note_id))

        body = self._working_body(note_id)
        if body is None:
            raise NoteNotFoundError(str(note_id))
        return body

    def create_note(self, body: str) -> UUID:
        note_id = self._note_id_factory()
        if self.current_state:
            parts = split_note(body)
            state = self.repository.save_local(
                note_id, parts.title or "Untitled", parts.content, self._now()
            )
            self._edit_bases[note_id] = state.change_id
            return note_id
        revision = self.repository.create_revision(
            note_id,
            body,
            self.origin_device,
            self._now(),
        )
        self._edit_bases[note_id] = revision.revision_id
        return note_id

    def save_note(self, note_id: UUID, body: str) -> Revision | StateEnvelope:
        current = self._require_live_head(note_id)
        if self.current_state:
            expected_head = self._edit_bases.get(note_id, current.change_id)
            if current.change_id != expected_head:
                raise ConflictRequired("note changed since it was opened")
            parts = split_note(body)
            title = parts.title or "Untitled"
            if current.title == title and current.body == parts.content:
                return current
            state = self.repository.save_local(
                note_id, title, parts.content, self._now()
            )
            self._edit_bases[note_id] = state.change_id
            return state
        expected_head = self._edit_bases.get(note_id, current.revision_id)
        if current.revision_id != expected_head:
            raise ConflictRequired("note changed since it was opened")
        if current.body == body:
            return current
        revision = self.repository.create_revision(
            note_id,
            body,
            self.origin_device,
            self._now(),
            expected_head_ids=(expected_head,),
        )
        self._edit_bases[note_id] = revision.revision_id
        return revision

    def delete_note(
        self,
        note_id: UUID,
        *,
        expected_revision_ids: tuple[str, ...] | None = None,
    ) -> None:
        """Create a tombstone delivered by the ordinary JSON sync path."""
        current = self._require_live_head(note_id)
        if self.current_state:
            expected = expected_revision_ids or (current.change_id,)
            if self.head_ids(note_id) != tuple(expected):
                raise ConflictRequired("note changed since deletion was requested")
            self.repository.delete_local(note_id)
            self._edit_bases.pop(note_id, None)
            self._conflict_snapshots.pop(note_id, None)
            return
        expected = expected_revision_ids or (current.revision_id,)
        self.repository.create_revision(
            note_id,
            "",
            self.origin_device,
            self._now(),
            deleted=True,
            expected_head_ids=expected,
        )
        self._edit_bases.pop(note_id, None)
        self._conflict_snapshots.pop(note_id, None)

    def conflict(self, note_id: UUID) -> tuple[ConflictCandidate, ...]:
        if self.current_state:
            conflict = self.repository.conflict(note_id)
            candidates = () if conflict is None else tuple(
                ConflictCandidate(
                    revision_id=state.change_id,
                    origin_device=state.origin_device,
                    deleted=False,
                    preview=_preview(_document(state.title or "Untitled", state.body or "")),
                    body=_document(state.title or "Untitled", state.body or ""),
                )
                for state in conflict.candidates
            )
        else:
            legacy = list_conflict(self.repository, note_id)
            candidates = tuple(self._legacy_candidate(candidate) for candidate in legacy)
        if candidates:
            self._conflict_snapshots[note_id] = tuple(
                candidate.revision_id for candidate in candidates
            )
        else:
            self._conflict_snapshots.pop(note_id, None)
        return candidates

    def _legacy_candidate(self, candidate: LegacyConflictCandidate) -> ConflictCandidate:
        revision = self.repository.revision(candidate.revision_id)
        body = "" if revision is None else revision.body
        return ConflictCandidate(
            candidate.revision_id,
            candidate.origin_device,
            candidate.deleted,
            candidate.preview,
            body,
        )

    def resolve(
        self,
        note_id: UUID,
        choice: Literal["keep-linux", "keep-android", "skip"],
        revision_id: str | None = None,
    ) -> Revision | StateEnvelope | None:
        if choice == "skip":
            self._conflict_snapshots.pop(note_id, None)
            if self.current_state:
                return None
            return resolve_conflict(
                self.repository,
                note_id,
                choice,
                self.origin_device,
                self._now(),
            )

        snapshot = self._conflict_snapshots.get(note_id)
        if snapshot is None:
            raise StaleConflictChoice("inspect the current conflict before resolving it")
        if self.current_state:
            current_heads = self.head_ids(note_id)
            if current_heads != snapshot:
                self._conflict_snapshots.pop(note_id, None)
                raise StaleConflictChoice("conflict changed before resolution")
            candidates = self.conflict(note_id)
            expected_origin = "linux" if choice == "keep-linux" else "android"
            selected = next(
                (
                    candidate for candidate in candidates
                    if candidate.revision_id == revision_id
                    and candidate.origin_device.startswith(expected_origin)
                ),
                None,
            )
            if selected is None:
                self._conflict_snapshots.pop(note_id, None)
                raise ValueError("exact conflict version is not available")
            try:
                resolution = self.repository.resolve(
                    note_id, selected.revision_id, self._now()
                )
            finally:
                self._conflict_snapshots.pop(note_id, None)
            self._edit_bases[note_id] = resolution.change_id
            return resolution
        try:
            resolution = resolve_conflict(
                self.repository,
                note_id,
                choice,
                self.origin_device,
                self._now(),
                revision_id=revision_id,
                expected_head_ids=snapshot,
            )
        except (ConflictChangedError, ConflictRequired) as error:
            raise StaleConflictChoice("conflict changed before resolution") from error
        finally:
            self._conflict_snapshots.pop(note_id, None)
        if resolution is not None and not resolution.deleted:
            self._edit_bases[note_id] = resolution.revision_id
        else:
            self._edit_bases.pop(note_id, None)
        return resolution

    def head_ids(self, note_id: UUID) -> tuple[str, ...]:
        if self.current_state:
            return self.repository.head_ids(note_id)
        return self.repository.graph().status(note_id).head_ids

    def is_conflicted(self, note_id: UUID) -> bool:
        if self.current_state:
            return self.repository.conflict(note_id) is not None
        return self.repository.graph().status(note_id).conflicted

    def is_deleted(self, note_id: UUID) -> bool:
        if self.current_state:
            return self.repository.is_deleted(note_id)
        heads = self.repository.graph().heads(note_id)
        return self.repository.is_purged(note_id) or (
            len(heads) == 1 and heads[0].deleted
        )

    @staticmethod
    def change_id(change: Revision | StateEnvelope) -> str:
        return change.change_id if isinstance(change, StateEnvelope) else change.revision_id

    @staticmethod
    def change_deleted(change: Revision | StateEnvelope) -> bool:
        return change.operation == "delete" if isinstance(change, StateEnvelope) else change.deleted

    def delivery_statuses(self) -> dict[UUID, str]:
        if self.current_state:
            result = {state.note_id: "Pending" for state in self.repository.pending_states()}
            result.update({conflict.note_id: "Needs attention" for conflict in self.repository.conflicts()})
            return result
        target = self.repository.target_device
        if target is None:
            return {}
        from reasonnotes_sync.delivery import DeliveryLedger, DeliveryState
        revision_notes = {
            revision.revision_id: revision.note_id for revision in self.repository.revisions()
        }
        states: dict[UUID, list[DeliveryState]] = {}
        for entry in DeliveryLedger(self.repository.root).entries(target):
            note_id = revision_notes.get(entry.revision_id)
            if note_id is not None:
                states.setdefault(note_id, []).append(entry.state)
        result = {}
        for note_id, note_states in states.items():
            if DeliveryState.NEEDS_ATTENTION in note_states:
                value = "Needs attention"
            elif DeliveryState.PENDING in note_states:
                value = "Pending"
            elif DeliveryState.TRANSFER_REQUESTED in note_states:
                value = "Transfer requested"
            elif note_states and all(state == DeliveryState.CONFIRMED for state in note_states):
                value = "Confirmed"
            else:
                value = "Local"
            result[note_id] = value
        return result

    def sync_notes(self) -> list[NoteSummary]:
        rows = {summary.note_id: summary for summary in self.list_notes("")}
        if self.current_state:
            for state in self.repository.pending_states():
                if state.operation != "delete" or state.note_id in rows:
                    continue
                rows[state.note_id] = NoteSummary(
                    state.note_id,
                    "Deleted note",
                    "Pending deletion",
                    False,
                    state.modified_utc,
                )
        else:
            graph = self.repository.graph()
            note_ids = {revision.note_id for revision in self.repository.revisions()}
            for note_id in note_ids:
                if note_id in rows:
                    continue
                heads = graph.heads(note_id)
                if len(heads) != 1 or not heads[0].deleted:
                    continue
                rows[note_id] = NoteSummary(
                    note_id, "Deleted note", "Pending deletion", False,
                    heads[0].modified_utc,
                )
        return sorted(
            rows.values(),
            key=lambda row: (row.modified_utc, str(row.note_id)),
            reverse=True,
        )
