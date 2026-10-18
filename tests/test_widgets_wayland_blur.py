from pathlib import Path
from tempfile import TemporaryDirectory
import os
import unittest

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMainWindow

from reasonnotes_widgets.bootstrap import create_application


class WidgetsWaylandBlurTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls.qt = QApplication.instance() or create_application(["blur-test"])

    def test_prepare_translucent_surface_happens_before_show(self):
        from reasonnotes_widgets.wayland_blur import prepare_translucent_surface

        window = QMainWindow()
        self.addCleanup(window.close)
        self.assertFalse(window.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground))

        prepare_translucent_surface(window, platform_name="wayland")

        self.assertFalse(window.isVisible())
        self.assertTrue(window.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground))
        self.assertFalse(window.autoFillBackground())

    def test_offscreen_attachment_falls_back_to_readable_opaque_window(self):
        from reasonnotes_widgets.wayland_blur import QWidgetBlurController

        with TemporaryDirectory() as folder:
            window = QMainWindow()
            self.addCleanup(window.close)
            controller = QWidgetBlurController(
                Path(folder) / "missing-helper.so"
            )
            controller.attach(window)

            self.assertFalse(controller.active)
            self.assertTrue(window.autoFillBackground())
            self.assertEqual(window.palette().window().color().alpha(), 255)
            controller.close()
            self.assertIsNone(controller.window)

    def test_active_lifecycle_is_idempotent(self):
        from reasonnotes_widgets.wayland_blur import QWidgetBlurController

        controller = QWidgetBlurController()
        changes = []
        controller.active_changed.connect(changes.append)
        controller._set_active(True)
        controller._set_active(True)
        controller._set_active(False)
        self.assertEqual(changes, [True, False])

    def test_native_helper_commits_enable_but_never_qt_surface_teardown(self):
        source = (
            Path(__file__).resolve().parents[1]
            / "linux-app/native/reasonnotes_wayland_blur.c"
        ).read_text()
        cleanup = source[
            source.index("static void free_blur("):
            source.index("void *rn_blur_enable(")
        ]
        enable = source[source.index("void *rn_blur_enable("):]
        self.assertNotIn("wl_surface_commit", cleanup)
        self.assertIn("wl_surface_commit(state->surface)", enable)

    def test_controller_does_not_modify_system_kvantum_configuration(self):
        from reasonnotes_widgets.wayland_blur import QWidgetBlurController

        config = Path.home() / ".config/Kvantum/kvantum.kvconfig"
        before = config.read_bytes() if config.is_file() else None
        controller = QWidgetBlurController(Path("/nonexistent/helper.so"))
        window = QMainWindow()
        controller.attach(window)
        controller.close()
        after = config.read_bytes() if config.is_file() else None
        self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
