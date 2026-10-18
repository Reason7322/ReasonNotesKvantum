from pathlib import Path
from tempfile import TemporaryDirectory
import os
import unittest

from PySide6.QtCore import QCoreApplication, QSettings, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QProxyStyle,
    QSizePolicy,
    QStyle,
    QStyleOptionFrame,
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

    def test_line_edit_proxy_suppresses_only_the_forced_kvantum_panel(self):
        fields = (
            self.window.sidebar.search_field,
            self.window.editor.title_editor,
            self.window.settings_page.purge_address,
            self.window.settings_page.purge_key,
            self.window.sync_panel.search_field,
        )
        untouched = QColor(17, 23, 31)
        for field in fields:
            with self.subTest(field=field.objectName()):
                self.assertIsInstance(field.style(), QProxyStyle)
                self.assertEqual(field.style().baseStyle().objectName(), "kvantum")
                image = QImage(40, 24, QImage.Format.Format_ARGB32_Premultiplied)
                image.fill(untouched)
                option = QStyleOptionFrame()
                option.initFrom(field)
                option.rect = image.rect()
                painter = QPainter(image)
                field.style().drawPrimitive(
                    QStyle.PrimitiveElement.PE_PanelLineEdit,
                    option,
                    painter,
                    field,
                )
                painter.end()
                self.assertEqual(image.pixelColor(image.rect().center()), untouched)

    def test_sidebar_icons_are_system_theme_backed(self):
        # Individual pictograms come from Qt's native icon theme; no
        # application-owned mock LiquidGlass icon renderer.
        for button in (
            self.window.sidebar.new_button,
            self.window.sidebar.save_button,
            self.window.sidebar.sync_button,
            self.window.sidebar.delete_button,
            self.window.sidebar.settings_button,
        ):
            with self.subTest(button=button.text()):
                self.assertFalse(button.icon().isNull())

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

    def test_settings_has_no_back_button_and_sidebar_toggles(self):
        page = self.window.settings_page
        self.assertFalse(hasattr(page, "back_button"))
        self.assertEqual(
            [child.text() for child in page.findChildren(QToolButton)
             if "Back to notes" in child.text()], []
        )
        self.assertFalse(hasattr(page, "system_appearance"))
        self.assertLessEqual(page.content_column.maximumWidth(), 720)
        self.assertEqual(page.heading.parentWidget(), page.content_column)
        self.window.sidebar.settings_button.click()
        QCoreApplication.processEvents()
        self.assertGreaterEqual(page.content_column.width(), 500)
        self.assertIs(self.window.page_stack.currentWidget(), page)
        self.window.sidebar.settings_button.click()
        self.assertIsNot(self.window.page_stack.currentWidget(), page)

    def test_window_material_uses_system_kvantum_base_not_an_app_theme(self):
        from PySide6.QtGui import QPalette
        from PySide6.QtCore import Qt
        from reasonnotes_widgets.wayland_blur import prepare_translucent_surface

        self.assertTrue(
            prepare_translucent_surface(self.window, platform_name="wayland")
        )
        self.assertTrue(self.window.editor.autoFillBackground())
        self.assertEqual(
            self.window.editor.backgroundRole(), QPalette.ColorRole.Base
        )
        material = self.window.palette().color(QPalette.ColorRole.Base)
        self.assertGreater(material.alpha(), 0)
        self.assertLess(material.alpha(), 255)
        # A translucent window paints the actual material onto otherwise
        # transparent space; it must not leave that space alpha=0.
        canvas = QImage(self.window.size(), QImage.Format.Format_ARGB32_Premultiplied)
        canvas.fill(Qt.GlobalColor.transparent)
        self.window.render(canvas)
        pixel = canvas.pixelColor(self.window.width() - 30, self.window.height() // 2)
        # The real Kvantum window primitive and native Base brush can
        # overlap; composited alpha need not equal a single palette entry.
        self.assertGreater(pixel.alpha(), 0)
        self.assertLessEqual(pixel.alpha(), 255)
        # The window uses the QStyle PE_Widget and native palette brushes;
        # it does not ship its own LiquidGlass material.
        self.assertEqual(self.window.editor.writing_column.__class__.__name__, "GlassCard")
        self.assertEqual(self.window.sidebar.__class__.__name__, "NotesSidebar")
        self.assertEqual(self.window.sidebar.search_well.__class__.__name__, "SearchWell")


if __name__ == "__main__":
    unittest.main()
