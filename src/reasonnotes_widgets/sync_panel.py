"""Focused right-edge synchronization drawer."""

from PySide6.QtCore import QEvent, QSize, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPen
from PySide6.QtWidgets import (
    QButtonGroup,
    QDockWidget,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QPushButton,
    QProgressBar,
    QSizePolicy,
    QStyle,
    QStyleOptionButton,
    QStyledItemDelegate,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .material import GlassCard, SearchWell
from .sidebar import SidebarActionButton
from .visuals import (
    configure_action_button,
    integrate_line_edit,
    integrate_scroll_surface,
)


class SyncNoteDelegate(QStyledItemDelegate):
    """Compact note cards with preview, delivery badge, and checkbox."""

    def __init__(self, view: QListView):
        super().__init__(view)
        self._roles = {
            bytes(name).decode("utf-8"): role
            for role, name in view.model().roleNames().items()
        }

    def sizeHint(self, _option, _index) -> QSize:
        return QSize(320, 78)

    def paint(self, painter, option, index) -> None:
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        bounds = option.rect.adjusted(1, 2, -1, -2)
        palette = option.palette
        selected = (
            index.data(Qt.ItemDataRole.CheckStateRole)
            == Qt.CheckState.Checked
        )

        surface = QColor(palette.base().color())
        surface.setAlpha(112 if selected else 74)
        border = QColor(
            palette.highlight().color()
            if selected
            else palette.text().color()
        )
        border.setAlpha(170 if selected else 34)
        painter.setBrush(surface)
        painter.setPen(QPen(border, 1.25 if selected else 1.0))
        painter.drawRoundedRect(bounds, 9, 9)

        indicator = QStyleOptionButton()
        indicator.initFrom(option.widget)
        indicator.state = QStyle.StateFlag.State_Enabled
        indicator.state |= (
            QStyle.StateFlag.State_On
            if selected
            else QStyle.StateFlag.State_Off
        )
        checkbox_size = option.widget.style().pixelMetric(
            QStyle.PixelMetric.PM_IndicatorWidth, indicator, option.widget
        )
        indicator.rect = bounds.adjusted(0, 0, -14, 0)
        indicator.rect.setLeft(indicator.rect.right() - checkbox_size)
        indicator.rect.setTop(bounds.center().y() - checkbox_size // 2)
        indicator.rect.setHeight(checkbox_size)
        option.widget.style().drawControl(
            QStyle.ControlElement.CE_CheckBox,
            indicator,
            painter,
            option.widget,
        )

        title = str(
            index.data(Qt.ItemDataRole.DisplayRole) or "Untitled"
        )
        preview = str(
            index.data(self._roles.get("preview", -1)) or ""
        )
        delivery = str(
            index.data(self._roles.get("deliveryStatus", -1)) or "Local"
        )
        badge_width = max(
            48, option.fontMetrics.horizontalAdvance(delivery) + 18
        )
        badge = bounds.adjusted(0, 0, -(checkbox_size + 24), 0)
        badge.setLeft(badge.right() - badge_width)
        badge.setTop(bounds.center().y() - 13)
        badge.setHeight(26)
        badge_fill = QColor(palette.mid().color())
        badge_fill.setAlpha(105)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(badge_fill)
        painter.drawRoundedRect(badge, 13, 13)
        painter.setPen(palette.text().color())
        painter.drawText(badge, Qt.AlignmentFlag.AlignCenter, delivery)

        text_right = badge.left() - 12
        title_rect = bounds.adjusted(16, 10, 0, 0)
        title_rect.setRight(text_right)
        title_rect.setHeight(25)
        title_font = QFont(option.font)
        title_font.setPixelSize(16)
        title_font.setWeight(
            QFont.Weight.DemiBold if selected else QFont.Weight.Normal
        )
        painter.setFont(title_font)
        painter.setPen(palette.text().color())
        title_metrics = painter.fontMetrics()
        painter.drawText(
            title_rect,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            title_metrics.elidedText(
                title,
                Qt.TextElideMode.ElideRight,
                title_rect.width(),
            ),
        )

        preview_rect = bounds.adjusted(16, 39, 0, -8)
        preview_rect.setRight(text_right)
        preview_color = QColor(palette.text().color())
        preview_color.setAlpha(168)
        preview_font = QFont(option.font)
        preview_font.setPixelSize(13)
        painter.setFont(preview_font)
        painter.setPen(preview_color)
        preview_metrics = painter.fontMetrics()
        painter.drawText(
            preview_rect,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            preview_metrics.elidedText(
                preview or "No preview",
                Qt.TextElideMode.ElideRight,
                preview_rect.width(),
            ),
        )
        painter.restore()

    def editorEvent(self, event, model, option, index) -> bool:
        if (
            event.type() == QEvent.Type.MouseButtonRelease
            and event.button() == Qt.MouseButton.LeftButton
            and option.rect.contains(event.position().toPoint())
        ):
            checked = (
                index.data(Qt.ItemDataRole.CheckStateRole)
                == Qt.CheckState.Checked
            )
            return model.setData(
                index,
                (
                    Qt.CheckState.Unchecked
                    if checked
                    else Qt.CheckState.Checked
                ),
                Qt.ItemDataRole.CheckStateRole,
            )
        return super().editorEvent(event, model, option, index)


class SyncPanel(QDockWidget):
    def __init__(self, controller, translator, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.translator = translator
        self.setObjectName("syncPanel")
        self.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        self.setFeatures(
            QDockWidget.DockWidgetFeature.NoDockWidgetFeatures
        )
        self.setMinimumWidth(460)
        self.setMaximumWidth(580)

        # The drawer owns its close action; suppress the redundant native
        # dock title strip while keeping it docked to the main window.
        title_bar = QWidget(self)
        title_bar.setFixedHeight(1)
        self.setTitleBarWidget(title_bar)

        content = QWidget(self)
        content.setObjectName("syncDrawer")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 20, 24, 22)
        layout.setSpacing(13)

        header = QHBoxLayout()
        header.setSpacing(12)
        self.heading = QLabel(content)
        heading_font = QFont(self.heading.font())
        heading_font.setPixelSize(28)
        heading_font.setWeight(QFont.Weight.DemiBold)
        self.heading.setFont(heading_font)
        self.close_button = QToolButton(content)
        configure_action_button(self.close_button)
        self.close_button.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextOnly
        )
        self.close_button.setText("×")
        self.close_button.setMinimumSize(36, 36)
        close_font = QFont(self.close_button.font())
        close_font.setPixelSize(24)
        self.close_button.setFont(close_font)
        self.close_button.setAccessibleName("Close synchronization")
        header.addWidget(self.heading, 1)
        header.addWidget(self.close_button)

        self.subtitle = QLabel(content)
        self.subtitle.setWordWrap(True)

        scope = QHBoxLayout()
        scope.setSpacing(8)
        self.all_button = QPushButton(content)
        self.selected_button = QPushButton(content)
        self.scope_group = QButtonGroup(content)
        self.scope_group.setExclusive(True)
        for button in (self.all_button, self.selected_button):
            button.setCheckable(True)
            button.setMinimumHeight(48)
            button.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Fixed,
            )
            self.scope_group.addButton(button)
            scope.addWidget(button, 1)
        self.all_button.setChecked(True)

        self.all_summary_card = GlassCard(content)
        all_layout = QVBoxLayout(self.all_summary_card)
        all_layout.setContentsMargins(22, 18, 22, 19)
        all_layout.setSpacing(6)
        self.all_summary_heading = QLabel(self.all_summary_card)
        summary_font = QFont(self.all_summary_heading.font())
        summary_font.setPixelSize(17)
        summary_font.setWeight(QFont.Weight.DemiBold)
        self.all_summary_heading.setFont(summary_font)
        self.all_summary = QLabel(self.all_summary_card)
        self.all_summary.setWordWrap(True)
        all_layout.addWidget(self.all_summary_heading)
        all_layout.addWidget(self.all_summary)

        self.selection_section = QWidget(content)
        selected_layout = QVBoxLayout(self.selection_section)
        selected_layout.setContentsMargins(0, 0, 0, 0)
        selected_layout.setSpacing(9)
        search_well = SearchWell(self.selection_section)
        search_layout = QHBoxLayout(search_well)
        search_layout.setContentsMargins(12, 6, 12, 6)
        self.search_field = QLineEdit(search_well)
        self.search_field.setObjectName("syncSearch")
        self.search_field.setClearButtonEnabled(True)
        self.search_field.addAction(
            QIcon.fromTheme(
                "edit-find",
                self.style().standardIcon(
                    QStyle.StandardPixmap.SP_FileDialogContentsView
                ),
            ),
            QLineEdit.ActionPosition.LeadingPosition,
        )
        integrate_line_edit(self.search_field)
        search_layout.addWidget(self.search_field)

        selection_actions = QHBoxLayout()
        selection_actions.setSpacing(8)
        self.select_all_button = QToolButton(self.selection_section)
        self.clear_button = QToolButton(self.selection_section)
        for button in (self.select_all_button, self.clear_button):
            configure_action_button(button)
        self.select_all_button.setIcon(
            self.style().standardIcon(
                QStyle.StandardPixmap.SP_DialogApplyButton
            )
        )
        self.clear_button.setIcon(
            self.style().standardIcon(
                QStyle.StandardPixmap.SP_DialogResetButton
            )
        )
        self.selection_count = QLabel(self.selection_section)
        selection_actions.addWidget(self.select_all_button)
        selection_actions.addWidget(self.clear_button)
        selection_actions.addStretch(1)
        selection_actions.addWidget(self.selection_count)

        self.note_list = QListView(self.selection_section)
        self.note_list.setObjectName("syncNoteList")
        self.note_list.setModel(controller.sync_model)
        self.note_list.setItemDelegate(SyncNoteDelegate(self.note_list))
        self.note_list.setEditTriggers(
            QListView.EditTrigger.NoEditTriggers
        )
        self.note_list.setSpacing(6)
        self.note_list.setUniformItemSizes(True)
        integrate_scroll_surface(self.note_list)
        selected_layout.addWidget(search_well)
        selected_layout.addLayout(selection_actions)
        selected_layout.addWidget(self.note_list, 1)

        self.action_card = GlassCard(content)
        action_layout = QVBoxLayout(self.action_card)
        action_layout.setContentsMargins(22, 17, 22, 18)
        action_layout.setSpacing(7)
        self.action_context = QLabel(self.action_card)
        context_font = QFont(self.action_context.font())
        context_font.setWeight(QFont.Weight.DemiBold)
        self.action_context.setFont(context_font)
        self.action_context.setWordWrap(True)
        self.receipt_notice = QLabel(self.action_card)
        self.receipt_notice.setWordWrap(True)
        self.status_label = QLabel(self.action_card)
        self.status_label.setWordWrap(True)
        self.progress_bar = QProgressBar(self.action_card)
        self.progress_bar.setObjectName("syncProgress")
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setVisible(False)
        actions = QHBoxLayout()
        actions.setSpacing(10)
        self.cancel_button = QToolButton(self.action_card)
        configure_action_button(self.cancel_button)
        self.cancel_button.setIcon(
            self.style().standardIcon(
                QStyle.StandardPixmap.SP_DialogCancelButton
            )
        )
        self.start_button = SidebarActionButton(
            primary=True, parent=self.action_card
        )
        self.start_button.setIcon(
            QIcon.fromTheme(
                "document-send",
                self.style().standardIcon(
                    QStyle.StandardPixmap.SP_ArrowForward
                ),
            )
        )
        actions.addWidget(self.cancel_button)
        actions.addWidget(self.start_button, 1)
        action_layout.addWidget(self.action_context)
        action_layout.addWidget(self.receipt_notice)
        action_layout.addWidget(self.status_label)
        action_layout.addWidget(self.progress_bar)
        action_layout.addLayout(actions)

        layout.addLayout(header)
        layout.addWidget(self.subtitle)
        layout.addLayout(scope)
        layout.addWidget(self.all_summary_card)
        layout.addWidget(self.selection_section, 1)
        layout.addWidget(self.action_card)
        layout.addStretch(1)
        self.setWidget(content)

        self.all_button.toggled.connect(self.refresh)
        self.selected_button.toggled.connect(self.refresh)
        self.search_field.textChanged.connect(
            controller.set_sync_search
        )
        self.select_all_button.clicked.connect(
            controller.select_all_sync_notes
        )
        self.clear_button.clicked.connect(
            controller.clear_sync_selection
        )
        self.close_button.clicked.connect(self.hide)
        self.cancel_button.clicked.connect(self.hide)
        self.start_button.clicked.connect(self.start_sync)
        controller.selection_changed.connect(self.refresh)
        controller.models_changed.connect(self.refresh)
        controller.state_changed.connect(self.refresh)
        translator.language_changed.connect(
            lambda _language: self.retranslate()
        )
        self.retranslate()

    def _copy(self, english: str, polish: str) -> str:
        return (
            polish
            if self.translator.language == "pl"
            else english
        )

    def retranslate(self) -> None:
        tr = self.translator.text
        self.setWindowTitle(tr("sync"))
        self.heading.setText(
            self._copy("Synchronize notes", "Synchronizuj notatki")
        )
        self.subtitle.setText(
            self._copy(
                "Choose what this device requests through KDE Connect.",
                "Wybierz, o co to urządzenie poprosi przez KDE Connect.",
            )
        )
        self.all_button.setText(tr("all_notes"))
        self.selected_button.setText(tr("selected_notes"))
        self.all_summary_heading.setText(tr("all_notes"))
        self.all_summary.setText(
            self._copy(
                "Every eligible pending revision from every note is included.",
                "Uwzględnione zostaną wszystkie oczekujące wersje każdej notatki.",
            )
        )
        self.search_field.setPlaceholderText(tr("search_notes"))
        self.select_all_button.setText(tr("select_all"))
        self.clear_button.setText(tr("clear"))
        self.cancel_button.setText(tr("cancel"))
        self.receipt_notice.setText(
            self._copy(
                "A transfer request is not delivery. Confirmed appears only after durable receipt import.",
                "Żądanie transferu nie jest dostarczeniem. Potwierdzenie pojawia się dopiero po trwałym imporcie pokwitowania.",
            )
        )
        self.refresh()

    def refresh(self) -> None:
        selected_mode = self.selected_button.isChecked()
        self.selection_section.setVisible(selected_mode)
        self.all_summary_card.setVisible(not selected_mode)
        count = len(self.controller.sync_selected_ids)
        self.selection_count.setText(
            self._copy(f"{count} selected", f"Wybrano: {count}")
        )
        if selected_mode:
            self.action_context.setText(
                self._copy(
                    "Only the checked notes will be requested for transfer.",
                    "Tylko zaznaczone notatki zostaną objęte żądaniem transferu.",
                )
            )
            self.start_button.setText(
                self._copy(
                    f"Sync selected ({count})",
                    f"Synchronizuj wybrane ({count})",
                )
            )
        else:
            self.action_context.setText(
                self._copy(
                    "All eligible notes will be requested for transfer.",
                    "Wszystkie kwalifikujące się notatki zostaną objęte żądaniem transferu.",
                )
            )
            self.start_button.setText(
                self._copy(
                    "Sync all notes",
                    "Synchronizuj wszystkie",
                )
            )
        presenter = self.controller.presenter
        state = self.translator.text(
            presenter.sync_state.casefold()
        )
        status = self._copy("Status", "Stan") + f": {state}"
        if presenter.sync_message:
            status += f" — {presenter.sync_message}"
        self.status_label.setText(status)
        self.progress_bar.setVisible(presenter.sync_state == "Running")
        self.start_button.setEnabled(
            presenter.sync_state != "Running"
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
