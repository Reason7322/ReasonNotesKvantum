"""Application settings that do not compete with system theming."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QRadioButton,
    QSizePolicy,
    QStyle,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .visuals import configure_action_button, integrate_line_edit


class SettingsPage(QWidget):
    back_requested = Signal()

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

        header = QHBoxLayout()
        header.setSpacing(12)
        self.back_button = QToolButton(self.content_column)
        configure_action_button(self.back_button)
        self.back_button.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowLeft)
        )
        self.back_button.setSizePolicy(
            QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed
        )
        self.heading = QLabel(self.content_column)
        heading_font = self.heading.font()
        heading_font.setPointSize(max(heading_font.pointSize() + 6, 18))
        heading_font.setBold(True)
        self.heading.setFont(heading_font)
        header.addWidget(self.back_button)
        header.addWidget(self.heading)
        header.addStretch(1)

        self.language_label = QLabel(self.content_column)
        section_font = self.language_label.font()
        section_font.setBold(True)
        self.language_label.setFont(section_font)
        self.english_button = QRadioButton(self.content_column)
        self.polish_button = QRadioButton(self.content_column)
        self.language_group = QButtonGroup(self.content_column)
        self.language_group.addButton(self.english_button)
        self.language_group.addButton(self.polish_button)
        self.system_appearance = QLabel(self.content_column)
        self.system_appearance.setWordWrap(True)
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
        layout.addLayout(header)
        layout.addSpacing(20)
        layout.addWidget(self.language_label)
        layout.addWidget(self.english_button)
        layout.addWidget(self.polish_button)
        layout.addSpacing(8)
        layout.addWidget(self.system_appearance)
        layout.addSpacing(20)
        for widget in pairing_widgets:
            layout.addWidget(widget)
        layout.addStretch(1)
        outer.addStretch(1)
        outer.addWidget(self.content_column, 1)
        outer.addStretch(1)
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
        self.deletion_heading.setText(tr("deletion_heading"))
        self.deletion_help.setText(tr("deletion_help"))
        self.purge_address_label.setText(tr("computer_address"))
        self.purge_key_label.setText(tr("pairing_key"))
        self.english_button.setChecked(self.translator.language == "en")
        self.polish_button.setChecked(self.translator.language == "pl")
