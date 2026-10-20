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
    # Preserve a qt6ct-style -> Kvantum chain when the platform theme
    # installed one; only the panel primitive is suppressed.
    style = IntegratedLineEditStyle(field.style().objectName())
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


def integrate_solid_surface(view: QAbstractScrollArea, color: QColor) -> None:
    """Make a writing viewport one uniform opaque sheet of ``color``.

    Unlike :func:`integrate_scroll_surface` this keeps an opaque Base brush so
    Qt fills the editable region with exactly that color. No gradient and no
    wallpaper transparency remain inside the surface; the glass material stays
    on the window and card around it.
    """

    opaque = QColor(color)
    if not opaque.isValid() or opaque.alpha() != 255:
        raise ValueError("solid writing surfaces require an opaque color")
    view.setFrameShape(QFrame.Shape.NoFrame)
    for target in (view, view.viewport()):
        palette = target.palette()
        for group in (
            QPalette.ColorGroup.Active,
            QPalette.ColorGroup.Inactive,
            QPalette.ColorGroup.Disabled,
        ):
            palette.setColor(group, QPalette.ColorRole.Base, opaque)
            palette.setColor(
                group, QPalette.ColorRole.AlternateBase, opaque
            )
        target.setPalette(palette)


def configure_action_button(button: QToolButton) -> None:
    """Use compact system tool-button chrome instead of opaque command slabs."""

    button.setAutoRaise(True)
    button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
