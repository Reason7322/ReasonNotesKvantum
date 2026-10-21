from pathlib import Path
from tempfile import TemporaryDirectory
import os
import unittest

from PySide6.QtCore import QCoreApplication, QPoint, QSettings, Qt
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPalette
from PySide6.QtTest import QTest
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QLabel,
    QProxyStyle,
    QSizePolicy,
    QStyle,
    QStyleOptionFrame,
    QStyleOptionViewItem,
    QToolButton,
    QWidget,
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

    def assert_kvantum_style_chain(self, style):
        chain = [style]
        while chain[-1] is not None:
            if not isinstance(chain[-1], QProxyStyle):
                break
            chain.append(chain[-1].baseStyle())
        names = [item.objectName().casefold() for item in chain if item is not None]
        self.assertEqual(names[-1], "kvantum", names)

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

        text_views = ()
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

    def test_note_body_is_one_uniform_opaque_solid_surface(self):
        body = self.window.editor.body_editor
        surface = QColor(44, 53, 57)  # #2C3539
        for group in (
            QPalette.ColorGroup.Active,
            QPalette.ColorGroup.Inactive,
            QPalette.ColorGroup.Disabled,
        ):
            with self.subTest(group=group):
                self.assertEqual(
                    body.palette().color(group, QPalette.ColorRole.Base),
                    surface,
                )
        self.assertEqual(body.frameShape(), QFrame.Shape.NoFrame)

        image = QImage(body.size(), QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(Qt.GlobalColor.transparent)
        body.render(image)
        for x in range(1, image.width() - 1, 9):
            for y in range(1, image.height() - 1, 13):
                with self.subTest(x=x, y=y):
                    self.assertEqual(
                        image.pixelColor(x, y), surface,
                        f"patchy or translucent writing surface at ({x},{y})",
                    )

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
                self.assert_kvantum_style_chain(field.style())
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

    def test_sidebar_icons_are_available(self):
        for button in (
            self.window.sidebar.new_button,
            self.window.sidebar.save_button,
            self.window.sidebar.sync_button,
            self.window.sidebar.delete_button,
            self.window.sidebar.settings_button,
        ):
            with self.subTest(button=button.text()):
                self.assertFalse(button.icon().isNull())

    def test_sidebar_restores_the_original_single_column_action_hierarchy(self):
        sidebar = self.window.sidebar
        self.assertEqual(sidebar.brand_reason.font().pixelSize(), 27)
        self.assertEqual(sidebar.brand_notes.font().pixelSize(), 27)
        self.assertFalse(sidebar.new_button.is_primary)
        self.assertTrue(sidebar.new_button.is_prominent)
        self.assertGreaterEqual(sidebar.new_button.minimumHeight(), 50)
        self.assertTrue(sidebar.new_button.autoRaise())

        secondary = (
            sidebar.save_button,
            sidebar.sync_button,
            sidebar.delete_button,
        )
        for button in secondary:
            with self.subTest(button=button.text()):
                self.assertIsInstance(button, QToolButton)
                self.assertFalse(button.is_primary)
                self.assertTrue(button.autoRaise())
                self.assertGreaterEqual(button.minimumHeight(), 42)
                self.assertGreaterEqual(button.iconSize().width(), 24)

        layout = sidebar.layout()
        indices = [
            layout.indexOf(sidebar.new_button),
            layout.indexOf(sidebar.save_button),
            layout.indexOf(sidebar.sync_button),
            layout.indexOf(sidebar.settings_button),
            layout.indexOf(sidebar.delete_button),
            layout.indexOf(sidebar.search_well),
            layout.indexOf(sidebar.list_view),
            layout.indexOf(sidebar.status_area),
        ]
        self.assertEqual(indices, sorted(indices))
        self.assertEqual(len(indices), len(set(indices)))

    def test_new_note_action_has_no_filled_background(self):
        sidebar = self.window.sidebar

        def render_button(button):
            image = QImage(
                button.size(), QImage.Format.Format_ARGB32_Premultiplied
            )
            image.fill(Qt.GlobalColor.transparent)
            button.render(image)
            return image

        new_note = render_button(sidebar.new_button)
        flat_action = render_button(sidebar.save_button)

        new_sample = QPoint(sidebar.new_button.width() - 8,
                            sidebar.new_button.height() // 2)
        flat_sample = QPoint(sidebar.save_button.width() - 8,
                             sidebar.save_button.height() // 2)
        self.assertEqual(
            new_note.pixelColor(new_sample),
            flat_action.pixelColor(flat_sample),
            "New Note painted a filled button background",
        )

    def test_save_sync_and_settings_use_deterministic_visible_icons(self):
        sidebar = self.window.sidebar
        for button in (
            sidebar.save_button,
            sidebar.sync_button,
            sidebar.settings_button,
        ):
            with self.subTest(button=button.text()):
                self.assertEqual(
                    button.icon().name(),
                    "",
                    "sidebar action still depends on a theme-supplied glyph",
                )
                image = button.icon().pixmap(24, 24).toImage()
                visible_pixels = []
                for x in range(image.width()):
                    for y in range(image.height()):
                        color = image.pixelColor(x, y)
                        if color.alpha() >= 96 and color.lightness() >= 120:
                            visible_pixels.append(color)
                self.assertGreaterEqual(
                    len(visible_pixels),
                    16,
                    "sidebar icon is too dark to read against the rail",
                )

    def test_normal_note_glyph_uses_the_reasonnotes_accent(self):
        icon = self.window.sidebar.list_view.itemDelegate().note_icon
        image = icon.pixmap(22, 22).toImage()
        accent_pixels = 0
        for x in range(image.width()):
            for y in range(image.height()):
                color = image.pixelColor(x, y)
                channels = (color.red(), color.green(), color.blue())
                if color.alpha() >= 96 and max(channels) - min(channels) >= 24:
                    accent_pixels += 1
        self.assertGreaterEqual(
            accent_pixels,
            12,
            "normal notes still use an achromatic generic document glyph",
        )

    def test_sidebar_boundary_has_no_painted_separator(self):
        sidebar = self.window.sidebar
        sidebar.set_material_fill_enabled(False)
        image = QImage(
            sidebar.size(), QImage.Format.Format_ARGB32_Premultiplied
        )
        image.fill(Qt.GlobalColor.transparent)
        sidebar.render(image)

        for y in range(20, sidebar.height() - 20, 23):
            with self.subTest(y=y):
                self.assertEqual(
                    image.pixelColor(sidebar.width() - 1, y),
                    image.pixelColor(sidebar.width() - 2, y),
                    "sidebar rail painted a visible boundary separator",
                )

    def test_secondary_sidebar_actions_never_paint_highlight_containers(self):
        sidebar = self.window.sidebar

        def render_button(button):
            image = QImage(
                button.size(), QImage.Format.Format_ARGB32_Premultiplied
            )
            image.fill(Qt.GlobalColor.transparent)
            button.render(image)
            return image

        for button in (
            sidebar.save_button,
            sidebar.sync_button,
            sidebar.delete_button,
            sidebar.settings_button,
        ):
            with self.subTest(button=button.objectName() or button.text()):
                QTest.mouseMove(
                    self.window, QPoint(self.window.width() - 20, 20)
                )
                QCoreApplication.processEvents()
                resting = render_button(button)
                QTest.mouseMove(
                    button, QPoint(button.width() - 8, button.height() // 2)
                )
                QCoreApplication.processEvents()
                self.assertTrue(button.underMouse())
                hovered = render_button(button)
                sample = QPoint(button.width() - 8, button.height() // 2)
                self.assertEqual(
                    hovered.pixelColor(sample),
                    resting.pixelColor(sample),
                    "secondary action painted a hover background",
                )

        sidebar.settings_button.setChecked(False)
        unchecked = render_button(sidebar.settings_button)
        sidebar.settings_button.setChecked(True)
        QTest.mouseMove(self.window, QPoint(self.window.width() - 20, 20))
        QCoreApplication.processEvents()
        self.assertTrue(sidebar.settings_button.isChecked())
        checked = render_button(sidebar.settings_button)
        sample = QPoint(
            sidebar.settings_button.width() - 8,
            sidebar.settings_button.height() // 2,
        )
        self.assertEqual(
            checked.pixelColor(sample),
            unchecked.pixelColor(sample),
            "checked Settings painted a selected background",
        )

    def test_note_rows_restore_icons_and_comfortable_full_row_navigation(self):
        sidebar = self.window.sidebar
        delegate = sidebar.list_view.itemDelegate()
        self.assertEqual(delegate.__class__.__name__, "NoteItemDelegate")
        self.assertFalse(delegate.note_icon.isNull())
        self.assertFalse(delegate.conflict_icon.isNull())
        self.assertGreaterEqual(delegate.sizeHint(None, None).height(), 56)
        self.assertEqual(sidebar.list_view.iconSize().width(), 22)
        self.assertTrue(sidebar.list_view.hasMouseTracking())

    def test_note_rows_preserve_selection_without_hover_or_selected_fill(self):
        sidebar = self.window.sidebar
        self.window.controller.create_note()
        self.window.refresh_from_controller()
        view = sidebar.list_view
        index = view.model().index(0, 0)
        self.assertTrue(index.isValid())
        view.clearSelection()
        QTest.mouseMove(self.window, QPoint(self.window.width() - 20, 20))
        QCoreApplication.processEvents()
        row = view.visualRect(index)
        sample = QPoint(row.right() - 8, row.center().y())
        resting = QImage(
            view.viewport().size(), QImage.Format.Format_ARGB32_Premultiplied
        )
        resting.fill(Qt.GlobalColor.transparent)
        view.viewport().render(resting)

        view.setCurrentIndex(index)
        QCoreApplication.processEvents()
        self.assertTrue(view.selectionModel().isSelected(index))

        QTest.mouseMove(view.viewport(), row.center())
        QCoreApplication.processEvents()
        self.assertTrue(view.viewport().underMouse())
        highlighted = QImage(
            view.viewport().size(), QImage.Format.Format_ARGB32_Premultiplied
        )
        highlighted.fill(Qt.GlobalColor.transparent)
        view.viewport().render(highlighted)
        self.assertEqual(
            highlighted.pixelColor(sample),
            resting.pixelColor(sample),
            "selected or hovered note row painted a filled rectangle",
        )

        option = QStyleOptionViewItem()
        option.initFrom(view)
        option.state |= QStyle.StateFlag.State_Selected
        view.itemDelegate().initStyleOption(option, index)
        self.assertEqual(option.font.weight(), QFont.Weight.DemiBold)

    def test_editor_title_body_hierarchy_without_header_status_or_rule(self):
        editor = self.window.editor
        # The top-right Local/Phone block is gone from the writing card; its
        # object names must no longer exist anywhere in the page.
        self.assertIsNone(editor.findChild(QWidget, "editorStatusBar"))
        self.assertIsNone(editor.findChild(QLabel, "saveStatus"))
        self.assertIsNone(editor.findChild(QLabel, "deliveryStatus"))
        self.assertEqual(editor.title_editor.font().pixelSize(), 36)
        self.assertEqual(editor.body_editor.font().pixelSize(), 18)
        # Empty-title placeholder is the localized title prompt; the body
        # keeps no placeholder of its own.
        self.assertEqual(editor.title_editor.placeholderText(), "Title")
        self.assertEqual(editor.body_editor.placeholderText(), "")
        layout = editor.writing_column.layout()
        self.assertFalse(hasattr(editor, "title_rule"))
        # The body follows the title directly; no separator widget is present.
        self.assertEqual(
            layout.indexOf(editor.body_editor),
            layout.indexOf(editor.title_editor) + 1,
        )
        editor.set_document(
            "The beginning of a deliberately long title remains visible",
            "Body",
        )
        self.assertEqual(editor.title_editor.cursorPosition(), 0)


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
        # The rejected regression filled the whole editor page with the
        # palette Base brush, producing an opaque charcoal slab.
        self.assertFalse(self.window.editor.autoFillBackground())
        material = self.window.palette().color(QPalette.ColorRole.Base)
        self.assertGreater(material.alpha(), 0)
        self.assertLess(material.alpha(), 255)
        # A translucent window paints the actual material onto otherwise
        # transparent space; it must not leave that space alpha=0.
        canvas = QImage(self.window.size(), QImage.Format.Format_ARGB32_Premultiplied)
        canvas.fill(Qt.GlobalColor.transparent)
        self.window.render(canvas)
        pixel = canvas.pixelColor(self.window.width() - 30, self.window.height() // 2)
        self.assertGreater(pixel.alpha(), 110)
        self.assertLess(pixel.alpha(), 235)
        # The material still belongs to the system palette family; the
        # page/card/rail add separation rather than a solid background.
        self.assertEqual(self.window.editor.writing_column.__class__.__name__, "GlassCard")
        self.assertEqual(self.window.sidebar.__class__.__name__, "NotesSidebar")
        self.assertEqual(self.window.sidebar.search_well.__class__.__name__, "SearchWell")

    def test_window_material_has_no_repeated_quantized_bands(self):
        from reasonnotes_widgets.wayland_blur import prepare_translucent_surface

        self.assertTrue(
            prepare_translucent_surface(self.window, platform_name="wayland")
        )
        canvas = QImage(
            self.window.size(), QImage.Format.Format_ARGB32_Premultiplied
        )
        canvas.fill(Qt.GlobalColor.transparent)
        self.window.render(canvas)

        # This exposed strip contains only the top-level material. The failed
        # implementation quantized a low-contrast window-sized gradient into
        # a sequence of long equal-color runs, visible as rectangular bands.
        y = 10
        start = self.window.sidebar.width() + 20
        colors = [
            canvas.pixelColor(x, y).rgba()
            for x in range(start, self.window.width() - 10)
        ]
        run_lengths = []
        run_start = 0
        for index in range(1, len(colors) + 1):
            if index == len(colors) or colors[index] != colors[run_start]:
                run_lengths.append(index - run_start)
                run_start = index
        long_runs = [length for length in run_lengths if length >= 4]
        self.assertLessEqual(
            len(long_runs),
            1,
            f"quantized material bands: {long_runs[:12]}",
        )


if __name__ == "__main__":
    unittest.main()
