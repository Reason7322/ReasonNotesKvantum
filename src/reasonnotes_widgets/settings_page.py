"""Application settings that do not compete with system theming."""

from __future__ import annotations

from PySide6.QtGui import QFontDatabase

from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QRadioButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .visuals import integrate_line_edit
from .material import GlassCard


class SettingsPage(QWidget):
    def __init__(self, translator, deletion_pairing=None, parent=None):
        super().__init__(parent)
        self.translator = translator
        outer = QHBoxLayout(self)
        outer.setContentsMargins(32, 26, 32, 32)
        outer.setSpacing(0)

        self.content_column = QWidget(self)
        self.content_column.setObjectName("settingsColumn")
        self.content_column.setMaximumWidth(720)
        self.content_column.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        layout = QVBoxLayout(self.content_column)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self.heading = QLabel(self.content_column)
        heading_font = self.heading.font()
        heading_font.setPointSize(max(heading_font.pointSize() + 6, 18))
        heading_font.setBold(True)
        self.heading.setFont(heading_font)

        self.language_label = QLabel(self.content_column)
        section_font = self.language_label.font()
        section_font.setBold(True)
        self.language_label.setFont(section_font)
        self.english_button = QRadioButton(self.content_column)
        self.polish_button = QRadioButton(self.content_column)
        self.language_group = QButtonGroup(self.content_column)
        self.language_group.addButton(self.english_button)
        self.language_group.addButton(self.polish_button)
        self.deletion_heading = QLabel(self.content_column)
        deletion_font = self.deletion_heading.font()
        deletion_font.setBold(True)
        self.deletion_heading.setFont(deletion_font)
        self.deletion_help = QLabel(self.content_column)
        self.deletion_help.setWordWrap(True)
        self.purge_address_label = QLabel(self.content_column)
        self.purge_address = QLineEdit(self.content_column)
        self.purge_address.setObjectName("purgeAddress")
        self.purge_address.setReadOnly(True)
        self.purge_address.setClearButtonEnabled(False)
        integrate_line_edit(self.purge_address)
        self.purge_key_label = QLabel(self.content_column)
        self.purge_key = QLineEdit(self.content_column)
        self.purge_key.setObjectName("purgeKey")
        self.purge_key.setReadOnly(True)
        self.purge_key.setClearButtonEnabled(False)
        key_font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        key_font.setPointSize(10)
        self.purge_key.setFont(key_font)
        integrate_line_edit(self.purge_key)
        pairing_widgets = (
            self.deletion_heading,
            self.deletion_help,
            self.purge_address_label,
            self.purge_address,
            self.purge_key_label,
            self.purge_key,
        )
        if deletion_pairing is None:
            for widget in pairing_widgets:
                widget.hide()
        else:
            address, port, key = deletion_pairing
            self.purge_address.setText(f"{address}:{port}")
            self.purge_key.setText(key)
            # Show the beginning of long credentials rather than a clipped tail;
            # users can still select/copy the entire read-only field.
            self.purge_key.setCursorPosition(0)
        layout.addWidget(self.heading)
        layout.addSpacing(14)

        self.language_card = GlassCard(self.content_column)
        language_layout = QVBoxLayout(self.language_card)
        language_layout.setContentsMargins(26, 22, 26, 24)
        language_layout.setSpacing(13)
        language_layout.addWidget(self.language_label)
        language_layout.addWidget(self.english_button)
        language_layout.addWidget(self.polish_button)
        layout.addWidget(self.language_card)

        self.pairing_card = GlassCard(self.content_column)
        pairing_layout = QVBoxLayout(self.pairing_card)
        pairing_layout.setContentsMargins(26, 22, 26, 24)
        pairing_layout.setSpacing(11)
        for widget in pairing_widgets:
            pairing_layout.addWidget(widget)
        if deletion_pairing is None:
            self.pairing_card.hide()
        else:
            layout.addSpacing(10)
            layout.addWidget(self.pairing_card)
        layout.addStretch(1)
        outer.addStretch(1)
        outer.addWidget(self.content_column, 7)
        outer.addStretch(1)
        self.english_button.clicked.connect(lambda: translator.set_language("en"))
        self.polish_button.clicked.connect(lambda: translator.set_language("pl"))
        translator.language_changed.connect(lambda _language: self.retranslate())
        self.retranslate()

    def retranslate(self) -> None:
        tr = self.translator.text
        self.heading.setText(tr("settings"))
        self.language_label.setText(tr("language"))
        self.english_button.setText(tr("english"))
        self.polish_button.setText(tr("polish"))
        self.deletion_heading.setText(tr("deletion_heading"))
        self.deletion_help.setText(tr("deletion_help"))
        self.purge_address_label.setText(tr("computer_address"))
        self.purge_key_label.setText(tr("pairing_key"))
        self.english_button.setChecked(self.translator.language == "en")
        self.polish_button.setChecked(self.translator.language == "pl")
