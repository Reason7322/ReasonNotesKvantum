from pathlib import Path
from tempfile import TemporaryDirectory
import os
import unittest

from PySide6.QtCore import QCoreApplication, QSettings, Qt
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QSizePolicy,
    QToolButton,
)

from reasonnotes_app.presenter import NotePresenter
from reasonnotes_app.service import NoteService
from reasonnotes_sync.repository import Repository
from reasonnotes_widgets.bootstrap import create_application
from reasonnotes_widgets.controller import WidgetsController


class WidgetsVisualPolishTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls.qt = QApplication.instance() or create_application(
            ["reasonnotes-visual-polish-test"]
        )

    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        base = Path(self.temporary.name)
        repository = Repository.open(
            base / "repository", local_device="linux", target_device="android"
        )
        service = NoteService(repository, origin_device="linux")
        controller = WidgetsController(NotePresenter(service))
        settings = QSettings(str(base / "candidate.ini"), QSettings.IniFormat)
        from reasonnotes_widgets.main_window import ReasonNotesMainWindow

        self.window = ReasonNotesMainWindow(
            controller,
            settings=settings,
            deletion_pairing=("127.0.0.1", 28452, "pairing-key"),
        )
        self.addCleanup(self.window.close)
        self.window.resize(1400, 850)
        self.window.show()
        QCoreApplication.processEvents()

    def assert_transparent_base(self, widget):
        self.assertEqual(
            widget.palette().brush(QPalette.ColorRole.Base).color().alpha(), 0
        )

    def test_writing_search_and_list_surfaces_reveal_kvantum_window_material(self):
        line_edits = (
            self.window.sidebar.search_field,
            self.window.editor.title_editor,
            self.window.settings_page.purge_address,
            self.window.settings_page.purge_key,
            self.window.sync_panel.search_field,
        )
        for field in line_edits:
            with self.subTest(field=field.objectName()):
                self.assertFalse(field.hasFrame())
                self.assert_transparent_base(field)
                self.assertEqual(field.styleSheet(), "")

        text_views = (self.window.editor.body_editor,)
        item_views = (
            self.window.sidebar.list_view,
            self.window.sync_panel.note_list,
        )
        for view in (*text_views, *item_views):
            with self.subTest(view=view.objectName()):
                self.assertEqual(view.frameShape(), QFrame.Shape.NoFrame)
                self.assert_transparent_base(view.viewport())
                self.assertFalse(view.viewport().autoFillBackground())
                self.assertEqual(view.styleSheet(), "")

    def test_sidebar_actions_are_compact_native_tool_buttons(self):
        for button in (
            self.window.sidebar.new_button,
            self.window.sidebar.save_button,
            self.window.sidebar.sync_button,
            self.window.sidebar.delete_button,
            self.window.sidebar.settings_button,
        ):
            with self.subTest(button=button.text()):
                self.assertIsInstance(button, QToolButton)
                self.assertTrue(button.autoRaise())
                self.assertEqual(
                    button.toolButtonStyle(), Qt.ToolButtonStyle.ToolButtonTextBesideIcon
                )

    def test_settings_uses_compact_navigation_and_bounded_content_column(self):
        page = self.window.settings_page

        self.assertIsInstance(page.back_button, QToolButton)
        self.assertTrue(page.back_button.autoRaise())
        self.assertEqual(
            page.back_button.toolButtonStyle(),
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon,
        )
        self.assertNotEqual(
            page.back_button.sizePolicy().horizontalPolicy(),
            QSizePolicy.Policy.Expanding,
        )
        self.assertLessEqual(page.content_column.maximumWidth(), 720)
        self.assertEqual(page.heading.parentWidget(), page.content_column)


if __name__ == "__main__":
    unittest.main()
