from importlib.util import module_from_spec, spec_from_file_location
from inspect import signature
from pathlib import Path
from tempfile import TemporaryDirectory
import os
import unittest

from PySide6.QtCore import QCoreApplication, QPoint, QSettings, Qt
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtWidgets import QApplication, QStyle, QStyleOption

from reasonnotes_app.presenter import NotePresenter
from reasonnotes_app.service import NoteService
from reasonnotes_sync.repository import Repository
from reasonnotes_widgets.bootstrap import create_application
from reasonnotes_widgets.controller import WidgetsController
from reasonnotes_widgets.wayland_blur import prepare_translucent_surface


class NativeWindowMaterialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls.qt = QApplication.instance() or create_application(
            ["reasonnotes-native-material-test"]
        )

    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        base = Path(self.temporary.name)
        repository = Repository.open(
            base / "repository", local_device="linux", target_device="android"
        )
        controller = WidgetsController(
            NotePresenter(NoteService(repository, origin_device="linux"))
        )
        self.settings = QSettings(str(base / "candidate.ini"), QSettings.IniFormat)
        self.controller = controller

    def test_native_variant_delegates_top_level_sheet_to_kvantum(self):
        from reasonnotes_widgets.main_window import ReasonNotesMainWindow

        self.assertIn("native_window_material", signature(ReasonNotesMainWindow).parameters)
        window = ReasonNotesMainWindow(
            self.controller,
            settings=self.settings,
            native_window_material=True,
        )
        self.addCleanup(window.close)
        window.resize(1280, 800)
        self.assertTrue(prepare_translucent_surface(window, platform_name="wayland"))
        window.show()
        QCoreApplication.processEvents()

        actual = QImage(window.size(), QImage.Format.Format_ARGB32_Premultiplied)
        actual.fill(Qt.GlobalColor.transparent)
        window.render(actual)

        expected = QImage(window.size(), QImage.Format.Format_ARGB32_Premultiplied)
        expected.fill(Qt.GlobalColor.transparent)
        option = QStyleOption()
        option.initFrom(window)
        option.rect = expected.rect()
        painter = QPainter(expected)
        window.style().drawPrimitive(
            QStyle.PrimitiveElement.PE_Widget,
            option,
            painter,
            window,
        )
        painter.end()

        exposed = window.rect().topRight() + QPoint(-20, 10)
        self.assertEqual(actual.pixelColor(exposed), expected.pixelColor(exposed))
        self.assertEqual(window.window_material_mode, "native-kvantum")

    def test_entrypoint_exposes_source_only_native_material_switch(self):
        project = Path(__file__).resolve().parents[1]
        entrypoint = project / "linux-app/reasonnotes_widgets.py"
        spec = spec_from_file_location("reasonnotes_widgets_entrypoint", entrypoint)
        module = module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)

        candidate_parser = module.parser()
        self.assertIn(
            "--native-window-material", candidate_parser._option_string_actions
        )
        options = candidate_parser.parse_args(["--native-window-material"])

        self.assertTrue(options.native_window_material)

    def test_kitty_variant_uses_measured_sheet_and_bypasses_pane_fills(self):
        from reasonnotes_widgets.main_window import ReasonNotesMainWindow

        self.assertIn("kitty_window_material", signature(ReasonNotesMainWindow).parameters)
        window = ReasonNotesMainWindow(
            self.controller,
            settings=self.settings,
            kitty_window_material=True,
        )
        self.addCleanup(window.close)
        window.resize(1280, 800)
        self.assertTrue(prepare_translucent_surface(window, platform_name="wayland"))
        window.show()
        QCoreApplication.processEvents()

        actual = QImage(window.size(), QImage.Format.Format_RGBA8888)
        actual.fill(Qt.GlobalColor.transparent)
        window.render(actual)

        exposed = window.rect().topRight() + QPoint(-20, 10)
        self.assertEqual(actual.pixelColor(exposed), QColor(28, 33, 33, 209))
        self.assertEqual(window.window_material_mode, "kitty-equivalent")
        self.assertFalse(window.sidebar.material_fill_enabled)
        self.assertFalse(window.editor.writing_column.material_fill_enabled)
        self.assertFalse(window.settings_page.language_card.material_fill_enabled)
        self.assertFalse(window.settings_page.pairing_card.material_fill_enabled)

    def test_default_renderer_keeps_existing_pane_materials(self):
        from reasonnotes_widgets.main_window import ReasonNotesMainWindow

        window = ReasonNotesMainWindow(self.controller, settings=self.settings)
        self.addCleanup(window.close)

        self.assertEqual(window.window_material_mode, "reasonnotes-custom")
        self.assertTrue(window.sidebar.material_fill_enabled)
        self.assertTrue(window.editor.writing_column.material_fill_enabled)
        self.assertTrue(window.settings_page.language_card.material_fill_enabled)

    def test_disabled_pane_materials_keep_edges_but_leave_centers_clear(self):
        from reasonnotes_widgets.material import GlassCard, NavigationRail

        cases = (
            (GlassCard, QPoint(120, 60), QPoint(1, 60)),
            (NavigationRail, QPoint(120, 60), QPoint(239, 60)),
        )
        for widget_type, center, edge in cases:
            with self.subTest(widget=widget_type.__name__):
                widget = widget_type()
                self.addCleanup(widget.close)
                widget.resize(240, 120)
                widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
                widget.set_material_fill_enabled(False)
                widget.show()
                QCoreApplication.processEvents()
                image = QImage(240, 120, QImage.Format.Format_RGBA8888)
                image.fill(Qt.GlobalColor.transparent)
                widget.render(image)

                self.assertEqual(image.pixelColor(center).alpha(), 0)
                self.assertGreater(image.pixelColor(edge).alpha(), 0)

    def test_entrypoint_exposes_mutually_exclusive_kitty_material_switch(self):
        project = Path(__file__).resolve().parents[1]
        entrypoint = project / "linux-app/reasonnotes_widgets.py"
        spec = spec_from_file_location("reasonnotes_widgets_kitty_entrypoint", entrypoint)
        module = module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)

        candidate_parser = module.parser()
        self.assertIn(
            "--kitty-window-material", candidate_parser._option_string_actions
        )
        options = candidate_parser.parse_args(["--kitty-window-material"])
        self.assertTrue(options.kitty_window_material)
        self.assertFalse(options.native_window_material)
        with self.assertRaises(SystemExit):
            candidate_parser.parse_args(
                ["--native-window-material", "--kitty-window-material"]
            )


if __name__ == "__main__":
    unittest.main()
