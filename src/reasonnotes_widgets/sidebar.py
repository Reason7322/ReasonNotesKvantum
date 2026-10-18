"""Permanent native notes sidebar matching the established ReasonNotes UI."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QSizePolicy,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .material import NavigationRail, SearchWell, tinted
from .visuals import integrate_line_edit, integrate_scroll_surface


def _theme_icon(widget: QWidget, names: tuple[str, ...], fallback) -> QIcon:
    """Return the first system-theme icon, retaining a native fallback."""

    for name in names:
        icon = QIcon.fromTheme(name)
        if not icon.isNull():
            return icon
    return widget.style().standardIcon(fallback)


class SidebarActionButton(QToolButton):
    """Full-row action retaining native behavior and original alignment."""

    def __init__(self, *, primary: bool = False, parent=None):
        super().__init__(parent)
        self.is_primary = primary
        self.setAutoRaise(not primary)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.setIconSize(QSize(24, 24))
        self.setMinimumHeight(50 if primary else 42)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)

    def sizeHint(self) -> QSize:
        width = 12 + self.iconSize().width() + 12
        width += self.fontMetrics().horizontalAdvance(self.text()) + 16
        return QSize(max(150, width), 50 if self.is_primary else 42)

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        bounds = self.rect().adjusted(1, 1, -2, -2)
        palette = self.palette()
        enabled = self.isEnabled()
        hovered = self.underMouse()
        pressed = self.isDown()

        if self.is_primary:
            accent = QColor(palette.highlight().color())
            top = accent.lighter(116 if hovered else 109)
            bottom = accent.darker(106 if pressed else 101)
            top.setAlpha(225 if enabled else 95)
            bottom.setAlpha(210 if enabled else 82)
            fill = QLinearGradient(bounds.topLeft(), bounds.bottomLeft())
            fill.setColorAt(0.0, top)
            fill.setColorAt(1.0, bottom)
            painter.setBrush(fill)
            painter.setPen(QPen(tinted(palette.light().color(), 82), 1))
            painter.drawRoundedRect(bounds, 7, 7)
            text_role = palette.ColorRole.HighlightedText
        else:
            if pressed or self.isChecked():
                painter.setBrush(tinted(palette.highlight().color(), 58))
            elif hovered:
                painter.setBrush(tinted(palette.light().color(), 30))
            else:
                painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(Qt.PenStyle.NoPen)
            if painter.brush().style() != Qt.BrushStyle.NoBrush:
                painter.drawRoundedRect(bounds, 7, 7)
            text_role = palette.ColorRole.ButtonText

        if self.hasFocus():
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(tinted(palette.highlight().color(), 210), 1.5))
            painter.drawRoundedRect(bounds.adjusted(1, 1, -1, -1), 7, 7)

        shift = 1 if pressed else 0
        icon_rect = self.rect().adjusted(12 + shift, 0, 0, 0)
        icon_rect.setWidth(self.iconSize().width())
        icon_rect.setHeight(self.iconSize().height())
        icon_rect.moveTop((self.height() - icon_rect.height()) // 2 + shift)
        mode = QIcon.Mode.Disabled if not enabled else (
            QIcon.Mode.Active if hovered else QIcon.Mode.Normal
        )
        state = QIcon.State.On if self.isChecked() else QIcon.State.Off
        self.icon().paint(painter, icon_rect, Qt.AlignmentFlag.AlignCenter, mode, state)

        text_rect = self.rect().adjusted(
            12 + self.iconSize().width() + 12 + shift, 0, -12, 0
        )
        painter.setOpacity(1.0 if enabled else 0.46)
        self.style().drawItemText(
            painter,
            text_rect,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            palette,
            enabled,
            self.text(),
            text_role,
        )
        painter.end()


class NoteItemDelegate(QStyledItemDelegate):
    """Native full-row note items with the original notebook visual cue."""

    def __init__(self, view: QListView):
        super().__init__(view)
        self.note_icon = _theme_icon(
            view,
            ("accessories-text-editor", "document-edit", "x-office-document"),
            QStyle.StandardPixmap.SP_FileIcon,
        )
        self.conflict_icon = _theme_icon(
            view,
            ("emblem-important", "dialog-warning"),
            QStyle.StandardPixmap.SP_MessageBoxWarning,
        )
        self.selected_icon = _theme_icon(
            view,
            ("emblem-checked", "checkbox"),
            QStyle.StandardPixmap.SP_DialogApplyButton,
        )
        self._roles = {
            bytes(name).decode("utf-8"): role
            for role, name in view.model().roleNames().items()
        }

    def sizeHint(self, _option, _index) -> QSize:
        return QSize(180, 56)

    def initStyleOption(self, option, index) -> None:
        super().initStyleOption(option, index)
        option.decorationSize = QSize(22, 22)
        option.decorationPosition = QStyleOptionViewItem.Position.Left
        option.decorationAlignment = Qt.AlignmentFlag.AlignVCenter
        option.displayAlignment = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        option.features |= QStyleOptionViewItem.ViewItemFeature.HasDecoration
        conflicted = bool(index.data(self._roles.get("conflicted", -1)))
        bulk_selected = bool(index.data(self._roles.get("bulkSelected", -1)))
        option.icon = (
            self.selected_icon if bulk_selected
            else self.conflict_icon if conflicted
            else self.note_icon
        )
        option.font.setPixelSize(16)
        if option.state & QStyle.StateFlag.State_Selected:
            option.font.setWeight(QFont.Weight.DemiBold)

    def paint(self, painter, option, index) -> None:
        native_option = QStyleOptionViewItem(option)
        self.initStyleOption(native_option, index)
        style = option.widget.style() if option.widget is not None else self.parent().style()
        style.drawControl(
            QStyle.ControlElement.CE_ItemViewItem,
            native_option,
            painter,
            option.widget,
        )


class NotesSidebar(NavigationRail):
    def __init__(self, model, *, icon_root: Path | None = None, parent=None):
        super().__init__(parent)
        self.setObjectName("notesSidebar")
        self.setMinimumWidth(250)
        self.setMaximumWidth(520)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 18)
        layout.setSpacing(8)

        brand_row = QHBoxLayout()
        brand_row.setSpacing(10)
        self.brand_icon = QLabel(self)
        self.brand_icon.setObjectName("brandIcon")
        self.brand_icon.setFixedSize(38, 38)
        self.brand_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand_text = QHBoxLayout()
        brand_text.setSpacing(0)
        self.brand_reason = QLabel("Reason", self)
        self.brand_reason.setObjectName("brandReason")
        self.brand_notes = QLabel("Notes", self)
        self.brand_notes.setObjectName("brandNotes")
        reason_font = QFont(self.brand_reason.font())
        reason_font.setPixelSize(27)
        reason_font.setWeight(QFont.Weight.DemiBold)
        self.brand_reason.setFont(reason_font)
        notes_font = QFont(reason_font)
        notes_font.setWeight(QFont.Weight.Light)
        self.brand_notes.setFont(notes_font)
        brand_text.addWidget(self.brand_reason)
        brand_text.addWidget(self.brand_notes)
        brand_row.addWidget(self.brand_icon)
        brand_row.addLayout(brand_text)
        brand_row.addStretch(1)
        layout.addLayout(brand_row)
        layout.addSpacing(16)

        self.new_button = SidebarActionButton(primary=True, parent=self)
        self.save_button = SidebarActionButton(parent=self)
        self.sync_button = SidebarActionButton(parent=self)
        self.delete_button = SidebarActionButton(parent=self)
        self.settings_button = SidebarActionButton(parent=self)
        self.settings_button.setCheckable(True)
        button_icons = (
            (self.new_button, ("list-add", "document-new"), QStyle.StandardPixmap.SP_FileIcon),
            (self.save_button, ("document-save",), QStyle.StandardPixmap.SP_DialogSaveButton),
            (self.sync_button, ("view-refresh",), QStyle.StandardPixmap.SP_BrowserReload),
            (self.delete_button, ("edit-delete",), QStyle.StandardPixmap.SP_TrashIcon),
            (self.settings_button, ("settings-configure", "preferences-system"), QStyle.StandardPixmap.SP_FileDialogDetailedView),
        )
        for button, names, fallback in button_icons:
            button.setIcon(_theme_icon(self, names, fallback))

        layout.addWidget(self.new_button)
        layout.addSpacing(4)
        layout.addWidget(self.save_button)
        layout.addWidget(self.sync_button)
        layout.addWidget(self.delete_button)
        layout.addSpacing(8)

        self.search_field = QLineEdit(self)
        self.search_field.setObjectName("noteSearch")
        self.search_field.setPlaceholderText("Search notes")
        self.search_field.setClearButtonEnabled(True)
        self.search_field.setAccessibleName("Search notes")
        self.search_field.addAction(
            _theme_icon(self, ("edit-find",), QStyle.StandardPixmap.SP_FileDialogContentsView),
            QLineEdit.ActionPosition.LeadingPosition,
        )
        integrate_line_edit(self.search_field)
        self.search_well = SearchWell(self)
        self.search_well.setObjectName("searchWell")
        self.search_well.setMinimumHeight(46)
        search_layout = QVBoxLayout(self.search_well)
        search_layout.setContentsMargins(10, 5, 10, 5)
        search_layout.addWidget(self.search_field)
        layout.addWidget(self.search_well)

        self.notes_heading = QLabel("NOTES", self)
        self.notes_heading.setObjectName("notesHeading")
        heading_font = self.notes_heading.font()
        heading_font.setPixelSize(13)
        heading_font.setWeight(QFont.Weight.DemiBold)
        self.notes_heading.setFont(heading_font)
        self.notes_heading.setContentsMargins(4, 8, 0, 2)
        layout.addWidget(self.notes_heading)

        self.list_view = QListView(self)
        self.list_view.setObjectName("noteList")
        self.list_view.setModel(model)
        self.list_view.setSelectionMode(QListView.SelectionMode.ExtendedSelection)
        self.list_view.setSelectionBehavior(QListView.SelectionBehavior.SelectRows)
        self.list_view.setUniformItemSizes(True)
        self.list_view.setEditTriggers(QListView.EditTrigger.NoEditTriggers)
        self.list_view.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.list_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_view.setMouseTracking(True)
        self.list_view.setIconSize(QSize(22, 22))
        self.list_view.setSpacing(2)
        self.list_view.setItemDelegate(NoteItemDelegate(self.list_view))
        integrate_scroll_surface(self.list_view)
        layout.addWidget(self.list_view, 1)

        layout.addSpacing(4)
        layout.addWidget(self.settings_button)

        self.status_area = QWidget(self)
        self.status_area.setObjectName("sidebarStatus")
        status_layout = QVBoxLayout(self.status_area)
        status_layout.setContentsMargins(0, 10, 0, 0)
        status_layout.setSpacing(4)
        self.status_separator = QFrame(self.status_area)
        self.status_separator.setFrameShape(QFrame.Shape.HLine)
        self.status_separator.setFrameShadow(QFrame.Shadow.Plain)
        self.local_status = QLabel("Local: Idle", self.status_area)
        self.local_status.setObjectName("localStatus")
        self.sync_status = QLabel("Phone: Idle", self.status_area)
        self.sync_status.setObjectName("syncStatus")
        for label in (self.local_status, self.sync_status):
            status_font = label.font()
            status_font.setPixelSize(13)
            label.setFont(status_font)
            label.setWordWrap(False)
        status_layout.addWidget(self.status_separator)
        status_layout.addWidget(self.local_status)
        status_layout.addWidget(self.sync_status)
        layout.addWidget(self.status_area)

        if icon_root is not None:
            app_icon = Path(icon_root) / "reasonnotes-yamis.svg"
            if app_icon.is_file():
                self.brand_icon.setPixmap(QIcon(str(app_icon)).pixmap(36, 36))

    def set_brand_text(self, app_name: str) -> None:
        if app_name.casefold().endswith("notes"):
            split = len(app_name) - len("Notes")
            self.brand_reason.setText(app_name[:split])
            self.brand_notes.setText(app_name[split:])
        else:
            self.brand_reason.setText(app_name)
            self.brand_notes.clear()
