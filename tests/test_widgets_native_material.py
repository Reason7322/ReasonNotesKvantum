from importlib.util import module_from_spec, spec_from_file_location
from inspect import signature
from pathlib import Path
from tempfile import TemporaryDirectory
import os
import unittest
from unittest.mock import patch

from PySide6.QtCore import QCoreApplication, QPoint, QSettings, Qt
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtWidgets import QApplication, QProxyStyle, QStyle, QStyleOption

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

    def test_default_renderer_delegates_all_large_surfaces_to_native_style(self):
        from reasonnotes_widgets.main_window import ReasonNotesMainWindow
        from reasonnotes_widgets.material import GlassCard, NavigationRail, SearchWell

        window = ReasonNotesMainWindow(self.controller, settings=self.settings)
        self.addCleanup(window.close)

        self.assertEqual(window.window_material_mode, "native-kvantum")
        surfaces = [
            window.sidebar,
            *window.findChildren(GlassCard),
            *window.findChildren(SearchWell),
        ]
        self.assertIsInstance(window.sidebar, NavigationRail)
        self.assertGreater(len(surfaces), 4)
        self.assertTrue(all(surface.native_style_enabled for surface in surfaces))

    def test_native_material_children_do_not_stack_widget_primitives(self):
        from reasonnotes_widgets.material import GlassCard, NavigationRail, SearchWell

        class PrimitiveRecordingStyle(QProxyStyle):
            def __init__(self, base_style):
                super().__init__(base_style)
                self.widget_primitive_calls = 0

            def drawPrimitive(self, element, option, painter=None, widget=None):
                if element == QStyle.PrimitiveElement.PE_Widget:
                    self.widget_primitive_calls += 1
                return super().drawPrimitive(element, option, painter, widget)

        for widget_type in (NavigationRail, GlassCard, SearchWell):
            with self.subTest(widget_type=widget_type.__name__):
                baseline = widget_type()
                self.addCleanup(baseline.close)
                baseline.resize(240, 120)
                baseline_style = PrimitiveRecordingStyle(
                    baseline.style().objectName()
                )
                baseline_style.setParent(baseline)
                baseline.setStyle(baseline_style)
                baseline.show()
                QCoreApplication.processEvents()
                self._render_widget_image(baseline, 240, 120)

                widget = widget_type()
                self.addCleanup(widget.close)
                widget.resize(240, 120)
                widget.set_native_style_enabled(True)
                recording_style = PrimitiveRecordingStyle(widget.style().objectName())
                recording_style.setParent(widget)
                widget.setStyle(recording_style)
                widget.show()
                QCoreApplication.processEvents()

                self._render_widget_image(widget, 240, 120)
                self.assertEqual(
                    recording_style.widget_primitive_calls,
                    baseline_style.widget_primitive_calls,
                )

    def test_native_navigation_rail_uses_the_theme_base_brush(self):
        from reasonnotes_widgets.material import NavigationRail

        rail = NavigationRail()
        self.addCleanup(rail.close)
        rail.resize(240, 120)
        rail.set_native_style_enabled(True)
        rail.show()
        QCoreApplication.processEvents()

        image = self._render_widget_image(rail, 240, 120)
        self.assertEqual(
            image.pixelColor(QPoint(120, 60)),
            rail.palette().base().color(),
        )

    def test_application_style_chain_contains_kvantum_leaf(self):
        from reasonnotes_widgets.bootstrap import style_chain_names

        names = style_chain_names(self.qt.style())
        self.assertIn("kvantum", names)
        if names[0] == "qt6ct-style":
            self.assertEqual(names[-1], "kvantum")

    def test_missing_kvantum_fails_without_installing_a_fallback_palette(self):
        from reasonnotes_widgets.bootstrap import ensure_kvantum_style

        class FakeStyle:
            def objectName(self):
                return "fusion"

        class FakeApplication:
            def __init__(self):
                self.palette_was_set = False

            def style(self):
                return FakeStyle()

            def setStyle(self, _style):
                raise AssertionError("No style is available to install")

            def setPalette(self, _palette):
                self.palette_was_set = True

        application = FakeApplication()
        with patch("reasonnotes_widgets.bootstrap.QStyleFactory.create", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "Kvantum style is required"):
                ensure_kvantum_style(application)
        self.assertFalse(application.palette_was_set)

    def test_disabled_card_keeps_rim_while_navigation_rail_is_fully_clear(self):
        from reasonnotes_widgets.material import GlassCard, NavigationRail

        card = GlassCard()
        self.addCleanup(card.close)
        card.resize(240, 120)
        card.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        card.set_material_fill_enabled(False)
        card.show()
        QCoreApplication.processEvents()
        card_image = self._render_widget_image(card, 240, 120)
        self.assertEqual(card_image.pixelColor(QPoint(120, 60)).alpha(), 0)
        self.assertGreater(card_image.pixelColor(QPoint(1, 60)).alpha(), 0)

        rail = NavigationRail()
        self.addCleanup(rail.close)
        rail.resize(240, 120)
        rail.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        rail.set_material_fill_enabled(False)
        rail.show()
        QCoreApplication.processEvents()
        rail_image = self._render_widget_image(rail, 240, 120)
        self.assertEqual(rail_image.pixelColor(QPoint(120, 60)).alpha(), 0)
        self.assertEqual(rail_image.pixelColor(QPoint(239, 60)).alpha(), 0)

    def _render_widget_image(self, widget, width, height):
        image = QImage(width, height, QImage.Format.Format_RGBA8888)
        image.fill(Qt.GlobalColor.transparent)
        widget.render(image)
        return image

    @staticmethod
    def _kitty_card():
        from reasonnotes_widgets.material import GlassCard

        card = GlassCard()
        card.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        card.set_material_fill_enabled(False)  # Kitty-equivalent presentation.
        card.resize(480, 320)
        card.show()
        QCoreApplication.processEvents()
        return card

    def test_kitty_sheet_pixels_unchanged_in_unobstructed_regions(self):
        from reasonnotes_widgets.main_window import ReasonNotesMainWindow

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

        # Points outside every painted child (above the writing column,
        # below it, and in its right margin) must remain the measured sheet.
        for point in (QPoint(740, 10), QPoint(740, 790), QPoint(1260, 10)):
            with self.subTest(point=point):
                self.assertEqual(actual.pixelColor(point), QColor(28, 33, 33, 209))

    def test_kitty_card_interior_stays_free_of_pane_fill(self):
        from reasonnotes_widgets.material import GlassCard

        card = self._kitty_card()
        self.addCleanup(card.close)
        image = self._render_widget_image(card, 480, 320)

        # A grid across the card interior (more than two rim widths inside
        # every boundary) must remain fully transparent: no pane-sized fill.
        for x in range(30, 451, 10):
            for y in range(26, 295, 10):
                with self.subTest(x=x, y=y):
                    self.assertEqual(image.pixelColor(QPoint(x, y)).alpha(), 0)

    def test_kitty_card_edge_treatment_is_visible_and_localized(self):
        from reasonnotes_widgets.material import GlassCard

        card = self._kitty_card()
        self.addCleanup(card.close)
        image = self._render_widget_image(card, 480, 320)

        def alpha(point):
            return image.pixelColor(QPoint(*point)).alpha()

        # Visible rim pixels a few pixels inside each boundary. The top edge
        # is the strongest because the existing reflection line overlaps it.
        visible = ((240, 1, 80), (240, 4, 35), (3, 160, 35), (475, 160, 35),
                  (240, 315, 35))
        for x, y, minimum in visible:
            with self.subTest(x=x, y=y):
                self.assertGreaterEqual(alpha((x, y)), minimum)

        # The treatment must stay localized: beyond the rim fade width the
        # surface is transparent again.
        clear = ((240, 16), (18, 160), (463, 160), (240, 304))
        for point in clear:
            with self.subTest(point=point):
                self.assertEqual(alpha(point), 0)

    def test_default_card_still_paints_gradient_fill(self):
        from reasonnotes_widgets.material import GlassCard

        card = GlassCard()  # material fill stays enabled by default.
        card.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        card.resize(480, 320)
        card.show()
        QCoreApplication.processEvents()
        self.addCleanup(card.close)
        image = self._render_widget_image(card, 480, 320)

        center = image.pixelColor(QPoint(240, 160)).alpha()
        top_mid = image.pixelColor(QPoint(240, 60)).alpha()
        bottom_mid = image.pixelColor(QPoint(240, 260)).alpha()

        self.assertGreater(center, 55)
        self.assertLess(center, 95)
        self.assertGreater(top_mid, bottom_mid)

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
        defaults = candidate_parser.parse_args([])
        self.assertFalse(defaults.kitty_window_material)
        self.assertFalse(defaults.native_window_material)
        with self.assertRaises(SystemExit):
            candidate_parser.parse_args(
                ["--native-window-material", "--kitty-window-material"]
            )


if __name__ == "__main__":
    unittest.main()
