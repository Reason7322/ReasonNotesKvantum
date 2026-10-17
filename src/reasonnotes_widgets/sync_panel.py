"""Right-edge native synchronization panel."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDockWidget, QHBoxLayout, QLabel, QLineEdit, QListView, QPushButton,
    QRadioButton, QVBoxLayout, QWidget,
)


class SyncPanel(QDockWidget):
    def __init__(self, controller, translator, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.translator = translator
        self.setObjectName("syncPanel")
        self.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        self.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetClosable)
        self.setMinimumWidth(420)
        self.setMaximumWidth(600)
        content = QWidget(self)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)
        self.subtitle = QLabel(content)
        self.subtitle.setWordWrap(True)
        modes = QHBoxLayout()
        self.all_button = QRadioButton(content)
        self.selected_button = QRadioButton(content)
        self.all_button.setChecked(True)
        modes.addWidget(self.all_button)
        modes.addWidget(self.selected_button)
        self.all_summary = QLabel(content)
        self.all_summary.setWordWrap(True)
        self.search_field = QLineEdit(content)
        self.search_field.setClearButtonEnabled(True)
        selection_actions = QHBoxLayout()
        self.select_all_button = QPushButton(content)
        self.clear_button = QPushButton(content)
        self.selection_count = QLabel(content)
        selection_actions.addWidget(self.select_all_button)
        selection_actions.addWidget(self.clear_button)
        selection_actions.addStretch(1)
        selection_actions.addWidget(self.selection_count)
        self.note_list = QListView(content)
        self.note_list.setModel(controller.sync_model)
        self.note_list.setEditTriggers(QListView.EditTrigger.NoEditTriggers)
        self.receipt_notice = QLabel(content)
        self.receipt_notice.setWordWrap(True)
        footer = QHBoxLayout()
        self.cancel_button = QPushButton(content)
        self.start_button = QPushButton(content)
        footer.addStretch(1)
        footer.addWidget(self.cancel_button)
        footer.addWidget(self.start_button)
        layout.addWidget(self.subtitle)
        layout.addLayout(modes)
        layout.addWidget(self.all_summary)
        layout.addWidget(self.search_field)
        layout.addLayout(selection_actions)
        layout.addWidget(self.note_list, 1)
        layout.addWidget(self.receipt_notice)
        layout.addLayout(footer)
        self.setWidget(content)
        self.all_button.toggled.connect(self.refresh)
        self.selected_button.toggled.connect(self.refresh)
        self.search_field.textChanged.connect(controller.set_sync_search)
        self.select_all_button.clicked.connect(controller.select_all_sync_notes)
        self.clear_button.clicked.connect(controller.clear_sync_selection)
        self.cancel_button.clicked.connect(self.hide)
        self.start_button.clicked.connect(self.start_sync)
        controller.selection_changed.connect(self.refresh)
        controller.models_changed.connect(self.refresh)
        controller.state_changed.connect(self.refresh)
        translator.language_changed.connect(lambda _language: self.retranslate())
        self.retranslate()

    def retranslate(self) -> None:
        tr = self.translator.text
        polish = self.translator.language == "pl"
        self.setWindowTitle(tr("sync"))
        self.subtitle.setText(
            "Wybierz notatki wysyłane przez KDE Connect. Żądanie transferu nie jest potwierdzeniem dostarczenia."
            if polish else
            "Choose notes to request through KDE Connect. A transfer request is not a delivery confirmation."
        )
        self.all_button.setText(tr("all_notes"))
        self.selected_button.setText(tr("selected_notes"))
        self.all_summary.setText(
            "Wyślij wszystkie oczekujące wersje kwalifikujące się do wysłania."
            if polish else "Send every eligible pending revision."
        )
        self.search_field.setPlaceholderText(tr("search_notes"))
        self.select_all_button.setText(tr("select_all"))
        self.clear_button.setText(tr("clear"))
        self.cancel_button.setText(tr("cancel"))
        self.start_button.setText(tr("start_sync"))
        self.receipt_notice.setText(
            "Potwierdzono oznacza, że urządzenie zwróciło trwały dowód importu."
            if polish else
            "Confirmed means the peer returned durable import evidence."
        )
        self.refresh()

    def refresh(self) -> None:
        selected_mode = self.selected_button.isChecked()
        for widget in (
            self.search_field, self.select_all_button, self.clear_button,
            self.selection_count, self.note_list,
        ):
            widget.setVisible(selected_mode)
        self.all_summary.setVisible(not selected_mode)
        count = len(self.controller.sync_selected_ids)
        self.selection_count.setText(str(count))
        self.start_button.setEnabled(
            self.controller.presenter.sync_state != "Running"
            and (not selected_mode or count > 0)
        )

    def start_sync(self) -> None:
        started = (
            self.controller.sync_selected()
            if self.selected_button.isChecked()
            else self.controller.sync_all()
        )
        if started:
            self.refresh()
