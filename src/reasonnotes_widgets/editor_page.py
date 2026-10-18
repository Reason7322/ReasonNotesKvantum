"""Native title and Markdown editing surface."""

from __future__ import annotations

from PySide6.QtCore import QSignalBlocker, Signal, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QHBoxLayout,
    QFrame,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .visuals import integrate_line_edit, integrate_scroll_surface
from .material import GlassCard, TitleRule


class EditorPage(QWidget):
    title_edited = Signal(str)
    content_edited = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("editorPage")
        outer = QHBoxLayout(self)
        outer.setContentsMargins(32, 30, 32, 32)
        outer.setSpacing(0)
        outer.addStretch(0)

        self.writing_column = GlassCard(self)
        self.writing_column.setObjectName("writingColumn")
        self.writing_column.setMaximumWidth(920)
        self.writing_column.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        column = QVBoxLayout(self.writing_column)
        column.setContentsMargins(38, 22, 38, 26)
        column.setSpacing(0)

        self.status_bar = QWidget(self.writing_column)
        self.status_bar.setObjectName("editorStatusBar")
        self.status_bar.setMinimumHeight(40)
        status_layout = QHBoxLayout(self.status_bar)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(10)
        self.save_status = QLabel("Idle", self.status_bar)
        self.save_status.setObjectName("saveStatus")
        self.delivery_status = QLabel("No note selected", self.status_bar)
        self.delivery_status.setObjectName("deliveryStatus")
        self.status_separator = QFrame(self.status_bar)
        self.status_separator.setFrameShape(QFrame.Shape.VLine)
        self.status_separator.setFrameShadow(QFrame.Shadow.Plain)
        for label in (self.save_status, self.delivery_status):
            status_font = QFont(label.font())
            status_font.setPixelSize(13)
            label.setFont(status_font)
        status_layout.addStretch(1)
        status_layout.addWidget(self.save_status)
        status_layout.addWidget(self.status_separator)
        status_layout.addWidget(self.delivery_status)

        self.title_editor = QLineEdit(self.writing_column)
        self.title_editor.setObjectName("titleEditor")
        self.title_editor.setPlaceholderText("Note title")
        self.title_editor.setAccessibleName("Note title")
        integrate_line_edit(self.title_editor)
        title_font = QFont(self.title_editor.font())
        title_font.setPixelSize(36)
        title_font.setWeight(QFont.Weight.DemiBold)
        self.title_editor.setFont(title_font)

        self.title_rule = TitleRule(self.writing_column)
        self.body_editor = QPlainTextEdit(self.writing_column)
        self.body_editor.setObjectName("bodyEditor")
        self.body_editor.setPlaceholderText("Start writing…")
        self.body_editor.setAccessibleName("Markdown note body")
        self.body_editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        integrate_scroll_surface(self.body_editor)
        self.body_editor.document().setDocumentMargin(6)
        body_font = QFont(self.body_editor.font())
        body_font.setPixelSize(18)
        self.body_editor.setFont(body_font)

        column.addWidget(self.status_bar)
        column.addSpacing(16)
        column.addWidget(self.title_editor)
        column.addSpacing(12)
        column.addWidget(self.title_rule)
        column.addSpacing(22)
        column.addWidget(self.body_editor, 1)
        outer.addWidget(self.writing_column, 1)
        outer.addStretch(0)

        self.title_editor.textEdited.connect(self.title_edited)
        self.body_editor.textChanged.connect(
            lambda: self.content_edited.emit(self.body_editor.toPlainText())
        )

    def set_document(self, title: str, content: str) -> None:
        if self.title_editor.text() != title:
            title_blocker = QSignalBlocker(self.title_editor)
            self.title_editor.setText(title)
            # QLineEdit otherwise scrolls a long loaded heading to its tail.
            # The established editor always reveals the meaningful beginning.
            self.title_editor.setCursorPosition(0)
            del title_blocker
        if self.body_editor.toPlainText() != content:
            body_blocker = QSignalBlocker(self.body_editor)
            self.body_editor.setPlainText(content)
            del body_blocker

    def set_editable(self, editable: bool) -> None:
        self.title_editor.setEnabled(editable)
        self.body_editor.setEnabled(editable)
