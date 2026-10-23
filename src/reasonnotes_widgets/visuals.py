"""Keep editing and list controls while exposing the native window behind them.

The Qt/Kvantum style keeps text, selection, focus, and metrics. Opaque native
input/scroll-area panels are omitted only where they make giant solid blocks.
No application-owned colors or opacity values are used.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QPalette
from PySide6.QtWidgets import (
    QAbstractScrollArea,
    QFrame,
    QLineEdit,
    QProxyStyle,
    QStyle,
    QToolButton,
)


class _IntegratedLineEditStyle(QProxyStyle):
    """Preserve Kvantum control behavior except the solid edit panel."""

    def drawPrimitive(self, element, option, painter, widget=None) -> None:
        if element == QStyle.PrimitiveElement.PE_PanelLineEdit:
            return
        super().drawPrimitive(element, option, painter, widget)


def _omit_large_base_fill(widget) -> None:
    """Use no brush, not a hardcoded transparent RGBA color."""

    palette = widget.palette()
    for group in (
        QPalette.ColorGroup.Active,
        QPalette.ColorGroup.Inactive,
        QPalette.ColorGroup.Disabled,
    ):
        palette.setBrush(group, QPalette.ColorRole.Base, QBrush(Qt.BrushStyle.NoBrush))
        palette.setBrush(
            group, QPalette.ColorRole.AlternateBase, QBrush(Qt.BrushStyle.NoBrush)
        )
    widget.setPalette(palette)
    widget.setAutoFillBackground(False)


def integrate_line_edit(field: QLineEdit) -> None:
    """Native text editing and focus without a large standalone panel."""

    field.setFrame(False)
    _omit_large_base_fill(field)
    # Reuse the previously working object-name-based proxy construction.
    style = _IntegratedLineEditStyle(field.style().objectName())
    style.setParent(field)
    field.setStyle(style)
    field._reasonnotes_line_edit_style = style


def integrate_scroll_surface(view: QAbstractScrollArea) -> None:
    """No rectangle-sized native Base/AlternateBase fill over the window."""

    view.setFrameShape(QFrame.Shape.NoFrame)
    _omit_large_base_fill(view)
    viewport = view.viewport()
    _omit_large_base_fill(viewport)
    viewport.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)


def configure_action_button(button: QToolButton) -> None:
    """Use compact system tool-button chrome instead of opaque command slabs."""

    button.setAutoRaise(True)
    button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
