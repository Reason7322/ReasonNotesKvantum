"""Small native-widget presentation helpers for translucent Kvantum windows.

These helpers deliberately avoid style sheets and custom painting.  Kvantum
continues to own text, focus, hover, selection, metrics, and icon rendering;
only the large opaque base brush/frame is removed from writing surfaces so the
top-level system material remains visible.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QAbstractScrollArea, QFrame, QLineEdit, QToolButton


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
