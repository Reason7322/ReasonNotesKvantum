"""ReasonNotes native Qt Widgets main window."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings, QSignalBlocker, Qt, QTimer
from PySide6.QtGui import QCloseEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QLabel,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStackedWidget,
)

from .editor_page import EditorPage
from .sidebar import NotesSidebar


class ReasonNotesMainWindow(QMainWindow):
    def __init__(
        self,
        controller,
        *,
        settings: QSettings | None = None,
        confirm_delete=None,
        parent=None,
    ):
        super().__init__(parent)
        self.controller = controller
        self.settings = settings if settings is not None else QSettings()
        self._refreshing = False
        self._first_show = True
        self._confirm_delete = confirm_delete or self._confirm_delete_dialog
        self.setObjectName("reasonNotesMainWindow")
        self.setWindowTitle("ReasonNotes")
        self.setMinimumSize(820, 560)
        self.resize(1280, 800)

        icon_root = Path(__file__).resolve().parents[2] / "linux-app/icons"
        self.sidebar = NotesSidebar(
            controller.note_model, icon_root=icon_root, parent=self
        )
        self.editor = EditorPage(self)
        self.page_stack = QStackedWidget(self)
        self.page_stack.setObjectName("contentPages")
        self.page_stack.addWidget(self.editor)
        self.settings_placeholder = QLabel("Settings", self.page_stack)
        self.settings_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.conflict_placeholder = QLabel("Conflict", self.page_stack)
        self.conflict_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_stack.addWidget(self.settings_placeholder)
        self.page_stack.addWidget(self.conflict_placeholder)

        self.main_splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self.main_splitter.setObjectName("mainSplitter")
        self.main_splitter.setChildrenCollapsible(False)
        self.main_splitter.addWidget(self.sidebar)
        self.main_splitter.addWidget(self.page_stack)
        self.main_splitter.setStretchFactor(0, 0)
        self.main_splitter.setStretchFactor(1, 1)
        self.setCentralWidget(self.main_splitter)

        sidebar_width = self.settings.value("window/sidebarWidth", 300, int)
        self.main_splitter.setSizes([max(240, min(520, sidebar_width)), 980])

        self.autosave_timer = QTimer(self)
        self.autosave_timer.setObjectName("autosaveTimer")
        self.autosave_timer.setSingleShot(True)
        self.autosave_timer.setInterval(500)
        self.autosave_timer.timeout.connect(self._autosave)

        self.editor.title_edited.connect(self._title_edited)
        self.editor.content_edited.connect(self._content_edited)
        self.sidebar.new_button.clicked.connect(self._new_note)
        self.sidebar.save_button.clicked.connect(self._save_now)
        self.sidebar.delete_button.clicked.connect(self.delete_selection)
        self.sidebar.search_field.textChanged.connect(controller.search)
        self.sidebar.list_view.clicked.connect(self.activate_note)
        self.sidebar.list_view.activated.connect(self.activate_note)
        self.sidebar.list_view.selectionModel().currentChanged.connect(
            lambda current, _previous: self.activate_note(current)
        )
        controller.state_changed.connect(self.refresh_from_controller)
        controller.draft_changed.connect(self.refresh_from_controller)
        controller.save_status_changed.connect(self._refresh_status)
        controller.conflict_changed.connect(self.refresh_from_controller)
        controller.models_changed.connect(self._restore_active_selection)

        self._shortcuts = [
            QShortcut(QKeySequence.StandardKey.New, self, activated=self._new_note),
            QShortcut(QKeySequence.StandardKey.Save, self, activated=self._save_now),
            QShortcut(QKeySequence.StandardKey.Find, self, activated=self._focus_search),
        ]
        self.refresh_from_controller()

    def _title_edited(self, title: str) -> None:
        if self._refreshing:
            return
        self.controller.edit_title(title)
        self.autosave_timer.start()

    def _content_edited(self, content: str) -> None:
        if self._refreshing:
            return
        self.controller.edit_content(content)
        self.autosave_timer.start()

    def _autosave(self) -> None:
        self.controller.autosave()
        self.refresh_from_controller()

    def _save_now(self) -> None:
        self.autosave_timer.stop()
        self.controller.save_now()
        self.refresh_from_controller()

    def _new_note(self) -> None:
        self.autosave_timer.stop()
        if self.controller.create_note():
            self.refresh_from_controller()
            self.editor.title_editor.setFocus()

    def _focus_search(self) -> None:
        self.sidebar.search_field.setFocus()
        self.sidebar.search_field.selectAll()

    def activate_note(self, index) -> None:
        if self._refreshing or not index.isValid():
            return
        note_id = self.controller.note_model.note_id_at(index.row())
        if note_id is None:
            return
        self.autosave_timer.stop()
        if self.controller.select_note(note_id):
            self.refresh_from_controller()

    def sync_bulk_selection(self) -> None:
        selected_rows = self.sidebar.list_view.selectionModel().selectedRows()
        if not selected_rows and self.controller.bulk_selected_ids:
            return
        selected = tuple(
            note_id
            for index in selected_rows
            if (note_id := self.controller.note_model.note_id_at(index.row()))
            is not None
        )
        self.controller.set_bulk_selection(selected if len(selected) > 1 else ())

    def _confirm_delete_dialog(self, count: int, bulk: bool) -> bool:
        noun = "notes" if count != 1 else "note"
        answer = QMessageBox.question(
            self,
            "Delete notes" if bulk else "Delete note",
            f"Permanently delete {count} {noun} from this device? "
            "Recoverable revision history remains protected by the repository.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        return answer == QMessageBox.StandardButton.Yes

    def delete_selection(self) -> None:
        self.sync_bulk_selection()
        ids = self.controller.prepare_delete()
        if not ids:
            return
        bulk = bool(self.controller.bulk_selected_ids)
        if not self._confirm_delete(len(ids), bulk):
            self.controller.cancel_delete()
            return
        self.autosave_timer.stop()
        self.controller.confirm_delete()
        self.refresh_from_controller()

    def _restore_active_selection(self) -> None:
        active = self.controller.active_note_id
        if active is None:
            return
        for row in range(self.controller.note_model.rowCount()):
            if self.controller.note_model.note_id_at(row) == active:
                blocker = QSignalBlocker(self.sidebar.list_view.selectionModel())
                self.sidebar.list_view.setCurrentIndex(
                    self.controller.note_model.index(row, 0)
                )
                del blocker
                break

    def _refresh_status(self) -> None:
        presenter = self.controller.presenter
        text = presenter.save_state
        if presenter.save_error:
            text += f": {presenter.save_error}"
        self.editor.save_status.setText(text)
        self.sidebar.local_status.setText(f"Local: {text}")
        sync = presenter.sync_state
        if presenter.sync_message:
            sync += f": {presenter.sync_message}"
        self.sidebar.sync_status.setText(f"Phone: {sync}")
        active = presenter.active_note_id
        self.editor.delivery_status.setText(
            "No note selected"
            if active is None
            else self.controller._delivery_status_by_note.get(active, "Local")
        )

    def refresh_from_controller(self) -> None:
        self._refreshing = True
        try:
            self.editor.set_document(
                self.controller.current_title,
                self.controller.current_content,
            )
            self.editor.set_editable(self.controller.presenter.can_edit)
            self.page_stack.setCurrentWidget(
                self.conflict_placeholder
                if self.controller.presenter.conflict_view is not None
                else self.editor
            )
            self._restore_active_selection()
            self._refresh_status()
        finally:
            self._refreshing = False

    def save_ui_state(self) -> None:
        sizes = self.main_splitter.sizes()
        if sizes:
            self.settings.setValue("window/sidebarWidth", sizes[0])
        self.settings.setValue("window/geometry", self.saveGeometry())
        self.settings.sync()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if self._first_show:
            self._first_show = False
            geometry = self.settings.value("window/geometry")
            if geometry is not None:
                self.restoreGeometry(geometry)
            QTimer.singleShot(0, self.editor.body_editor.setFocus)

    def closeEvent(self, event: QCloseEvent) -> None:
        self.autosave_timer.stop()
        if not self.controller.close_requested():
            event.ignore()
            self.refresh_from_controller()
            return
        self.save_ui_state()
        event.accept()
