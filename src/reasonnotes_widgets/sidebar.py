"""Permanent native notes sidebar matching the established ReasonNotes UI."""

from __future__ import annotations

import math
from pathlib import Path

from PySide6.QtCore import QEvent, QPointF, QRect, QSize, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QIcon,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QPolygonF,
    QRegion,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QSizePolicy,
    QStyle,
    QStyleOptionFrame,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .material import NavigationRail, SearchWell, tinted
from .visuals import integrate_line_edit, integrate_scroll_surface


SIDEBAR_OUTER_MARGIN = 24
SIDEBAR_ICON_COLUMN_WIDTH = 38
SIDEBAR_ICON_SIZE = 24
SIDEBAR_ICON_INSET = (SIDEBAR_ICON_COLUMN_WIDTH - SIDEBAR_ICON_SIZE) // 2
SIDEBAR_TEXT_COLUMN = 48


def _theme_icon(widget: QWidget, names: tuple[str, ...], fallback) -> QIcon:
    """Return the first system-theme icon, retaining a native fallback."""

    for name in names:
        icon = QIcon.fromTheme(name)
        if not icon.isNull():
            return icon
    return widget.style().standardIcon(fallback)


def _draw_line_glyph(name: str, size: int, color: QColor) -> QPixmap:
    """Render one crisp, palette-owned sidebar glyph."""

    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.scale(size / 24.0, size / 24.0)
    pen = QPen(color, 1.9)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    if name == "add":
        painter.drawLine(QPointF(12, 5), QPointF(12, 19))
        painter.drawLine(QPointF(5, 12), QPointF(19, 12))
    elif name == "save":
        outline = QPainterPath()
        outline.moveTo(5, 4)
        outline.lineTo(17, 4)
        outline.lineTo(20, 7)
        outline.lineTo(20, 20)
        outline.lineTo(4, 20)
        outline.lineTo(4, 4)
        outline.closeSubpath()
        painter.drawPath(outline)
        painter.drawRect(8, 4, 8, 6)
        painter.drawLine(QPointF(8, 16), QPointF(16, 16))
    elif name == "sync":
        upper = QPainterPath(QPointF(5, 10))
        upper.cubicTo(QPointF(7, 5), QPointF(15, 4), QPointF(19, 8))
        lower = QPainterPath(QPointF(19, 14))
        lower.cubicTo(QPointF(17, 19), QPointF(9, 20), QPointF(5, 16))
        painter.drawPath(upper)
        painter.drawPath(lower)
        painter.drawPolyline(
            QPolygonF((QPointF(15.2, 8), QPointF(19, 8), QPointF(18.4, 4.4)))
        )
        painter.drawPolyline(
            QPolygonF((QPointF(8.8, 16), QPointF(5, 16), QPointF(5.6, 19.6)))
        )
    elif name == "settings":
        painter.drawEllipse(QPointF(12, 12), 3.2, 3.2)
        painter.drawEllipse(QPointF(12, 12), 7.1, 7.1)
        for step in range(8):
            angle = step * math.pi / 4
            inner = QPointF(12 + math.cos(angle) * 7.2,
                            12 + math.sin(angle) * 7.2)
            outer = QPointF(12 + math.cos(angle) * 9.3,
                            12 + math.sin(angle) * 9.3)
            painter.drawLine(inner, outer)
    elif name == "note":
        painter.drawRoundedRect(7, 3, 12, 16, 1.8, 1.8)
        painter.drawRoundedRect(4, 6, 12, 15, 1.8, 1.8)
        painter.drawLine(QPointF(7, 11), QPointF(13, 11))
        painter.drawLine(QPointF(7, 15), QPointF(12, 15))
        painter.drawLine(QPointF(7, 18), QPointF(10, 18))

    painter.end()
    return pixmap


def _line_icon(name: str, color: QColor) -> QIcon:
    """Create normal, hover, and disabled pixmaps without theme-icon drift."""

    icon = QIcon()
    disabled = QColor(color)
    disabled.setAlpha(168)
    variants = (
        (QIcon.Mode.Normal, QColor(color)),
        (QIcon.Mode.Active, QColor(color).lighter(118)),
        (QIcon.Mode.Disabled, disabled),
    )
    for size in (24, 48):
        for mode, variant in variants:
            icon.addPixmap(
                _draw_line_glyph(name, size, variant), mode, QIcon.State.Off
            )
    return icon


class SidebarActionButton(QToolButton):
    """Full-row action retaining native behavior and original alignment."""

    def __init__(
        self,
        *,
        primary: bool = False,
        prominent: bool = False,
        accented: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self.is_primary = primary
        self.is_prominent = primary or prominent
        self.is_accented = accented
        self.setAutoRaise(not primary)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.setIconSize(QSize(24, 24))
        self.setMinimumHeight(50 if self.is_prominent else 42)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)
        if prominent:
            font = self.font()
            font.setWeight(QFont.Weight.DemiBold)
            self.setFont(font)

    def sizeHint(self) -> QSize:
        width = SIDEBAR_TEXT_COLUMN
        width += self.fontMetrics().horizontalAdvance(self.text()) + 16
        return QSize(max(150, width), 50 if self.is_prominent else 42)

    def icon_rect(self, *, pressed: bool | None = None) -> QRect:
        shift = int(self.isDown() if pressed is None else pressed)
        rect = QRect(
            SIDEBAR_ICON_INSET + shift,
            (self.height() - self.iconSize().height()) // 2 + shift,
            self.iconSize().width(),
            self.iconSize().height(),
        )
        return rect

    def text_rect(self, *, pressed: bool | None = None) -> QRect:
        shift = int(self.isDown() if pressed is None else pressed)
        return self.rect().adjusted(SIDEBAR_TEXT_COLUMN + shift, 0, -12, 0)

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
            text_role = (
                palette.ColorRole.Highlight
                if self.is_accented
                else palette.ColorRole.ButtonText
            )

        if self.hasFocus():
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(tinted(palette.highlight().color(), 210), 1.5))
            painter.drawRoundedRect(bounds.adjusted(1, 1, -1, -1), 7, 7)

        icon_rect = self.icon_rect(pressed=pressed)
        mode = QIcon.Mode.Disabled if not enabled else (
            QIcon.Mode.Active if hovered else QIcon.Mode.Normal
        )
        state = QIcon.State.On if self.isChecked() else QIcon.State.Off
        self.icon().paint(painter, icon_rect, Qt.AlignmentFlag.AlignCenter, mode, state)

        text_rect = self.text_rect(pressed=pressed)
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


class SidebarSearchWell(SearchWell):
    """Kvantum-owned line-edit edge with no independent interior fill."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._focus_source: QLineEdit | None = None
        self.setMouseTracking(True)

    def set_focus_source(self, field: QLineEdit) -> None:
        self._focus_source = field
        field.installEventFilter(self)

    def eventFilter(self, watched, event) -> bool:
        if watched is self._focus_source and event.type() in (
            QEvent.Type.FocusIn,
            QEvent.Type.FocusOut,
            QEvent.Type.Enter,
            QEvent.Type.Leave,
        ):
            self.update()
        return super().eventFilter(watched, event)

    def draw_native_frame(self, painter: QPainter, rect: QRect) -> None:
        option = QStyleOptionFrame()
        option.initFrom(self)
        option.rect = rect
        option.lineWidth = self.style().pixelMetric(
            QStyle.PixelMetric.PM_DefaultFrameWidth, option, self
        )
        if self._focus_source is not None and self._focus_source.hasFocus():
            option.state |= QStyle.StateFlag.State_HasFocus
        frame_width = max(option.lineWidth, 1)
        frame_region = QRegion(rect).subtracted(
            QRegion(
                rect.adjusted(frame_width, frame_width, -frame_width, -frame_width)
            )
        )
        painter.save()
        painter.setClipRegion(frame_region)
        self.style().drawPrimitive(
            QStyle.PrimitiveElement.PE_PanelLineEdit,
            option,
            painter,
            self,
        )
        painter.restore()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        self.draw_native_frame(painter, self.rect())
        painter.end()


class NoteItemDelegate(QStyledItemDelegate):
    """Native full-row note items with the original notebook visual cue."""

    def __init__(self, view: QListView):
        super().__init__(view)
        self.note_icon = _line_icon("note", view.palette().highlight().color())
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
        # Selection remains represented by the model/view state and the
        # semibold title established above. Do not ask the native style to
        # paint a row-sized hover/selection container behind the content.
        native_option.state &= ~(
            QStyle.StateFlag.State_Selected
            | QStyle.StateFlag.State_MouseOver
        )
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
        layout.setContentsMargins(
            SIDEBAR_OUTER_MARGIN,
            SIDEBAR_OUTER_MARGIN,
            SIDEBAR_OUTER_MARGIN,
            18,
        )
        layout.setSpacing(8)

        brand_row = QHBoxLayout()
        brand_row.setSpacing(10)
        self.brand_icon = QLabel(self)
        self.brand_icon.setObjectName("brandIcon")
        self.brand_icon.setFixedSize(SIDEBAR_ICON_COLUMN_WIDTH, 38)
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

        self.new_button = SidebarActionButton(
            prominent=True,
            accented=True,
            parent=self,
        )
        self.save_button = SidebarActionButton(parent=self)
        self.sync_button = SidebarActionButton(parent=self)
        self.delete_button = SidebarActionButton(parent=self)
        self.settings_button = SidebarActionButton(parent=self)
        self.settings_button.setCheckable(True)
        action_color = self.palette().buttonText().color()
        accent_color = self.palette().highlight().color()
        self.new_button.setIcon(_line_icon("add", accent_color))
        self.save_button.setIcon(_line_icon("save", action_color))
        self.sync_button.setIcon(_line_icon("sync", action_color))
        self.settings_button.setIcon(_line_icon("settings", action_color))
        self.delete_button.setIcon(
            _theme_icon(
                self,
                ("edit-delete",),
                QStyle.StandardPixmap.SP_TrashIcon,
            )
        )

        layout.addWidget(self.new_button)
        layout.addSpacing(4)
        layout.addWidget(self.save_button)
        layout.addWidget(self.sync_button)
        layout.addWidget(self.settings_button)
        layout.addWidget(self.delete_button)
        layout.addSpacing(8)

        self.search_well = SidebarSearchWell(self)
        self.search_well.setObjectName("searchWell")
        self.search_well.setMinimumHeight(46)
        search_layout = QHBoxLayout(self.search_well)
        search_layout.setContentsMargins(0, 5, 0, 5)
        search_layout.setSpacing(SIDEBAR_TEXT_COLUMN - SIDEBAR_ICON_COLUMN_WIDTH)
        self.search_icon = QLabel(self.search_well)
        self.search_icon.setObjectName("noteSearchIcon")
        self.search_icon.setFixedSize(
            SIDEBAR_ICON_COLUMN_WIDTH, SIDEBAR_ICON_COLUMN_WIDTH
        )
        self.search_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.search_icon.setPixmap(
            _theme_icon(
                self,
                ("edit-find",),
                QStyle.StandardPixmap.SP_FileDialogContentsView,
            ).pixmap(18, 18)
        )
        search_layout.addWidget(self.search_icon)

        self.search_field = QLineEdit(self.search_well)
        self.search_field.setObjectName("noteSearch")
        self.search_field.setPlaceholderText("Search notes")
        self.search_field.setClearButtonEnabled(True)
        self.search_field.setAccessibleName("Search notes")
        integrate_line_edit(self.search_field)
        self.search_well.set_focus_source(self.search_field)
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
