"""Restartable one-time conversion from immutable history to current state."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import os
from pathlib import Path
from uuid import UUID

from reasonnotes_app.note_document import split_note

from .current_store import CurrentNoteStore
from .envelope import EnvelopeError, Revision
from .repository import Repository
from .state_envelope import StateEnvelope


@dataclass(frozen=True, slots=True)
class MigrationReport:
    live_notes: int
    conflicts: int
    deletions: int


@dataclass(frozen=True, slots=True)
class _Derived:
    current: tuple[StateEnvelope, ...]
    conflicts: tuple[tuple[StateEnvelope, StateEnvelope], ...]
    deletions: tuple[StateEnvelope, ...]
    legacy_change_ids: tuple[str, ...]

    def report(self) -> MigrationReport:
        return MigrationReport(len(self.current), len(self.conflicts), len(self.deletions))


def migrate_legacy_repository(
    old_root: Path, staging: Path, active: Path
) -> MigrationReport:
    """Convert one legacy repository, activate only after exact reopen validation."""

    old_root = Path(old_root)
    staging = Path(staging)
    active = Path(active)
    _validate_paths(old_root, staging, active)
    retiring = _retiring_path(old_root)
    if not old_root.exists():
        if not active.is_dir():
            raise ValueError("legacy repository root must exist")
        store = CurrentNoteStore.open(active, "linux")
        report = _report(store)
        if retiring.exists() or retiring.is_symlink():
            _erase_tree(retiring)
        return report
    if retiring.exists() or retiring.is_symlink():
        raise RuntimeError("legacy repository and interrupted retirement both exist")
    legacy = Repository(old_root)
    derived = _derive(legacy)

    if active.exists():
        existing = CurrentNoteStore.open(active, "linux")
        _validate(existing, derived)
        _mark_legacy_processed(existing, derived)
        _retire_legacy(old_root)
        return derived.report()

    _erase_tree(staging)
    staging.parent.mkdir(parents=True, exist_ok=True)
    staged = CurrentNoteStore.open(staging, "linux")
    for state in derived.current:
        staged._write_migrated_current(state)
    for candidates in derived.conflicts:
        staged._write_migrated_conflict(candidates)
    for deletion in derived.deletions:
        staged._write_migrated_deletion(deletion)
    _mark_legacy_processed(staged, derived)

    _validate(CurrentNoteStore.open(staging, "linux"), derived)
    os.replace(staging, active)
    _fsync_directory(active.parent)
    _validate(CurrentNoteStore.open(active, "linux"), derived)
    _retire_legacy(old_root)
    return derived.report()


def _derive(legacy: Repository) -> _Derived:
    _validate_raw_history(legacy.root)
    revisions = legacy.revisions()
    by_note: dict[UUID, list[Revision]] = {}
    for revision in revisions:
        by_note.setdefault(revision.note_id, []).append(revision)

    current: list[StateEnvelope] = []
    conflicts: list[tuple[StateEnvelope, StateEnvelope]] = []
    deletions: list[StateEnvelope] = []
    purged = legacy.purged_ids()
    for note_id in sorted(purged, key=str):
        deletions.append(
            StateEnvelope.deletion(
                note_id,
                (),
                "legacy-migration",
                datetime(1970, 1, 1, tzinfo=timezone.utc),
            )
        )

    graph = legacy.graph()
    for note_id in sorted(by_note, key=str):
        if note_id in purged:
            continue
        status = graph.status(note_id)
        if status.pending_ids:
            raise RuntimeError(f"legacy note has missing ancestry: {note_id}")
        heads = graph.heads(note_id)
        if not heads:
            raise RuntimeError(f"legacy note has no complete head: {note_id}")
        if len(heads) > 2:
            raise RuntimeError(f"legacy note has more than two heads: {note_id}")

        tombstones = tuple(head for head in heads if head.deleted)
        if tombstones:
            selected = min(tombstones, key=lambda revision: revision.revision_id)
            deletions.append(
                StateEnvelope.deletion(
                    note_id,
                    _legacy_parents(selected),
                    selected.origin_device,
                    selected.modified_utc,
                )
            )
        elif len(heads) == 1:
            current.append(_convert_live(heads[0]))
        else:
            candidates = tuple(sorted((_convert_live(head) for head in heads), key=lambda state: state.change_id))
            conflicts.append((candidates[0], candidates[1]))

    return _Derived(
        tuple(sorted(current, key=lambda state: str(state.note_id))),
        tuple(sorted(conflicts, key=lambda pair: str(pair[0].note_id))),
        tuple(sorted(deletions, key=lambda state: str(state.note_id))),
        tuple(sorted(_convert_revision(revision).change_id for revision in revisions)),
    )


def _convert_live(revision: Revision) -> StateEnvelope:
    parts = split_note(revision.body)
    title = parts.title or "Untitled"
    return StateEnvelope.upsert(
        revision.note_id,
        _legacy_parents(revision),
        revision.origin_device,
        revision.modified_utc,
        title,
        parts.content,
    )


def _convert_revision(revision: Revision) -> StateEnvelope:
    if revision.deleted:
        return StateEnvelope.deletion(
            revision.note_id,
            _legacy_parents(revision),
            revision.origin_device,
            revision.modified_utc,
        )
    return _convert_live(revision)


def _mark_legacy_processed(store: CurrentNoteStore, derived: _Derived) -> None:
    for change_id in derived.legacy_change_ids:
        store.mark_processed("legacy", change_id)


def _legacy_parents(revision: Revision) -> tuple[str, ...]:
    if len(revision.parents) > 2:
        raise RuntimeError(f"legacy state has too many parents: {revision.revision_id}")
    return revision.parents


def _validate(store: CurrentNoteStore, expected: _Derived) -> None:
    current = {state.note_id: state for state in store.list()}
    for state in expected.current:
        if current.pop(state.note_id, None) != state:
            raise RuntimeError("staged current state did not reopen exactly")
    if current:
        raise RuntimeError("staged store contains extra live notes")

    actual_conflict_ids = set()
    for candidates in expected.conflicts:
        note_id = candidates[0].note_id
        conflict = store.conflict(note_id)
        if conflict is None or set(conflict.candidates) != set(candidates):
            raise RuntimeError("staged conflict did not reopen exactly")
        actual_conflict_ids.add(note_id)
    if {conflict.note_id for conflict in store.conflicts()} != actual_conflict_ids:
        raise RuntimeError("staged store contains extra conflicts")

    expected_deletions = {state.note_id for state in expected.deletions}
    if store._read_states(store.deleted_dir):
        raise RuntimeError("staged migration retained deletion fences")
    if any(store.get(note_id) is not None for note_id in expected_deletions):
        raise RuntimeError("staged deleted note retained live content")

    expected_pending = {state.note_id: state for state in expected.current}
    actual_pending = {state.note_id: state for state in store.pending_states()}
    if actual_pending != expected_pending:
        raise RuntimeError("staged pending state did not reopen exactly")


def _validate_raw_history(root: Path) -> None:
    history = root / "history"
    if not history.exists():
        return
    if history.is_symlink() or not history.is_dir():
        raise RuntimeError("malformed legacy history root")
    for directory in history.iterdir():
        if directory.is_symlink() or not directory.is_dir():
            raise RuntimeError("malformed legacy note directory")
        try:
            note_id = UUID(directory.name)
        except ValueError as error:
            raise RuntimeError("malformed legacy note directory") from error
        if str(note_id) != directory.name:
            raise RuntimeError("malformed legacy note directory")
        for path in directory.iterdir():
            if path.is_symlink() or not path.is_file() or path.suffix != ".md":
                raise RuntimeError(f"malformed legacy history: {path}")
            try:
                revision = Revision.parse(path.read_bytes())
            except (OSError, EnvelopeError) as error:
                raise RuntimeError(f"malformed legacy history: {path}") from error
            if path.name != f"{revision.revision_id}.md" or revision.note_id != note_id:
                raise RuntimeError("legacy revision filename disagrees with content")


def _validate_paths(old_root: Path, staging: Path, active: Path) -> None:
    old = old_root.resolve(strict=False)
    stage = staging.resolve(strict=False)
    target = active.resolve(strict=False)
    if old in (stage, target) or stage == target or stage.parent != target.parent:
        raise ValueError("migration paths must be distinct and staging/active must be siblings")
    for path in (old_root, staging, active):
        if path.is_symlink():
            raise RuntimeError("migration refuses symbolic-link roots")


def _retiring_path(old_root: Path) -> Path:
    return old_root.with_name(f".{old_root.name}.reasonnotes-v2-retiring")


def _retire_legacy(old_root: Path) -> None:
    retiring = _retiring_path(old_root)
    if retiring.exists() or retiring.is_symlink():
        raise RuntimeError("legacy retirement path already exists")
    os.replace(old_root, retiring)
    _fsync_directory(old_root.parent)
    _erase_tree(retiring)


def _report(store: CurrentNoteStore) -> MigrationReport:
    return MigrationReport(
        len(store.list()),
        len(store.conflicts()),
        len(store._read_states(store.deleted_dir)),
    )


def _erase_tree(root: Path) -> None:
    if not root.exists() and not root.is_symlink():
        return
    if root.is_symlink():
        raise RuntimeError("migration refuses symbolic-link roots")
    if root.is_dir():
        for child in root.iterdir():
            if child.is_symlink():
                child.unlink()
            elif child.is_dir():
                _erase_tree(child)
            elif child.is_file():
                child.unlink()
            else:
                raise RuntimeError(f"cannot retire migration path: {child}")
        root.rmdir()
    elif root.is_file():
        root.unlink()
    else:
        raise RuntimeError(f"cannot retire migration path: {root}")
    if root.parent.exists():
        _fsync_directory(root.parent)


def _fsync_directory(directory: Path) -> None:
    descriptor = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
