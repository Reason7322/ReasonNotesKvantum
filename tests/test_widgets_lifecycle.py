from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import os
import subprocess
import sys
import unittest
from uuid import UUID

from PySide6.QtCore import QCoreApplication, QSettings, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from reasonnotes_app.presenter import NotePresenter
from reasonnotes_app.service import NoteService
from reasonnotes_sync.repository import Repository
from reasonnotes_widgets.bootstrap import create_application
from reasonnotes_widgets.controller import WidgetsController


class Pool:
    def __init__(self): self.workers = []
    def start(self, worker): self.workers.append(worker)
    def run_next(self):
        self.workers.pop(0).run()
        QCoreApplication.processEvents()


class Relay:
    def __init__(self):
        self.changes = 0
        self.started = False
        self.stopped = False
    def start(self): self.started = True
    def stop(self): self.stopped = True


class WidgetsLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls.qt = QApplication.instance() or create_application(["lifecycle-test"])

    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        base = Path(self.temporary.name)
        self.repository = Repository.open(base / "repo")
        self.service = NoteService(self.repository, origin_device="linux")
        self.pool = Pool()
        self.controller = WidgetsController(
            NotePresenter(self.service, lambda _selection: (_ for _ in ()).throw(
                AssertionError("F5 must not upload")
            )),
            thread_pool=self.pool,
        )
        from reasonnotes_widgets.main_window import ReasonNotesMainWindow
        self.window = ReasonNotesMainWindow(
            self.controller,
            settings=QSettings(str(base / "ui.ini"), QSettings.IniFormat),
        )
        self.addCleanup(self.window.close)

    def test_f5_queues_one_followup_and_preserves_dirty_draft_without_upload(self):
        note_id = str(self.service.create_note("# Note\n\nSaved"))
        self.controller.presenter.refresh()
        self.controller.refresh_models()
        self.controller.select_note(note_id)
        self.controller.edit_content("Exact dirty draft")
        scans = []

        def scan():
            scans.append(True)
            return SimpleNamespace(imported=(), confirmed=(), errors=())

        self.controller.configure_incoming_scan(scan)
        self.window.show()
        self.window.activateWindow()
        self.window.editor.body_editor.setFocus()
        QCoreApplication.processEvents()
        QTest.keyClick(self.window.editor.body_editor, Qt.Key.Key_F5)
        QTest.keyClick(self.window.editor.body_editor, Qt.Key.Key_F5)
        self.assertEqual(len(self.pool.workers), 1)
        self.pool.run_next()
        self.assertEqual(len(self.pool.workers), 1)
        self.pool.run_next()

        self.assertEqual(len(scans), 2)
        self.assertTrue(self.controller.presenter.dirty)
        self.assertEqual(self.controller.current_content, "Exact dirty draft")

    def test_deferred_startup_scan_window_first_and_teardown(self):
        from reasonnotes_widgets.runtime import ApplicationRuntime

        self.controller.configure_incoming_scan(
            lambda: SimpleNamespace(imported=(), confirmed=(), errors=())
        )
        relay = Relay()
        runtime = ApplicationRuntime(
            self.repository, self.controller, relay=relay
        )
        self.window.show()
        runtime.start(auto_receive=True)
        self.assertTrue(self.window.isVisible())
        QCoreApplication.processEvents()
        self.assertEqual(len(self.pool.workers), 1)
        self.assertTrue(relay.started)

        runtime.stop()

        self.assertTrue(relay.stopped)
        self.assertFalse(runtime.purge_timer.isActive())

    def test_remote_purge_clears_active_note_on_poll(self):
        from reasonnotes_widgets.runtime import ApplicationRuntime

        note_id = str(self.service.create_note("# Purge me"))
        self.controller.presenter.refresh()
        self.controller.select_note(note_id)
        relay = Relay()
        runtime = ApplicationRuntime(self.repository, self.controller, relay=relay)
        runtime.start(auto_receive=False)
        self.repository.purge_note(UUID(note_id))
        relay.changes += 1

        runtime.poll_purge()

        self.assertIsNone(self.controller.active_note_id)
        self.assertEqual(self.controller.note_model.rowCount(), 0)
        runtime.stop()

    def test_full_candidate_check_launch_uses_disposable_paths(self):
        project = Path(__file__).resolve().parents[1]
        base = Path(self.temporary.name)
        environment = dict(os.environ)
        environment["QT_QPA_PLATFORM"] = "offscreen"
        environment["XDG_DATA_HOME"] = str(base / "data")
        environment["XDG_CONFIG_HOME"] = str(base / "config")
        completed = subprocess.run(
            [sys.executable, str(project / "linux-app/reasonnotes_widgets.py"),
             "--check-launch", "--no-auto-receive",
             "--root", str(base / "repo-check"),
             "--inbox", str(base / "inbox"),
             "--received-dir", str(base / "received")],
            env=environment, capture_output=True, text=True, timeout=15,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == "__main__":
    unittest.main()
