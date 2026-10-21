from pathlib import Path
from tempfile import TemporaryDirectory
import os
import unittest

from PySide6.QtCore import QCoreApplication, QPoint, QSettings, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDockWidget, QProgressBar

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
            revision_id = "a" * 64
            report = SyncReport(
                (), (revision_id,), (), (), (revision_id,), (), (), ()
            )

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
            self.assertIsInstance(panel.progress_bar, QProgressBar)
            self.assertFalse(panel.progress_bar.isVisible())
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
            self.assertTrue(panel.progress_bar.isVisible())
            self.assertEqual(
                (panel.progress_bar.minimum(), panel.progress_bar.maximum()),
                (0, 0),
            )
            self.assertEqual(calls, [])
            pool.run_next()

            self.assertEqual(controller.presenter.sync_state, "Completed")
            self.assertFalse(panel.progress_bar.isVisible())
            self.assertEqual(len(calls), 1)
            self.assertEqual(len(calls[0]), 1)

    def test_redesigned_drawer_keeps_scope_summary_status_and_action_connected(self):
        """Catch a return to the disconnected footer and empty all-notes body."""
        from reasonnotes_widgets.main_window import ReasonNotesMainWindow

        with TemporaryDirectory() as folder:
            base = Path(folder)
            repository = Repository.open(
                base / "repo", local_device="linux", target_device="android"
            )
            service = NoteService(repository, origin_device="linux")
            service.create_note("Reference note\n\nVisible preview")
            pool = CapturingPool()
            revision_id = "b" * 64
            controller = WidgetsController(
                NotePresenter(
                    service,
                    lambda _selection: SyncReport(
                        (), (revision_id,), (), (), (revision_id,), (), (), ()
                    ),
                ),
                thread_pool=pool,
            )
            settings = QSettings(str(base / "ui.ini"), QSettings.IniFormat)
            window = ReasonNotesMainWindow(controller, settings=settings)
            self.addCleanup(window.close)
            window.resize(1280, 860)
            window.show()
            window.open_sync_panel()
            QCoreApplication.processEvents()
            panel = window.sync_panel

            self.assertTrue(hasattr(panel, "heading"))
            self.assertEqual(panel.heading.text(), "Synchronize notes")
            self.assertTrue(panel.close_button.isVisible())
            self.assertEqual(panel.close_button.text(), "×")
            self.assertEqual(
                panel.close_button.toolButtonStyle(),
                Qt.ToolButtonStyle.ToolButtonTextOnly,
            )
            self.assertTrue(panel.all_button.isChecked())
            self.assertTrue(panel.all_summary_card.isVisible())
            self.assertFalse(panel.selection_section.isVisible())
            self.assertTrue(panel.action_card.isVisible())
            self.assertEqual(panel.start_button.text(), "Sync all notes")
            self.assertTrue(hasattr(panel.start_button, "is_primary"))
            self.assertTrue(panel.start_button.is_primary)
            self.assertLessEqual(
                panel.action_card.geometry().top()
                - panel.all_summary_card.geometry().bottom(),
                24,
            )

            panel.selected_button.click()
            QCoreApplication.processEvents()
            self.assertFalse(panel.all_summary_card.isVisible())
            self.assertTrue(panel.selection_section.isVisible())
            self.assertEqual(panel.start_button.text(), "Sync selected (0)")
            self.assertFalse(panel.start_button.isEnabled())
            self.assertGreaterEqual(panel.note_list.itemDelegate().sizeHint(None, None).height(), 72)

            controller.select_all_sync_notes()
            QCoreApplication.processEvents()
            self.assertEqual(panel.start_button.text(), "Sync selected (1)")
            self.assertTrue(panel.start_button.isEnabled())

            panel.start_button.click()
            QCoreApplication.processEvents()
            self.assertIn("Running", panel.status_label.text())
            self.assertTrue(panel.progress_bar.isVisible())
            self.assertFalse(panel.start_button.isEnabled())
            pool.run_next()
            self.assertIn("Completed", panel.status_label.text())
            self.assertFalse(panel.progress_bar.isVisible())

    def test_progress_hides_after_worker_failure(self):
        from reasonnotes_widgets.main_window import ReasonNotesMainWindow

        with TemporaryDirectory() as folder:
            base = Path(folder)
            repository = Repository.open(
                base / "repo", local_device="linux", target_device="android"
            )
            service = NoteService(repository, origin_device="linux")
            service.create_note("Failure fixture")

            def fail_sync(_selection):
                raise RuntimeError("phone disconnected")

            pool = CapturingPool()
            controller = WidgetsController(
                NotePresenter(service, fail_sync), thread_pool=pool
            )
            window = ReasonNotesMainWindow(
                controller,
                settings=QSettings(str(base / "ui.ini"), QSettings.IniFormat),
            )
            self.addCleanup(window.close)
            window.show()
            window.open_sync_panel()
            panel = window.sync_panel

            panel.start_button.click()
            self.assertTrue(panel.progress_bar.isVisible())
            pool.run_next()

            self.assertEqual(controller.presenter.sync_state, "Error")
            self.assertFalse(panel.progress_bar.isVisible())
            self.assertIn("phone disconnected", panel.status_label.text())


if __name__ == "__main__":
    unittest.main()
