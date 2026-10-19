"""ReasonNotes native Qt Widgets main window."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings, QSignalBlocker, Qt, QTimer
from PySide6.QtGui import (
    QCloseEvent,
    QColor,
    QKeySequence,
    QPainter,
    QShortcut,
)
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStackedWidget,
    QStyle,
    QStyleOption,
)

from .editor_page import EditorPage
from .conflict_page import ConflictPage
from .i18n import Translator
from .material import GlassCard
from .settings_page import SettingsPage
from .sidebar import NotesSidebar
from .sync_panel import SyncPanel


class ReasonNotesMainWindow(QMainWindow):
    def __init__(
        self,
        controller,
        *,
        settings: QSettings | None = None,
        translator: Translator | None = None,
        deletion_pairing=None,
        confirm_delete=None,
        native_window_material: bool = False,
        kitty_window_material: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        if native_window_material and kitty_window_material:
            raise ValueError("window material variants are mutually exclusive")
        self.controller = controller
        self.settings = settings if settings is not None else QSettings()
        self.translator = translator or Translator(self.settings, self)
        self._refreshing = False
        self._first_show = True
        self._confirm_delete = confirm_delete or self._confirm_delete_dialog
        if kitty_window_material:
            self.window_material_mode = "kitty-equivalent"
        elif native_window_material:
            self.window_material_mode = "native-kvantum"
        else:
            self.window_material_mode = "reasonnotes-custom"
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
        self.settings_page = SettingsPage(
            self.translator, deletion_pairing, self.page_stack
        )
        self.conflict_page = ConflictPage(controller, self.translator, self.page_stack)
        self.page_stack.addWidget(self.settings_page)
        self.page_stack.addWidget(self.conflict_page)

        self.main_splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self.main_splitter.setObjectName("mainSplitter")
        self.main_splitter.setChildrenCollapsible(False)
        self.main_splitter.addWidget(self.sidebar)
        self.main_splitter.addWidget(self.page_stack)
        self.main_splitter.setStretchFactor(0, 0)
        self.main_splitter.setStretchFactor(1, 1)
        self.setCentralWidget(self.main_splitter)
        self.sync_panel = SyncPanel(controller, self.translator, self)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.sync_panel)
        self.sync_panel.hide()

        if self.window_material_mode == "kitty-equivalent":
            # The measured Kitty-equivalent sheet is already the complete
            # window material. Keep local outlines and controls, but avoid
            # compositing pane-sized fills over that calibrated base.
            self.sidebar.set_material_fill_enabled(False)
            for card in self.findChildren(GlassCard):
                card.set_material_fill_enabled(False)

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
        self.sidebar.sync_button.clicked.connect(self.open_sync_panel)
        self.sidebar.settings_button.clicked.connect(self.open_settings)
        self.sidebar.search_field.textChanged.connect(controller.search)
        self.sidebar.list_view.activated.connect(self.activate_note)
        self.sidebar.list_view.selectionModel().currentChanged.connect(
            self._current_note_changed
        )
        controller.state_changed.connect(self.refresh_from_controller)
        controller.draft_changed.connect(self.refresh_from_controller)
        controller.save_status_changed.connect(self._refresh_status)
        controller.conflict_changed.connect(self.refresh_from_controller)
        controller.models_changed.connect(self._restore_active_selection)
        controller.incoming_message_changed.connect(self._show_incoming_message)
        self.translator.language_changed.connect(lambda _language: self.retranslate())

        self._shortcuts = [
            QShortcut(QKeySequence.StandardKey.New, self, activated=self._new_note),
            QShortcut(QKeySequence.StandardKey.Save, self, activated=self._save_now),
            QShortcut(QKeySequence.StandardKey.Find, self, activated=self._focus_search),
            QShortcut(QKeySequence("F5"), self,
                      activated=self.controller.refresh_incoming),
        ]
        self.retranslate()
        self.refresh_from_controller()

    def _show_incoming_message(self, message: str) -> None:
        persistent = message in ("Checking incoming notes…", "Refresh queued…")
        self.statusBar().showMessage(message, 0 if persistent else 5000)

    def retranslate(self) -> None:
        tr = self.translator.text
        self.setWindowTitle(tr("app_name"))
        self.sidebar.set_brand_text(tr("app_name"))
        self.sidebar.new_button.setText(tr("new_note"))
        self.sidebar.save_button.setText(tr("save"))
        self.sidebar.sync_button.setText(tr("sync"))
        self.sidebar.delete_button.setText(tr("delete"))
        self.sidebar.settings_button.setText(tr("settings"))
        self.sidebar.notes_heading.setText(tr("notes_section").upper())
        self.sidebar.search_field.setPlaceholderText(tr("search_notes"))
        self.sidebar.search_field.setAccessibleName(tr("search_notes"))
        self.editor.title_editor.setPlaceholderText(tr("untitled"))
        self.editor.title_editor.setAccessibleName(tr("note_title"))
        self.editor.body_editor.setPlaceholderText(tr("start_writing"))
        self.settings_page.retranslate()
        self._refresh_status()

    def open_settings(self) -> None:
        # The permanent sidebar is the navigation control; Settings toggles.
        if self.page_stack.currentWidget() is self.settings_page:
            self.back_to_notes()
            return
        self.autosave_timer.stop()
        if self.controller.save_now():
            self.page_stack.setCurrentWidget(self.settings_page)
            self.sidebar.settings_button.setChecked(True)

    def back_to_notes(self) -> None:
        self.sidebar.settings_button.setChecked(False)
        self.refresh_from_controller()

    def open_sync_panel(self) -> None:
        self.controller.open_sync_panel()
        self.sync_panel.show()
        self.sync_panel.raise_()

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

    def _current_note_changed(self, current, _previous) -> None:
        modifiers = QApplication.keyboardModifiers()
        bulk_modifiers = (
            Qt.KeyboardModifier.ControlModifier
            | Qt.KeyboardModifier.ShiftModifier
        )
        if modifiers & bulk_modifiers:
            return
        self.activate_note(current)

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
        tr = self.translator.text
        answer = QMessageBox.question(
            self,
            tr("delete_notes") if bulk else tr("delete_note"),
            self._delete_confirmation_text(count),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        return answer == QMessageBox.StandardButton.Yes

    def _delete_confirmation_text(self, count: int) -> str:
        key = "delete_confirm_one" if count == 1 else "delete_confirm_many"
        return self.translator.text(key).format(count=count)

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
        tr = self.translator.text
        state_key = presenter.save_state.casefold()
        text = tr(state_key)
        if presenter.save_error:
            text += f": {presenter.save_error}"
        self.editor.save_status.setText(f"{tr('local')}: {text}")
        self.sidebar.local_status.setText(f"{tr('local')}: {text}")
        sync = presenter.sync_state
        sync = tr(sync.casefold())
        if presenter.sync_message:
            sync += f": {presenter.sync_message}"
        self.sidebar.sync_status.setText(f"{tr('phone')}: {sync}")
        active = presenter.active_note_id
        delivery = (
            tr("no_note_selected")
            if active is None
            else self.controller._delivery_status_by_note.get(active, "Local")
        )
        self.editor.delivery_status.setText(f"{tr('phone')}: {delivery}")

    def refresh_from_controller(self) -> None:
        self.sidebar.settings_button.setChecked(False)
        self._refreshing = True
        try:
            self.editor.set_document(
                self.controller.current_title,
                self.controller.current_content,
            )
            self.editor.set_editable(self.controller.presenter.can_edit)
            self.conflict_page.load()
            self.page_stack.setCurrentWidget(
                self.conflict_page
                if self.controller.presenter.conflict_view is not None
                else self.editor
            )
            self._restore_active_selection()
            self._refresh_status()
        finally:
            self._refreshing = False

    def paintEvent(self, event) -> None:
        if self.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground):
            painter = QPainter(self)
            if self.window_material_mode == "native-kvantum":
                # A plain QMainWindow paint event does not guarantee that the
                # style's window primitive is drawn. Clear the damaged alpha
                # region, then explicitly delegate the complete window sheet
                # to the active qt6ct -> Kvantum style chain.
                painter.setClipRegion(event.region())
                painter.setCompositionMode(
                    QPainter.CompositionMode.CompositionMode_Source
                )
                painter.fillRect(event.rect(), Qt.GlobalColor.transparent)
                painter.setCompositionMode(
                    QPainter.CompositionMode.CompositionMode_SourceOver
                )
                option = QStyleOption()
                option.initFrom(self)
                self.style().drawPrimitive(
                    QStyle.PrimitiveElement.PE_Widget,
                    option,
                    painter,
                    self,
                )
            elif self.window_material_mode == "kitty-equivalent":
                painter.setCompositionMode(
                    QPainter.CompositionMode.CompositionMode_Source
                )
                painter.fillRect(event.rect(), QColor(28, 33, 33, 209))
            else:
                # Keep the accepted renderer available as the default A/B
                # path. Its uniform palette-derived sheet avoids quantized
                # full-window gradient bands while cards provide local depth.
                base = self.palette().base().color()
                material = base.lighter(108)
                material.setAlpha(max(105, min(230, int(base.alpha() * .93))))
                painter.setCompositionMode(
                    QPainter.CompositionMode.CompositionMode_Source
                )
                painter.fillRect(event.rect(), material)
            painter.end()
        else:
            super().paintEvent(event)

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
