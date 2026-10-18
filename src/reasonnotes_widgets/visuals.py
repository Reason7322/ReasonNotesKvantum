"""Small native-widget presentation helpers for translucent Kvantum windows.

These helpers deliberately avoid style sheets and custom painting.  Kvantum
continues to own text, focus, hover, selection, metrics, and icon rendering;
only the large opaque base brush/frame is removed from writing surfaces so the
top-level system material remains visible.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QAbstractScrollArea,
    QFrame,
    QLineEdit,
    QProxyStyle,
    QStyle,
    QToolButton,
)


class IntegratedLineEditStyle(QProxyStyle):
    """Kvantum proxy that omits only its forced line-edit panel.

    Kvantum deliberately renders ``PE_PanelLineEdit`` even when
    ``QLineEdit.hasFrame()`` is false.  The proxy keeps a real Kvantum base
    style for every other metric, icon, state, and primitive while leaving the
    panel pixels to the translucent top-level material.
    """

    def drawPrimitive(self, element, option, painter, widget=None) -> None:
        if element == QStyle.PrimitiveElement.PE_PanelLineEdit:
            return
        super().drawPrimitive(element, option, painter, widget)


def _clear_base_brush(widget) -> None:
    palette = widget.palette()
    transparent = QColor(0, 0, 0, 0)
    for group in (
        QPalette.ColorGroup.Active,
        QPalette.ColorGroup.Inactive,
        QPalette.ColorGroup.Disabled,
    ):
        palette.setColor(group, QPalette.ColorRole.Base, transparent)
        palette.setColor(group, QPalette.ColorRole.AlternateBase, transparent)
    widget.setPalette(palette)
    widget.setAutoFillBackground(False)


def integrate_line_edit(field: QLineEdit) -> None:
    """Keep native editing behavior without Kvantum's opaque input slab."""

    field.setFrame(False)
    _clear_base_brush(field)
    style = IntegratedLineEditStyle("kvantum")
    style.setParent(field)
    field.setStyle(style)
    field._reasonnotes_line_edit_style = style


def integrate_scroll_surface(view: QAbstractScrollArea) -> None:
    """Expose the window material behind an editor or item-view viewport."""

    view.setFrameShape(QFrame.Shape.NoFrame)
    _clear_base_brush(view)
    viewport = view.viewport()
    _clear_base_brush(viewport)
    viewport.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)


def configure_action_button(button: QToolButton) -> None:
    """Use compact system tool-button chrome instead of opaque command slabs."""

    button.setAutoRaise(True)
    button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)


def action_icon(name: str, palette) -> QIcon:
    """Consistent monochrome line icons, independent of missing icon themes.

    All chrome remains native/Kvantum-drawn. Only the tiny pictograms are
    application-owned so Qt does not fall back to unrelated file-manager icons.
    """
    from PySide6.QtCore import QPointF, QRectF
    from PySide6.QtGui import QIcon, QPainter, QPen, QPixmap

    image = QPixmap(48, 48)
    image.fill(Qt.GlobalColor.transparent)
    image.setDevicePixelRatio(2)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    ink = QColor(palette.text().color())
    ink.setAlpha(226)
    painter.setPen(QPen(ink, 1.7, Qt.PenStyle.SolidLine,
                        Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    painter.setBrush(Qt.BrushStyle.NoBrush)

    def line(x1, y1, x2, y2):
        painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

    if name == "new":
        painter.drawRoundedRect(QRectF(5, 3, 12, 18), 1.5, 1.5)
        line(9, 8, 14, 8)
        line(9, 11, 13, 11)
        painter.setBrush(palette.window().color())
        painter.drawEllipse(QPointF(17, 17), 5, 5)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        line(17, 14, 17, 20)
        line(14, 17, 20, 17)
    elif name == "save":
        painter.drawRoundedRect(QRectF(4, 4, 16, 16), 2, 2)
        painter.drawRect(QRectF(8, 4, 8, 6))
        line(12, 5.5, 12, 8)
        painter.drawRoundedRect(QRectF(8, 13, 8, 7), 1, 1)
    elif name == "sync":
        painter.drawArc(QRectF(5, 5, 14, 14), 35 * 16, 145 * 16)
        painter.drawArc(QRectF(5, 5, 14, 14), 215 * 16, 145 * 16)
        line(5, 7, 5, 12)
        line(5, 12, 10, 12)
        line(19, 17, 19, 12)
        line(19, 12, 14, 12)
    elif name == "delete":
        line(5, 7, 19, 7)
        line(10, 5, 14, 5)
        line(8, 10, 9, 19)
        line(16, 10, 15, 19)
        line(11, 10, 11, 17)
        line(13, 10, 13, 17)
        line(9, 19, 15, 19)
    elif name == "settings":
        for y, center in ((6, 9), (12, 16), (18, 11)):
            line(4, y, center - 3, y)
            line(center + 3, y, 20, y)
            painter.drawEllipse(QPointF(center, y), 2.2, 2.2)
    elif name == "search":
        painter.drawEllipse(QRectF(5, 4, 11, 11))
        line(14, 14, 20, 20)
    painter.end()
    return QIcon(image)
