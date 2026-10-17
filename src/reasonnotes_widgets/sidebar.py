"""Permanent native notes sidebar."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class NotesSidebar(QWidget):
    def __init__(self, model, *, icon_root: Path | None = None, parent=None):
        super().__init__(parent)
        self.setObjectName("notesSidebar")
        self.setMinimumWidth(240)
        self.setMaximumWidth(520)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 16, 14, 12)
        layout.setSpacing(10)

        brand_row = QHBoxLayout()
        brand_row.setSpacing(8)
        self.brand_icon = QLabel(self)
        self.brand_icon.setObjectName("brandIcon")
        self.brand_label = QLabel("ReasonNotes", self)
        self.brand_label.setObjectName("brandLabel")
        font = self.brand_label.font()
        font.setPointSize(max(font.pointSize() + 4, 15))
        font.setBold(True)
        self.brand_label.setFont(font)
        brand_row.addWidget(self.brand_icon)
        brand_row.addWidget(self.brand_label)
        brand_row.addStretch(1)
        layout.addLayout(brand_row)

        actions = QGridLayout()
        actions.setSpacing(8)
        self.new_button = QPushButton("New note", self)
        self.save_button = QPushButton("Save", self)
        self.sync_button = QPushButton("Sync", self)
        self.delete_button = QPushButton("Delete", self)
        self.settings_button = QPushButton("Settings", self)
        actions.addWidget(self.new_button, 0, 0)
        actions.addWidget(self.save_button, 0, 1)
        actions.addWidget(self.sync_button, 1, 0)
        actions.addWidget(self.delete_button, 1, 1)
        actions.addWidget(self.settings_button, 2, 0, 1, 2)
        layout.addLayout(actions)

        self.search_field = QLineEdit(self)
        self.search_field.setObjectName("noteSearch")
        self.search_field.setPlaceholderText("Search notes")
        self.search_field.setClearButtonEnabled(True)
        self.search_field.setAccessibleName("Search notes")
        layout.addWidget(self.search_field)

        self.list_view = QListView(self)
        self.list_view.setObjectName("noteList")
        self.list_view.setModel(model)
        self.list_view.setSelectionMode(QListView.SelectionMode.ExtendedSelection)
        self.list_view.setSelectionBehavior(QListView.SelectionBehavior.SelectRows)
        self.list_view.setUniformItemSizes(True)
        self.list_view.setEditTriggers(QListView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.list_view, 1)

        self.local_status = QLabel("Local: Idle", self)
        self.local_status.setObjectName("localStatus")
        self.sync_status = QLabel("Phone: Idle", self)
        self.sync_status.setObjectName("syncStatus")
        self.sync_status.setWordWrap(True)
        layout.addWidget(self.local_status)
        layout.addWidget(self.sync_status)

        if icon_root is not None:
            app_icon = Path(icon_root) / "reasonnotes-yamis.svg"
            if app_icon.is_file():
                self.brand_icon.setPixmap(
                    QIcon(str(app_icon)).pixmap(28, 28)
                )
