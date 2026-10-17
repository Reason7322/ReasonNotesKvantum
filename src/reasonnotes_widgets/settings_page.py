"""Application settings that do not compete with system theming."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QLabel,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)


class SettingsPage(QWidget):
    back_requested = Signal()

    def __init__(self, translator, parent=None):
        super().__init__(parent)
        self.translator = translator
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 36, 48, 36)
        layout.setSpacing(14)
        self.back_button = QPushButton(self)
        self.heading = QLabel(self)
        heading_font = self.heading.font()
        heading_font.setPointSize(max(heading_font.pointSize() + 6, 18))
        heading_font.setBold(True)
        self.heading.setFont(heading_font)
        self.language_label = QLabel(self)
        self.english_button = QRadioButton(self)
        self.polish_button = QRadioButton(self)
        self.language_group = QButtonGroup(self)
        self.language_group.addButton(self.english_button)
        self.language_group.addButton(self.polish_button)
        self.system_appearance = QLabel(self)
        self.system_appearance.setWordWrap(True)
        layout.addWidget(self.back_button)
        layout.addSpacing(12)
        layout.addWidget(self.heading)
        layout.addSpacing(12)
        layout.addWidget(self.language_label)
        layout.addWidget(self.english_button)
        layout.addWidget(self.polish_button)
        layout.addSpacing(16)
        layout.addWidget(self.system_appearance)
        layout.addStretch(1)
        self.back_button.clicked.connect(self.back_requested)
        self.english_button.clicked.connect(lambda: translator.set_language("en"))
        self.polish_button.clicked.connect(lambda: translator.set_language("pl"))
        translator.language_changed.connect(lambda _language: self.retranslate())
        self.retranslate()

    def retranslate(self) -> None:
        tr = self.translator.text
        self.back_button.setText(tr("back_to_notes"))
        self.heading.setText(tr("settings"))
        self.language_label.setText(tr("language"))
        self.english_button.setText(tr("english"))
        self.polish_button.setText(tr("polish"))
        self.system_appearance.setText(tr("system_appearance"))
        self.english_button.setChecked(self.translator.language == "en")
        self.polish_button.setChecked(self.translator.language == "pl")
