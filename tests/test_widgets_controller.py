from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from uuid import UUID

from PySide6.QtCore import QCoreApplication

from reasonnotes_app.presenter import NotePresenter
from reasonnotes_app.service import NoteService
from reasonnotes_sync.repository import Repository
from reasonnotes_sync.sync import SyncReport


class CapturingThreadPool:
    def __init__(self):
        self.workers = []

    def start(self, worker):
        self.workers.append(worker)

    def run_next(self):
        self.workers.pop(0).run()
        QCoreApplication.processEvents()


class WidgetsControllerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt = QCoreApplication.instance() or QCoreApplication(
            ["reasonnotes-widgets-controller-test"]
        )

    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.repository = Repository.open(
            Path(self.temporary.name) / "repository",
            local_device="linux",
            target_device="android",
        )
        self.service = NoteService(self.repository, origin_device="linux")
        self.pool = CapturingThreadPool()

    def controller(self, sync_runner=None):
        from reasonnotes_widgets.controller import WidgetsController

        presenter = NotePresenter(self.service, sync_runner)
        return WidgetsController(presenter, thread_pool=self.pool)

    def test_note_model_exposes_native_roles_and_draft_edit_is_targeted(self):
        first = self.service.create_note("# First\n\nBody")
        self.service.create_note("# Second\n\nOther")
        controller = self.controller()
        resets = []
        controller.note_model.modelReset.connect(lambda: resets.append(True))

        index = controller.note_model.index(0, 0)
        roles = {
            bytes(value).decode(): role
            for role, value in controller.note_model.roleNames().items()
        }
        self.assertIn("noteId", roles)
        self.assertIn("title", roles)
        self.assertTrue(controller.select_note(str(first)))
        before = len(resets)
        self.assertTrue(controller.edit_content("Changed body"))

        self.assertEqual(controller.current_title, "First")
        self.assertEqual(controller.current_content, "Changed body")
        self.assertEqual(len(resets), before)
        self.assertEqual(controller.presenter.save_state, "Dirty")
        self.assertIsInstance(
            controller.note_model.data(index, roles["title"]), str
        )

    def test_deletion_snapshot_is_exact_and_independent_of_later_selection(self):
        first = str(self.service.create_note("# First"))
        second = str(self.service.create_note("# Second"))
        controller = self.controller()

        self.assertTrue(controller.toggle_bulk_note(first))
        self.assertEqual(controller.prepare_delete(), (first,))
        self.assertTrue(controller.toggle_bulk_note(second))

        self.assertEqual(controller.pending_delete_ids, (first,))
        self.assertTrue(controller.confirm_delete())
        self.assertTrue(self.repository.is_purged(UUID(first)))
        self.assertFalse(any(row.note_id == first for row in controller.presenter.notes))
        self.assertTrue(any(row.note_id == second for row in controller.presenter.notes))

    def test_async_incoming_refresh_updates_model_after_worker_completion(self):
        controller = self.controller()
        finished = []
        controller.incoming_scan_finished.connect(finished.append)

        def scan():
            note_id = self.service.create_note("# Incoming\n\nFrom phone")
            return SimpleNamespace(
                imported=(str(note_id),), confirmed=(), errors=()
            )

        controller.configure_incoming_scan(scan)
        self.assertTrue(controller.refresh_incoming())
        self.assertEqual(controller.note_model.rowCount(), 0)

        self.pool.run_next()

        self.assertEqual(controller.note_model.rowCount(), 1)
        self.assertEqual(len(finished), 1)
        self.assertEqual(controller.incoming_message, "Received 1 revision(s), confirmed 0")

    def test_async_sync_flushes_draft_and_preserves_saved_content(self):
        note_id = str(self.service.create_note("# Draft\n\nOld"))
        report = SyncReport((), (), (), (), (), (), (), ())
        seen = []

        def sync_runner(selection):
            seen.append(selection)
            return report

        controller = self.controller(sync_runner)
        self.assertTrue(controller.select_note(note_id))
        self.assertTrue(controller.edit_content("Exact draft"))
        self.assertTrue(controller.start_sync((note_id,)))
        self.assertEqual(controller.presenter.sync_state, "Running")

        self.pool.run_next()

        self.assertEqual(controller.presenter.sync_state, "Completed")
        self.assertEqual(controller.current_content, "Exact draft")
        self.assertEqual(self.service.open_note(UUID(note_id)), "# Draft\n\nExact draft")
        self.assertEqual([[str(value) for value in seen[0]]], [[note_id]])


if __name__ == "__main__":
    unittest.main()
