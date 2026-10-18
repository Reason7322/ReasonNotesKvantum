from pathlib import Path
from tempfile import TemporaryDirectory
import os
import unittest

from PySide6.QtCore import QCoreApplication, QPoint, QSettings, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDockWidget

from reasonnotes_app.presenter import NotePresenter
from reasonnotes_app.service import NoteService
from reasonnotes_sync.repository import Repository
from reasonnotes_sync.sync import SyncReport
from reasonnotes_widgets.bootstrap import create_application
from reasonnotes_widgets.controller import WidgetsController


class CapturingPool:
    def __init__(self):
        self.workers = []

    def start(self, worker):
        self.workers.append(worker)

    def run_next(self):
        self.workers.pop(0).run()
        QCoreApplication.processEvents()


class WidgetsSyncPanelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls.qt = QApplication.instance() or create_application(["sync-panel-test"])

    def test_panel_modes_selection_preview_and_async_completion(self):
        from reasonnotes_widgets.main_window import ReasonNotesMainWindow

        with TemporaryDirectory() as folder:
            base = Path(folder)
            repository = Repository.open(
                base / "repo", local_device="linux", target_device="android"
            )
            service = NoteService(repository, origin_device="linux")
            service.create_note("# *Markdown title*\n\nLine one\nLine two")
            calls = []
            report = SyncReport((), (), (), (), (), (), (), ())

            def sync_runner(selection):
                calls.append(selection)
                return report

            pool = CapturingPool()
            controller = WidgetsController(
                NotePresenter(service, sync_runner), thread_pool=pool
            )
            settings = QSettings(str(base / "ui.ini"), QSettings.IniFormat)
            window = ReasonNotesMainWindow(controller, settings=settings)
            self.addCleanup(window.close)
            window.show()

            window.open_sync_panel()
            panel = window.sync_panel

            self.assertIsInstance(panel, QDockWidget)
            self.assertTrue(panel.isVisible())
            self.assertTrue(panel.all_button.isChecked())
            self.assertTrue(panel.start_button.isEnabled())
            self.assertEqual(calls, [])
            preview = controller.sync_model.row(0)["preview"]
            self.assertNotIn("#", preview)
            self.assertNotIn("*", preview)
            self.assertNotIn("\n", preview)

            panel.selected_button.click()
            self.assertFalse(panel.start_button.isEnabled())
            index = controller.sync_model.index(0, 0)
            panel.note_list.setCurrentIndex(index)
            panel.note_list.setFocus()
            QTest.keyClick(panel.note_list, Qt.Key.Key_Space)
            QCoreApplication.processEvents()
            self.assertEqual(len(controller.sync_selected_ids), 1)

            indicator = QPoint(
                panel.note_list.visualRect(index).left() + 8,
                panel.note_list.visualRect(index).center().y(),
            )
            QTest.mouseClick(
                panel.note_list.viewport(), Qt.MouseButton.LeftButton,
                pos=indicator,
            )
            QCoreApplication.processEvents()
            self.assertEqual(len(controller.sync_selected_ids), 0)
            QTest.keyClick(panel.note_list, Qt.Key.Key_Space)
            QCoreApplication.processEvents()
            self.assertEqual(len(controller.sync_selected_ids), 1)
            self.assertTrue(panel.start_button.isEnabled())

            panel.start_button.click()
            self.assertEqual(controller.presenter.sync_state, "Running")
            self.assertEqual(calls, [])
            pool.run_next()

            self.assertEqual(controller.presenter.sync_state, "Completed")
            self.assertEqual(len(calls), 1)
            self.assertEqual(len(calls[0]), 1)


if __name__ == "__main__":
    unittest.main()
