"""Small runtime catalogue for application chrome only."""

from __future__ import annotations

from PySide6.QtCore import QObject, QSettings, Signal


TRANSLATIONS = {
    "en": {
        "app_name": "ReasonNotes",
        "new_note": "New note",
        "save": "Save",
        "sync": "Sync",
        "delete": "Delete",
        "settings": "Settings",
        "search_notes": "Search notes",
        "note_title": "Note title",
        "start_writing": "Start writing…",
        "language": "Language",
        "english": "English",
        "polish": "Polski",
        "system_appearance": "Appearance follows the system Kvantum theme.",
        "deletion_heading": "Automatic permanent deletion",
        "deletion_help": "While ReasonNotes is open, pair your phone with this computer address and private key. Only deletion IDs are exchanged.",
        "computer_address": "Computer address",
        "pairing_key": "Private pairing key (copy to Android Settings)",
        "local": "Local",
        "phone": "Phone",
        "no_note_selected": "No note selected",
        "idle": "Idle",
        "dirty": "Dirty",
        "saving": "Saving",
        "saved": "Saved",
        "error": "Error",
        "running": "Running",
        "completed": "Completed",
        "delete_note": "Delete note",
        "delete_notes": "Delete notes",
        "delete_confirm_one": "Permanently delete this note and its local revision history? Its deletion will be sent to the paired phone when both apps reconnect.",
        "delete_confirm_many": "Permanently delete these {count} notes and their local revision history? Their deletions will be sent to the paired phone when both apps reconnect.",
        "cancel": "Cancel",
        "all_notes": "All notes",
        "selected_notes": "Selected notes",
        "select_all": "Select all",
        "clear": "Clear",
        "start_sync": "Start Sync",
        "conflict": "Conflict",
        "keep_version": "Keep this version",
        "skip": "Skip",
    },
    "pl": {
        "app_name": "ReasonNotes",
        "new_note": "Nowa notatka",
        "save": "Zapisz",
        "sync": "Synchronizuj",
        "delete": "Usuń",
        "settings": "Ustawienia",
        "search_notes": "Szukaj notatek",
        "note_title": "Tytuł notatki",
        "start_writing": "Zacznij pisać…",
        "language": "Język",
        "english": "English",
        "polish": "Polski",
        "system_appearance": "Wygląd jest zgodny z systemowym motywem Kvantum.",
        "deletion_heading": "Automatyczne trwałe usuwanie",
        "deletion_help": "Gdy ReasonNotes jest otwarty, sparuj telefon z adresem komputera i kluczem prywatnym. Wymieniane są tylko identyfikatory usunięć.",
        "computer_address": "Adres komputera",
        "pairing_key": "Prywatny klucz parowania (skopiuj do ustawień Androida)",
        "local": "Lokalnie",
        "phone": "Telefon",
        "no_note_selected": "Nie wybrano notatki",
        "idle": "Bezczynny",
        "dirty": "Niezapisana",
        "saving": "Zapisywanie",
        "saved": "Zapisano",
        "error": "Błąd",
        "running": "W toku",
        "completed": "Zakończono",
        "delete_note": "Usuń notatkę",
        "delete_notes": "Usuń notatki",
        "delete_confirm_one": "Trwale usunąć tę notatkę i jej lokalną historię wersji? Usunięcie zostanie wysłane do sparowanego telefonu po ponownym połączeniu obu aplikacji.",
        "delete_confirm_many": "Trwale usunąć te notatki ({count}) i ich lokalną historię wersji? Usunięcia zostaną wysłane do sparowanego telefonu po ponownym połączeniu obu aplikacji.",
        "cancel": "Anuluj",
        "all_notes": "Wszystkie notatki",
        "selected_notes": "Wybrane notatki",
        "select_all": "Zaznacz wszystkie",
        "clear": "Wyczyść",
        "start_sync": "Rozpocznij synchronizację",
        "conflict": "Konflikt",
        "keep_version": "Zachowaj tę wersję",
        "skip": "Pomiń",
    },
}


class Translator(QObject):
    language_changed = Signal(str)

    def __init__(self, settings: QSettings | None = None, parent=None):
        super().__init__(parent)
        self.settings = settings if settings is not None else QSettings()
        stored = self.settings.value("ui/language", "en")
        self.language = stored if stored in TRANSLATIONS else "en"

    def text(self, key: str) -> str:
        return TRANSLATIONS[self.language].get(key, key)

    def set_language(self, language: str) -> bool:
        if language not in TRANSLATIONS:
            return False
        if language == self.language:
            return True
        self.settings.setValue("ui/language", language)
        self.settings.sync()
        if self.settings.status() != QSettings.Status.NoError:
            raise RuntimeError("Unable to persist ReasonNotes language preference")
        self.language = language
        self.language_changed.emit(language)
        return True
