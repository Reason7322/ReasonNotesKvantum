from datetime import datetime, timedelta, timezone
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import os
import unittest
from uuid import UUID

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from reasonnotes_app.presenter import NotePresenter
from reasonnotes_app.service import NoteService
from reasonnotes_sync.current_store import CurrentNoteStore
from reasonnotes_sync.state_envelope import StateEnvelope
from reasonnotes_widgets.bootstrap import create_application
from reasonnotes_widgets.controller import WidgetsController


NOTE = UUID("cccccccc-3333-4333-8333-cccccccccccc")
T0 = datetime(2026, 10, 18, 12, 0, tzinfo=timezone.utc)


class ProtectedVisualSourceTests(unittest.TestCase):
    def test_approved_sidebar_material_and_editor_sources_are_unchanged(self):
        project = Path(__file__).resolve().parents[1]
        expected = {
            "src/reasonnotes_widgets/sidebar.py":
                "4432719b6ec73c514d14b29a47116c94d09ab95f4628656d3076b0342b6b3b7e",
            "src/reasonnotes_widgets/material.py":
                "755d6e3a0644a2b988cde0c13bde49db3cdf12f5c1e52946eb9026086007d64c",
            "src/reasonnotes_widgets/editor_page.py":
                "89ca32a9e04fed078827200cd6b6dca18a3a459bc623155547645feeb7238798",
        }
        actual = {
            relative: hashlib.sha256((project / relative).read_bytes()).hexdigest()
            for relative in expected
        }
        self.assertEqual(expected, actual)


class WidgetsConflictTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls.qt = QApplication.instance() or create_application(["conflict-test"])

    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        base = Path(self.temporary.name)
        self.repository = CurrentNoteStore.open(base / "reasonnotes-v2", "linux")
        self.service = NoteService(self.repository, origin_device="linux")
        root = self.repository.save_local(NOTE, "Base", "original", T0)
        self.repository.acknowledge(root.change_id)
        self.linux = self.repository.save_local(
            NOTE, "Linux full body", "second line", T0 + timedelta(seconds=1)
        )
        self.android = StateEnvelope.upsert(
            NOTE, (root.change_id,), "android", T0 + timedelta(seconds=2),
            "Android full body", "second line",
        )
        self.assertEqual("conflict", self.repository.apply(self.android).kind)
        self.controller = WidgetsController(NotePresenter(self.service))
        from reasonnotes_widgets.main_window import ReasonNotesMainWindow
        self.window = ReasonNotesMainWindow(
            self.controller,
            settings=QSettings(str(base / "ui.ini"), QSettings.IniFormat),
        )
        self.addCleanup(self.window.close)
        self.window.show()
        self.assertTrue(self.controller.select_note(str(NOTE)))
        self.window.refresh_from_controller()

    def test_full_candidates_exact_keep_and_loser_erasure(self):
        page = self.window.conflict_page
        bodies = [card.body.toPlainText() for card in page.cards]
        self.assertIn("# Linux full body\n\nsecond line", bodies)
        self.assertIn("# Android full body\n\nsecond line", bodies)
        pending_before = self.repository.pending_states()
        android_card = next(
            card for card in page.cards if card.revision_id == self.android.change_id
        )

        android_card.keep_button.click()

        self.assertEqual(
            self.service.open_note(NOTE), "# Android full body\n\nsecond line"
        )
        self.assertIsNone(self.repository.conflict(NOTE))
        self.assertNotEqual(pending_before, self.repository.pending_states())
        self.assertEqual(1, len(self.repository.pending_states()))
        self.assertIs(self.window.page_stack.currentWidget(), self.window.editor)

    def test_skip_writes_nothing(self):
        before = (
            self.repository.get(NOTE),
            self.repository.conflict(NOTE),
            self.repository.pending_states(),
        )

        self.window.conflict_page.skip_button.click()

        after = (
            self.repository.get(NOTE),
            self.repository.conflict(NOTE),
            self.repository.pending_states(),
        )
        self.assertEqual(after, before)
        self.assertIsNone(self.controller.presenter.conflict_view)

    def test_stale_choice_refreshes_current_conflict_state(self):
        stale_card = self.window.conflict_page.cards[0]
        self.repository.resolve(NOTE, self.android.change_id, T0 + timedelta(seconds=3))

        stale_card.keep_button.click()

        self.assertIn("conflict changed", self.controller.presenter.save_error)
        self.assertEqual(len(self.window.conflict_page.cards), 0)


if __name__ == "__main__":
    unittest.main()
