from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import os
import unittest
from uuid import UUID

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from reasonnotes_app.presenter import NotePresenter
from reasonnotes_app.service import NoteService
from reasonnotes_sync.envelope import Revision
from reasonnotes_sync.repository import Repository
from reasonnotes_widgets.bootstrap import create_application
from reasonnotes_widgets.controller import WidgetsController


NOTE = UUID("cccccccc-3333-4333-8333-cccccccccccc")
T0 = datetime(2026, 10, 18, 12, 0, tzinfo=timezone.utc)


class WidgetsConflictTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls.qt = QApplication.instance() or create_application(["conflict-test"])

    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        base = Path(self.temporary.name)
        self.repository = Repository.open(base / "repo")
        self.service = NoteService(self.repository, origin_device="linux")
        root = self.repository.create_revision(NOTE, "Base", "linux", T0)
        self.linux = self.repository.create_revision(
            NOTE, "Linux full body\nsecond line", "linux", T0 + timedelta(seconds=1)
        )
        self.android = Revision.create(
            NOTE, (root.revision_id,), "android", T0 + timedelta(seconds=2),
            False, "Android full body\nsecond line",
        )
        self.repository.import_bytes(self.android.serialize(), "android.md")
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

    def test_full_candidates_exact_keep_and_history_preservation(self):
        page = self.window.conflict_page
        bodies = [card.body.toPlainText() for card in page.cards]
        self.assertIn("Linux full body\nsecond line", bodies)
        self.assertIn("Android full body\nsecond line", bodies)
        history_before = len(tuple(self.repository.revisions()))
        android_card = next(
            card for card in page.cards if card.revision_id == self.android.revision_id
        )

        android_card.keep_button.click()

        self.assertEqual(self.service.open_note(NOTE), self.android.body)
        self.assertEqual(len(tuple(self.repository.revisions())), history_before + 1)
        self.assertIs(self.window.page_stack.currentWidget(), self.window.editor)

    def test_skip_writes_nothing(self):
        before = {revision.revision_id for revision in self.repository.revisions()}

        self.window.conflict_page.skip_button.click()

        after = {revision.revision_id for revision in self.repository.revisions()}
        self.assertEqual(after, before)
        self.assertIsNone(self.controller.presenter.conflict_view)

    def test_stale_choice_refreshes_and_deleted_head_is_labeled(self):
        stale_card = self.window.conflict_page.cards[0]
        third = Revision.create(
            NOTE, (self.linux.revision_id,), "android", T0 + timedelta(seconds=3),
            True, "",
        )
        self.repository.import_bytes(third.serialize(), "delete.md")

        stale_card.keep_button.click()

        self.assertIn("conflict changed", self.controller.presenter.save_error)
        self.assertEqual(len(self.window.conflict_page.cards), 2)
        self.assertTrue(
            any(not card.deleted_label.isHidden() for card in self.window.conflict_page.cards)
        )


if __name__ == "__main__":
    unittest.main()
