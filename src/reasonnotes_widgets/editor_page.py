"""Native title and Markdown editing surface."""

from __future__ import annotations

from PySide6.QtCore import QSignalBlocker, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class EditorPage(QWidget):
    title_edited = Signal(str)
    content_edited = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("editorPage")
        outer = QHBoxLayout(self)
        outer.setContentsMargins(32, 24, 32, 24)
        outer.setSpacing(0)
        outer.addStretch(1)

        self.writing_column = QWidget(self)
        self.writing_column.setObjectName("writingColumn")
        self.writing_column.setMaximumWidth(920)
        self.writing_column.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        column = QVBoxLayout(self.writing_column)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(12)

        self.title_editor = QLineEdit(self.writing_column)
        self.title_editor.setObjectName("titleEditor")
        self.title_editor.setPlaceholderText("Note title")
        self.title_editor.setAccessibleName("Note title")
        title_font = QFont(self.title_editor.font())
        title_font.setPointSize(max(title_font.pointSize() + 7, 18))
        title_font.setWeight(QFont.Weight.DemiBold)
        self.title_editor.setFont(title_font)

        self.body_editor = QPlainTextEdit(self.writing_column)
        self.body_editor.setObjectName("bodyEditor")
        self.body_editor.setPlaceholderText("Start writing…")
        self.body_editor.setAccessibleName("Markdown note body")
        self.body_editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        body_font = QFont(self.body_editor.font())
        body_font.setPointSize(max(body_font.pointSize() + 2, 12))
        self.body_editor.setFont(body_font)

        footer = QHBoxLayout()
        self.save_status = QLabel("Idle", self.writing_column)
        self.save_status.setObjectName("saveStatus")
        self.delivery_status = QLabel("No note selected", self.writing_column)
        self.delivery_status.setObjectName("deliveryStatus")
        footer.addWidget(self.save_status)
        footer.addStretch(1)
        footer.addWidget(self.delivery_status)

        column.addWidget(self.title_editor)
        column.addWidget(self.body_editor, 1)
        column.addLayout(footer)
        outer.addWidget(self.writing_column, 1)
        outer.addStretch(1)

        self.title_editor.textEdited.connect(self.title_edited)
        self.body_editor.textChanged.connect(
            lambda: self.content_edited.emit(self.body_editor.toPlainText())
        )

    def set_document(self, title: str, content: str) -> None:
        title_blocker = QSignalBlocker(self.title_editor)
        body_blocker = QSignalBlocker(self.body_editor)
        self.title_editor.setText(title)
        self.body_editor.setPlainText(content)
        del body_blocker
        del title_blocker

    def set_editable(self, editable: bool) -> None:
        self.title_editor.setEnabled(editable)
        self.body_editor.setEnabled(editable)
