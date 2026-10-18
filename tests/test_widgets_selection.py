from pathlib import Path
from tempfile import TemporaryDirectory
import os
import unittest
from uuid import UUID

from PySide6.QtCore import QSettings, QItemSelectionModel, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from reasonnotes_app.presenter import NotePresenter
from reasonnotes_app.service import NoteService
from reasonnotes_sync.repository import Repository
from reasonnotes_widgets.bootstrap import create_application
from reasonnotes_widgets.controller import WidgetsController


class WidgetsSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls.qt = QApplication.instance() or create_application(["selection-test"])

    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        base = Path(self.temporary.name)
        self.repository = Repository.open(base / "repo")
        self.service = NoteService(self.repository, origin_device="linux")
        self.settings = QSettings(str(base / "ui.ini"), QSettings.IniFormat)

    def controller(self):
        return WidgetsController(NotePresenter(self.service))

    def test_unicode_search_filters_real_note_model(self):
        self.service.create_note("# Zażółć\n\nGęślą jaźń")
        self.service.create_note("# Other\n\nPlain")
        controller = self.controller()

        controller.search("ZAŻÓŁĆ")

        self.assertEqual(controller.note_model.rowCount(), 1)
        self.assertEqual(controller.note_model.row(0)["title"], "Zażółć")

    def test_noncontiguous_native_selection_deletes_only_frozen_ids(self):
        from reasonnotes_widgets.main_window import ReasonNotesMainWindow

        ids = [str(self.service.create_note(f"# Note {number}")) for number in range(3)]
        confirmations = []
        controller = self.controller()
        window = ReasonNotesMainWindow(
            controller,
            settings=self.settings,
            confirm_delete=lambda count, bulk: confirmations.append((count, bulk)) or True,
        )
        self.addCleanup(window.close)
        selection = window.sidebar.list_view.selectionModel()
        selected_rows = [0, 2]
        for row in selected_rows:
            selection.select(
                controller.note_model.index(row, 0),
                QItemSelectionModel.SelectionFlag.Select
                | QItemSelectionModel.SelectionFlag.Rows,
            )
        window.sync_bulk_selection()
        frozen = set(controller.bulk_selected_ids)

        window.delete_selection()

        self.assertEqual(confirmations, [(2, True)])
        self.assertEqual(
            {note_id for note_id in ids if self.repository.is_purged(UUID(note_id))},
            frozen,
        )
        self.assertEqual(
            {row.note_id for row in controller.presenter.notes}, set(ids) - frozen
        )

    def test_delete_cancel_and_search_preserve_frozen_selection(self):
        from reasonnotes_widgets.main_window import ReasonNotesMainWindow

        first = str(self.service.create_note("# Alpha"))
        second = str(self.service.create_note("# Beta"))
        controller = self.controller()
        controller.set_bulk_selection((first,))
        self.assertEqual(controller.prepare_delete(), (first,))
        controller.search("Beta")
        self.assertEqual(controller.pending_delete_ids, (first,))

        window = ReasonNotesMainWindow(
            controller,
            settings=self.settings,
            confirm_delete=lambda _count, _bulk: False,
        )
        self.addCleanup(window.close)
        window.delete_selection()

        self.assertFalse(self.repository.is_purged(UUID(first)))
        self.assertFalse(self.repository.is_purged(UUID(second)))

    def test_stale_frozen_selection_fails_closed(self):
        first = str(self.service.create_note("# First"))
        second = str(self.service.create_note("# Second"))
        controller = self.controller()
        controller.set_bulk_selection((first,))
        controller.prepare_delete()
        self.service.delete_note(UUID(first))

        self.assertFalse(controller.confirm_delete())
        self.assertFalse(self.repository.is_purged(UUID(second)))
        self.assertIn("Selection changed", controller.presenter.save_error)

    def test_keyboard_navigation_opens_current_note(self):
        from reasonnotes_widgets.main_window import ReasonNotesMainWindow

        self.service.create_note("# First")
        self.service.create_note("# Second")
        controller = self.controller()
        window = ReasonNotesMainWindow(controller, settings=self.settings)
        self.addCleanup(window.close)
        window.show()
        view = window.sidebar.list_view
        view.setFocus()
        view.setCurrentIndex(controller.note_model.index(0, 0))

        QTest.keyClick(view, Qt.Key.Key_Down)

        self.assertEqual(
            controller.active_note_id,
            controller.note_model.note_id_at(view.currentIndex().row()),
        )

    def test_delete_confirmation_describes_irrecoverable_history_and_peer_purge(self):
        from reasonnotes_widgets.main_window import ReasonNotesMainWindow

        window = ReasonNotesMainWindow(self.controller(), settings=self.settings)
        self.addCleanup(window.close)

        prompt = window._delete_confirmation_text(2)

        self.assertIn("local revision history", prompt)
        self.assertIn("paired phone", prompt)
        self.assertNotIn("Recoverable", prompt)


if __name__ == "__main__":
    unittest.main()
