from pathlib import Path
from tempfile import TemporaryDirectory
import os
import unittest

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from reasonnotes_app.presenter import NotePresenter
from reasonnotes_app.service import NoteService
from reasonnotes_sync.repository import Repository
from reasonnotes_widgets.bootstrap import create_application
from reasonnotes_widgets.controller import WidgetsController


class WidgetsI18nTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls.qt = QApplication.instance() or create_application(["i18n-test"])

    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.settings = QSettings(str(self.base / "ui.ini"), QSettings.IniFormat)

    def test_language_persists_and_invalid_value_falls_back_to_english(self):
        from reasonnotes_widgets.i18n import Translator

        translator = Translator(self.settings)
        translator.set_language("pl")
        restored = Translator(
            QSettings(str(self.base / "ui.ini"), QSettings.IniFormat)
        )
        self.assertEqual(restored.language, "pl")
        self.assertEqual(restored.text("new_note"), "Nowa notatka")

        self.settings.setValue("ui/language", "xx")
        invalid = Translator(self.settings)
        self.assertEqual(invalid.language, "en")

    def test_settings_switches_polish_chrome_without_appearance_selector_or_note_change(self):
        from reasonnotes_widgets.i18n import Translator
        from reasonnotes_widgets.main_window import ReasonNotesMainWindow

        repository = Repository.open(self.base / "repo")
        service = NoteService(repository, origin_device="linux")
        note_id = service.create_note("# Tytuł użytkownika\n\nTreść *Markdown*")
        controller = WidgetsController(NotePresenter(service))
        controller.select_note(str(note_id))
        translator = Translator(self.settings)
        window = ReasonNotesMainWindow(
            controller, settings=self.settings, translator=translator
        )
        self.addCleanup(window.close)

        window.open_settings()
        window.settings_page.polish_button.click()

        self.assertEqual(window.sidebar.new_button.text(), "Nowa notatka")
        self.assertEqual(window.sidebar.settings_button.text(), "Ustawienia")
        self.assertEqual(window.settings_page.heading.text(), "Ustawienia")
        self.assertFalse(hasattr(window.settings_page, "appearance_group"))
        self.assertEqual(controller.current_title, "Tytuł użytkownika")
        self.assertEqual(controller.current_content, "Treść *Markdown*")
        self.assertEqual(service.open_note(note_id), "# Tytuł użytkownika\n\nTreść *Markdown*")

    def test_all_declared_polish_labels_are_nonempty(self):
        from reasonnotes_widgets.i18n import TRANSLATIONS

        self.assertEqual(set(TRANSLATIONS["en"]), set(TRANSLATIONS["pl"]))
        self.assertTrue(all(value.strip() for value in TRANSLATIONS["pl"].values()))

    def test_settings_exposes_foreground_purge_pairing_without_theme_controls(self):
        from reasonnotes_widgets.main_window import ReasonNotesMainWindow

        repository = Repository.open(self.base / "pairing-repo")
        controller = WidgetsController(
            NotePresenter(NoteService(repository, origin_device="linux"))
        )
        window = ReasonNotesMainWindow(
            controller,
            settings=self.settings,
            deletion_pairing=("192.0.2.25", 49233, "ab" * 32),
        )
        self.addCleanup(window.close)

        self.assertEqual(
            window.settings_page.purge_address.text(), "192.0.2.25:49233"
        )
        self.assertEqual(window.settings_page.purge_key.text(), "ab" * 32)
        self.assertTrue(window.settings_page.purge_address.isReadOnly())
        self.assertTrue(window.settings_page.purge_key.isReadOnly())
        self.assertFalse(hasattr(window.settings_page, "theme_group"))


if __name__ == "__main__":
    unittest.main()
