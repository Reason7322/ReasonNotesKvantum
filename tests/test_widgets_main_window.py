from pathlib import Path
from tempfile import TemporaryDirectory
import os
import unittest
from uuid import UUID

from PySide6.QtCore import QCoreApplication, QPoint, QSettings, Qt
from PySide6.QtGui import QImage
from PySide6.QtTest import QTest
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QProxyStyle,
    QSplitter,
)

from reasonnotes_app.presenter import NotePresenter
from reasonnotes_app.service import NoteService
from reasonnotes_sync.repository import Repository
from reasonnotes_widgets.bootstrap import create_application
from reasonnotes_widgets.controller import WidgetsController


class WidgetsMainWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls.qt = QApplication.instance() or create_application(
            ["reasonnotes-widgets-window-test"]
        )

    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        base = Path(self.temporary.name)
        self.repository = Repository.open(
            base / "repository", local_device="linux", target_device="android"
        )
        self.service = NoteService(self.repository, origin_device="linux")
        self.settings = QSettings(str(base / "candidate.ini"), QSettings.IniFormat)

    def make_window(self):
        from reasonnotes_widgets.main_window import ReasonNotesMainWindow

        controller = WidgetsController(NotePresenter(self.service))
        window = ReasonNotesMainWindow(controller, settings=self.settings)
        self.addCleanup(window.close)
        window.resize(1400, 850)
        window.show()
        window.activateWindow()
        QCoreApplication.processEvents()
        return window, controller

    def test_native_splitter_sidebar_and_centered_writing_column(self):
        window, _ = self.make_window()

        self.assertIsInstance(window, QMainWindow)
        self.assertIsInstance(window.main_splitter, QSplitter)
        self.assertEqual(window.main_splitter.orientation(), Qt.Orientation.Horizontal)
        self.assertGreaterEqual(window.sidebar.minimumWidth(), 240)
        self.assertEqual(window.editor.writing_column.maximumWidth(), 920)
        self.assertGreaterEqual(window.main_splitter.sizes()[0], 285)
        self.assertLessEqual(window.main_splitter.sizes()[0], 315)
        style_chain = [window.style()]
        while isinstance(style_chain[-1], QProxyStyle):
            style_chain.append(style_chain[-1].baseStyle())
        self.assertEqual(style_chain[-1].objectName().casefold(), "kvantum")
        self.assertEqual(
            window.sidebar.brand_reason.text() + window.sidebar.brand_notes.text(),
            "ReasonNotes",
        )

    def test_writing_column_uses_available_space_before_centering_at_cap(self):
        window, _ = self.make_window()
        window.resize(1024, 800)
        QCoreApplication.processEvents()

        self.assertGreaterEqual(window.editor.writing_column.width(), 590)
        self.assertLessEqual(window.editor.writing_column.width(), 920)

    def test_blank_startup_is_editable_focused_and_unpersisted(self):
        window, controller = self.make_window()
        window.editor.body_editor.setFocus()
        QCoreApplication.processEvents()

        self.assertTrue(window.editor.body_editor.hasFocus())
        self.assertTrue(window.editor.body_editor.isEnabled())
        self.assertEqual(controller.note_model.rowCount(), 0)
        self.assertEqual(tuple(self.repository.revisions()), ())

    def test_title_and_body_autosave_after_typing_pause(self):
        window, controller = self.make_window()
        window.editor.title_editor.setFocus()
        QTest.keyClicks(window.editor.title_editor, "Native title")
        window.editor.body_editor.setPlainText("Markdown *body*")

        self.assertTrue(controller.presenter.dirty)
        QTest.qWait(560)

        self.assertFalse(controller.presenter.dirty)
        self.assertIsNotNone(controller.active_note_id)
        saved = self.service.open_note(UUID(controller.active_note_id))
        self.assertEqual(saved, "# Native title\n\nMarkdown *body*")

    def test_autosave_preserves_caret_selection_and_undo(self):
        window, _ = self.make_window()
        body = window.editor.body_editor
        body.setFocus()
        QTest.keyClicks(body, "abcdef")
        cursor = body.textCursor()
        cursor.setPosition(2)
        cursor.setPosition(4, cursor.MoveMode.KeepAnchor)
        body.setTextCursor(cursor)
        self.assertTrue(body.document().isUndoAvailable())

        QTest.qWait(560)

        cursor = body.textCursor()
        self.assertEqual((cursor.selectionStart(), cursor.selectionEnd()), (2, 4))
        self.assertTrue(body.document().isUndoAvailable())

    def test_switching_notes_flushes_exact_draft(self):
        first = self.service.create_note("# First\n\nOld")
        second = self.service.create_note("# Second\n\nOther")
        window, controller = self.make_window()
        self.assertTrue(controller.select_note(str(first)))
        window.refresh_from_controller()
        window.editor.body_editor.setPlainText("Unsaved switch draft")

        row = next(
            index
            for index in range(controller.note_model.rowCount())
            if controller.note_model.note_id_at(index) == str(second)
        )
        window.activate_note(controller.note_model.index(row, 0))

        self.assertEqual(self.service.open_note(first), "# First\n\nUnsaved switch draft")
        self.assertEqual(controller.active_note_id, str(second))

    def test_shortcuts_create_save_and_focus_search(self):
        window, controller = self.make_window()
        QTest.keyClick(window, Qt.Key.Key_F, Qt.KeyboardModifier.ControlModifier)
        self.assertTrue(window.sidebar.search_field.hasFocus())

        QTest.keyClick(window, Qt.Key.Key_N, Qt.KeyboardModifier.ControlModifier)
        self.assertIsNotNone(controller.active_note_id)
        window.editor.body_editor.setPlainText("Shortcut body")
        QTest.keyClick(window, Qt.Key.Key_S, Qt.KeyboardModifier.ControlModifier)

        self.assertFalse(controller.presenter.dirty)
        self.assertIn("Shortcut body", self.service.open_note(UUID(controller.active_note_id)))

    def test_splitter_width_persists_across_window_instances(self):
        first, _ = self.make_window()
        first.main_splitter.setSizes([372, 1028])
        first.save_ui_state()
        first.close()

        second, _ = self.make_window()

        self.assertGreaterEqual(second.main_splitter.sizes()[0], 365)
        self.assertLessEqual(second.main_splitter.sizes()[0], 379)

    def test_sidebar_splitter_handle_is_native_and_still_resizable(self):
        window, _ = self.make_window()

        # The boundary handle between sidebar widget 0 and page-stack widget 1.
        handle = window.main_splitter.handle(1)
        self.assertIsNotNone(handle)
        self.assertGreater(handle.width(), 0)
        self.assertGreater(handle.height(), 0)
        self.assertEqual(handle.palette().resolveMask(), 0)
        self.assertIs(handle.style(), window.main_splitter.style())

        # The default hit target stays draggable: synthetic drag events are
        # delivered directly to the boundary handle in handle-local
        # coordinates and grow the sidebar by roughly the drag distance.
        grab = QPoint(
            max(1, handle.width() // 2), min(300, max(1, handle.height() - 1))
        )
        before = window.main_splitter.sizes()[0]
        QTest.mousePress(handle, Qt.MouseButton.LeftButton, pos=grab)
        QCoreApplication.processEvents()
        drag_end = grab + QPoint(42, 0)
        QTest.mouseMove(handle, drag_end)
        QCoreApplication.processEvents()
        QTest.mouseRelease(handle, Qt.MouseButton.LeftButton, pos=drag_end)
        QCoreApplication.processEvents()
        self.assertGreaterEqual(window.main_splitter.sizes()[0], before + 30)

    def test_sidebar_splitter_stays_style_owned_while_hovered(self):
        window, _ = self.make_window()
        handle = window.main_splitter.handle(1)
        self.assertIsNotNone(handle)

        hover_pos = handle.mapTo(window, QPoint(handle.width() // 2, 300))
        away_pos = window.main_splitter.mapTo(window, QPoint(100, 300))

        QTest.mouseMove(window, hover_pos)
        QCoreApplication.processEvents()
        self.assertTrue(handle.underMouse())
        self.assertEqual(handle.palette().resolveMask(), 0)
        self.assertIs(handle.style(), window.main_splitter.style())

        QTest.mouseMove(window, away_pos)
        QCoreApplication.processEvents()
        self.assertFalse(handle.underMouse())
        self.assertEqual(handle.palette().resolveMask(), 0)


if __name__ == "__main__":
    unittest.main()
