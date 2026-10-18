"""Qt Widgets coordinator over the UI-independent ReasonNotes presenter."""

from __future__ import annotations

import re
from uuid import UUID

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot

from reasonnotes_app.note_document import change_content, change_title, split_note
from reasonnotes_app.presenter import ConflictVersion, NotePresenter, NoteRow

from .models import ConflictListModel, NoteListModel, SyncListModel


class _WorkerSignals(QObject):
    completed = Signal(object)
    failed = Signal(str)


class _CallableWorker(QRunnable):
    def __init__(self, operation):
        super().__init__()
        self.operation = operation
        self.signals = _WorkerSignals()

    @Slot()
    def run(self):
        try:
            result = self.operation()
        except Exception as error:
            self.signals.failed.emit(str(error))
            return
        self.signals.completed.emit(result)


class WidgetsController(QObject):
    state_changed = Signal()
    save_status_changed = Signal()
    draft_changed = Signal()
    conflict_changed = Signal()
    selection_changed = Signal()
    models_changed = Signal()
    incoming_scan_finished = Signal(object)
    incoming_scan_failed = Signal(str)
    incoming_message_changed = Signal(str)

    def __init__(
        self,
        presenter: NotePresenter,
        *,
        thread_pool=None,
        parent: QObject | None = None,
    ):
        super().__init__(parent)
        self.presenter = presenter
        self.thread_pool = thread_pool or QThreadPool.globalInstance()
        self.note_model = NoteListModel(self)
        self.sync_model = SyncListModel(self)
        self.conflict_model = ConflictListModel(self)
        self._bulk_selected_ids: set[str] = set()
        self._pending_delete_ids: tuple[str, ...] = ()
        self._pending_delete_revisions: dict[str, tuple[str, ...]] = {}
        self._sync_selected_ids: set[str] = set()
        self._sync_query = ""
        self._incoming_scanner = None
        self._incoming_worker = None
        self._incoming_manual_worker = None
        self._incoming_queued = False
        self._incoming_message = ""
        self._sync_workers: set[_CallableWorker] = set()
        self._delivery_status_by_note: dict[str, str] = {}
        self.sync_model.selection_requested.connect(self.set_sync_selected)
        self.refresh_models()

    @staticmethod
    def _note_mapping(row: NoteRow, *, bulk_selected: bool = False):
        return {
            "noteId": row.note_id,
            "title": row.title,
            "preview": row.preview,
            "conflicted": row.conflicted,
            "modifiedUtc": row.modified_utc.isoformat(),
            "deliveryStatus": row.delivery_status,
            "bulkSelected": bulk_selected,
        }

    @staticmethod
    def _conflict_mapping(row: ConflictVersion):
        return {
            "revisionId": row.revision_id,
            "originDevice": row.origin_device,
            "deleted": row.deleted,
            "body": row.body,
        }

    @staticmethod
    def _plain_preview(source: str) -> str:
        one_line = " ".join(source.splitlines())
        return re.sub(r"[#*_`>\[\]()~]", "", one_line).strip()

    @property
    def current_title(self) -> str:
        return split_note(self.presenter.draft).title

    @property
    def current_content(self) -> str:
        return split_note(self.presenter.draft).content

    @property
    def active_note_id(self) -> str | None:
        return self.presenter.active_note_id

    @property
    def incoming_message(self) -> str:
        return self._incoming_message

    @property
    def pending_delete_ids(self) -> tuple[str, ...]:
        return self._pending_delete_ids

    @property
    def bulk_selected_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._bulk_selected_ids))

    @property
    def sync_selected_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._sync_selected_ids))

    def _set_incoming_message(self, message: str) -> None:
        if message == self._incoming_message:
            return
        self._incoming_message = message
        self.incoming_message_changed.emit(message)

    def refresh_models(self) -> None:
        live_ids = {
            str(row.note_id) for row in self.presenter.service.list_notes("")
        }
        self._bulk_selected_ids.intersection_update(live_ids)
        self._sync_selected_ids.intersection_update(
            row.note_id for row in self.presenter.sync_notes()
        )
        note_changed = self.note_model.replace(
            self._note_mapping(
                row, bulk_selected=row.note_id in self._bulk_selected_ids
            )
            for row in self.presenter.notes
        )
        query = self._sync_query.casefold()
        sync_rows = []
        for row in self.presenter.sync_notes():
            if query and query not in f"{row.title}\n{row.preview}".casefold():
                continue
            sync_rows.append(
                {
                    "noteId": row.note_id,
                    "title": row.title,
                    "preview": self._plain_preview(row.preview),
                    "selected": row.note_id in self._sync_selected_ids,
                    "deliveryStatus": row.delivery_status,
                }
            )
        sync_changed = self.sync_model.replace(sync_rows)
        self._delivery_status_by_note = {
            row["noteId"]: row["deliveryStatus"] for row in sync_rows
        }
        conflict_changed = self.refresh_conflict_model()
        if note_changed or sync_changed or conflict_changed:
            self.models_changed.emit()

    def refresh_conflict_model(self) -> bool:
        candidates = (
            ()
            if self.presenter.conflict_view is None
            else self.presenter.conflict_view.candidates
        )
        return self.conflict_model.replace(
            self._conflict_mapping(candidate) for candidate in candidates
        )

    def _notify(
        self, *, draft: bool = False, conflict: bool = False,
        refresh_models: bool = True,
    ) -> None:
        if refresh_models:
            self.refresh_models()
        elif conflict and self.refresh_conflict_model():
            self.models_changed.emit()
        self.state_changed.emit()
        self.save_status_changed.emit()
        if draft:
            self.draft_changed.emit()
        if conflict:
            self.conflict_changed.emit()
        self.selection_changed.emit()

    def create_note(self) -> bool:
        changed = self.presenter.create_note()
        self._notify(draft=changed, conflict=True)
        return changed

    def select_note(self, note_id: str) -> bool:
        before = self.presenter.notes
        was_dirty = self.presenter.dirty
        changed = self.presenter.select_note(note_id)
        if changed:
            self._bulk_selected_ids.clear()
        self._notify(
            draft=changed,
            conflict=True,
            refresh_models=(
                self.presenter.notes != before
                or (was_dirty and not self.presenter.dirty)
            ),
        )
        return changed

    def edit_title(self, title: str) -> bool:
        changed = self.presenter.edit_draft(
            change_title(self.presenter.draft, title),
            implicit_title=(not bool(title.strip()))
            if self.presenter.active_note_id is None
            else None,
        )
        self.save_status_changed.emit()
        return changed

    def edit_content(self, content: str) -> bool:
        implicit = None
        if self.presenter.active_note_id is None:
            implicit = (
                self.presenter._unbound_implicit_title
                or not split_note(self.presenter.draft).has_title
            )
        changed = self.presenter.edit_draft(
            change_content(self.presenter.draft, content),
            implicit_title=implicit,
        )
        self.save_status_changed.emit()
        return changed

    def save_now(self) -> bool:
        before = self.presenter.active_note_id
        saved = self.presenter.save_active()
        self._notify(draft=(before != self.presenter.active_note_id))
        return saved

    def autosave(self) -> bool:
        was_dirty = self.presenter.dirty
        before = self.presenter.active_note_id
        saved = self.presenter.autosave()
        if was_dirty or not saved:
            self._notify(draft=(before != self.presenter.active_note_id))
        return saved

    def close_requested(self) -> bool:
        if self.presenter.sync_state == "Running":
            return False
        saved = self.presenter.close_requested()
        self._notify()
        return saved

    def search(self, query: str) -> None:
        self.presenter.set_search(query)
        self._notify()

    def toggle_bulk_note(self, note_id: str) -> bool:
        if note_id not in {row.note_id for row in self.presenter.notes}:
            return False
        if note_id in self._bulk_selected_ids:
            self._bulk_selected_ids.remove(note_id)
        else:
            self._bulk_selected_ids.add(note_id)
        self.refresh_models()
        self.selection_changed.emit()
        return True

    def set_bulk_selection(self, note_ids) -> None:
        live = {
            str(row.note_id) for row in self.presenter.service.list_notes("")
        }
        self._bulk_selected_ids = {
            note_id for note_id in note_ids if note_id in live
        }
        self.refresh_models()
        self.selection_changed.emit()

    def clear_bulk_selection(self) -> None:
        if not self._bulk_selected_ids:
            return
        self._bulk_selected_ids.clear()
        self.refresh_models()
        self.selection_changed.emit()

    def prepare_delete(self) -> tuple[str, ...]:
        if self._bulk_selected_ids:
            self._pending_delete_ids = tuple(sorted(self._bulk_selected_ids))
        elif self.presenter.active_note_id is not None:
            self._pending_delete_ids = (self.presenter.active_note_id,)
        else:
            self._pending_delete_ids = ()
        self._pending_delete_revisions = {
            note_id: self.presenter.repository.note_revision_ids(UUID(note_id))
            for note_id in self._pending_delete_ids
        }
        self.selection_changed.emit()
        return self._pending_delete_ids

    def cancel_delete(self) -> None:
        self._pending_delete_ids = ()
        self._pending_delete_revisions = {}
        self.selection_changed.emit()

    def confirm_delete(self) -> bool:
        ids = self._pending_delete_ids
        expected_revisions = self._pending_delete_revisions
        self._pending_delete_ids = ()
        self._pending_delete_revisions = {}
        if not ids:
            self.selection_changed.emit()
            return False
        if len(ids) == 1 and self.presenter.active_note_id == ids[0] and not self._bulk_selected_ids:
            deleted = (
                ids
                if self.presenter.delete_active(expected_revisions[ids[0]])
                else ()
            )
        else:
            deleted = self.presenter.delete_notes(
                ids, expected_revisions=expected_revisions
            )
        self._bulk_selected_ids.difference_update(deleted)
        self._notify(draft=bool(deleted), conflict=True)
        return len(deleted) == len(ids) and self.presenter.save_state != "Error"

    def configure_incoming_scan(self, scanner) -> None:
        self._incoming_scanner = scanner

    def refresh_incoming(self) -> bool:
        if self._incoming_scanner is None:
            self._set_incoming_message("Incoming refresh unavailable")
            return False
        if self._incoming_worker is not None:
            self._incoming_queued = True
            self._set_incoming_message("Refresh queued…")
            return True
        return self.start_incoming_scan(self._incoming_scanner, manual=True)

    def start_incoming_scan(self, scanner, *, manual: bool = False) -> bool:
        if self._incoming_worker is not None:
            return False
        worker = _CallableWorker(scanner)
        self._incoming_worker = worker
        if manual:
            self._incoming_manual_worker = worker
            self._set_incoming_message("Checking incoming notes…")
        worker.signals.completed.connect(
            lambda report, current=worker: self._incoming_completed(current, report)
        )
        worker.signals.failed.connect(
            lambda reason, current=worker: self._incoming_failed(current, reason)
        )
        self.thread_pool.start(worker)
        return True

    def _incoming_completed(self, worker, report) -> None:
        if worker is not self._incoming_worker:
            return
        self._incoming_worker = None
        self.presenter.refresh()
        self._notify(conflict=True)
        self.incoming_scan_finished.emit(report)
        if worker is self._incoming_manual_worker:
            self._incoming_manual_worker = None
            errors = tuple(getattr(report, "errors", ()))
            imported = len(getattr(report, "imported", ()))
            confirmed = len(getattr(report, "confirmed", ()))
            if errors:
                self._set_incoming_message(
                    f"Refresh completed with {len(errors)} warning(s)"
                )
            elif imported or confirmed:
                self._set_incoming_message(
                    f"Received {imported} revision(s), confirmed {confirmed}"
                )
            else:
                self._set_incoming_message("Notes are up to date")
        self._start_queued_incoming()

    def _incoming_failed(self, worker, reason: str) -> None:
        if worker is not self._incoming_worker:
            return
        self._incoming_worker = None
        self.incoming_scan_failed.emit(reason)
        if worker is self._incoming_manual_worker:
            self._incoming_manual_worker = None
            self._set_incoming_message("Could not refresh incoming notes")
        self._start_queued_incoming()

    def _start_queued_incoming(self) -> None:
        if not self._incoming_queued:
            return
        self._incoming_queued = False
        self.start_incoming_scan(self._incoming_scanner, manual=True)

    def open_sync_panel(self) -> None:
        self._sync_selected_ids.intersection_update(
            row.note_id for row in self.presenter.sync_notes()
        )
        self._sync_query = ""
        self.refresh_models()

    def set_sync_search(self, query: str) -> None:
        self._sync_query = query
        self.refresh_models()

    def set_sync_selected(self, note_id: str, selected: bool) -> None:
        if selected:
            self._sync_selected_ids.add(note_id)
        else:
            self._sync_selected_ids.discard(note_id)
        for row in range(self.sync_model.rowCount()):
            if self.sync_model.note_id_at(row) == note_id:
                self.sync_model.update_row(row, selected=selected)
                break
        self.selection_changed.emit()

    def select_all_sync_notes(self) -> None:
        self._sync_selected_ids.update(
            row.note_id for row in self.presenter.sync_notes()
        )
        self.refresh_models()
        self.selection_changed.emit()

    def clear_sync_selection(self) -> None:
        self._sync_selected_ids.clear()
        self.refresh_models()
        self.selection_changed.emit()

    def start_sync(self, selection) -> bool:
        if self.presenter.sync_state == "Running":
            return False
        snapshot = None if selection is None else tuple(selection)
        if not self.presenter.prepare_sync(snapshot):
            self._notify()
            return False
        worker = _CallableWorker(lambda: self.presenter.execute_sync(snapshot))
        self._sync_workers.add(worker)
        worker.signals.completed.connect(
            lambda report, current=worker: self._sync_completed(current, report)
        )
        worker.signals.failed.connect(
            lambda reason, current=worker: self._sync_failed(current, reason)
        )
        self._notify()
        self.thread_pool.start(worker)
        return True

    def sync_all(self) -> bool:
        return self.start_sync(None)

    def sync_selected(self) -> bool:
        if not self._sync_selected_ids:
            return False
        return self.start_sync(tuple(sorted(self._sync_selected_ids)))

    def _sync_completed(self, worker, report) -> None:
        self._sync_workers.discard(worker)
        self.presenter.complete_sync(report)
        self._notify(conflict=True)

    def _sync_failed(self, worker, reason: str) -> None:
        self._sync_workers.discard(worker)
        self.presenter.fail_sync(reason)
        self._notify()

    def resolve_conflict(self, choice: str, revision_id: str | None = None) -> bool:
        resolved = self.presenter.resolve_conflict(choice, revision_id)
        self._notify(draft=resolved, conflict=True)
        return resolved

    def skip_conflict(self) -> bool:
        resolved = self.presenter.resolve_conflict("skip")
        self._notify(conflict=True)
        return resolved
