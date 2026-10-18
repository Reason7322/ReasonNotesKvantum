"""Explicit native conflict comparison and resolution UI."""

from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QScrollArea,
    QVBoxLayout, QWidget,
)

from .visuals import integrate_scroll_surface


class ConflictCard(QFrame):
    def __init__(self, candidate, keep, parent=None):
        super().__init__(parent)
        self.revision_id = candidate.revision_id
        self.origin_device = candidate.origin_device
        layout = QVBoxLayout(self)
        self.origin_label = QLabel(candidate.origin_device, self)
        self.revision_label = QLabel(candidate.revision_id, self)
        self.revision_label.setTextInteractionFlags(
            self.revision_label.textInteractionFlags()
        )
        self.deleted_label = QLabel("Deleted version", self)
        self.deleted_label.setVisible(candidate.deleted)
        self.body = QPlainTextEdit(self)
        self.body.setReadOnly(True)
        self.body.setPlainText(candidate.body)
        integrate_scroll_surface(self.body)
        self.keep_button = QPushButton("Keep this version", self)
        self.keep_button.clicked.connect(keep)
        layout.addWidget(self.origin_label)
        layout.addWidget(self.revision_label)
        layout.addWidget(self.deleted_label)
        layout.addWidget(self.body, 1)
        layout.addWidget(self.keep_button)


class ConflictPage(QWidget):
    def __init__(self, controller, translator, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.translator = translator
        self.cards = []
        outer = QVBoxLayout(self)
        self.heading = QLabel(self)
        heading_font = self.heading.font()
        heading_font.setPointSize(max(heading_font.pointSize() + 5, 17))
        heading_font.setBold(True)
        self.heading.setFont(heading_font)
        self.explanation = QLabel(self)
        self.explanation.setWordWrap(True)
        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        integrate_scroll_surface(self.scroll)
        self.container = QWidget(self.scroll)
        self.cards_layout = QHBoxLayout(self.container)
        self.scroll.setWidget(self.container)
        self.skip_button = QPushButton(self)
        outer.addWidget(self.heading)
        outer.addWidget(self.explanation)
        outer.addWidget(self.scroll, 1)
        outer.addWidget(self.skip_button)
        self.skip_button.clicked.connect(controller.skip_conflict)
        translator.language_changed.connect(lambda _language: self.retranslate())
        self.retranslate()

    def retranslate(self) -> None:
        polish = self.translator.language == "pl"
        self.heading.setText(self.translator.text("conflict"))
        self.explanation.setText(
            "Wybierz dokładną wersję. Wszystkie zastąpione wersje pozostaną w historii."
            if polish else
            "Choose the exact version to keep. Superseded revisions remain in history."
        )
        self.skip_button.setText(self.translator.text("skip"))
        for card in self.cards:
            card.keep_button.setText(self.translator.text("keep_version"))
            card.deleted_label.setText("Usunięta wersja" if polish else "Deleted version")

    def load(self) -> None:
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        self.cards = []
        view = self.controller.presenter.conflict_view
        if view is None:
            return
        for candidate in view.candidates:
            choice = (
                "keep-android"
                if candidate.origin_device.startswith("android")
                else "keep-linux"
            )
            card = ConflictCard(
                candidate,
                lambda _checked=False, selected=choice, revision=candidate.revision_id:
                    self.controller.resolve_conflict(selected, revision),
                self.container,
            )
            self.cards.append(card)
            self.cards_layout.addWidget(card, 1)
        self.retranslate()
