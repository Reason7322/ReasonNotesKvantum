"""Small native-widget presentation helpers for Qt/Kvantum windows."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractScrollArea, QLineEdit, QToolButton


def integrate_line_edit(field: QLineEdit) -> None:
    """Keep the active Qt style and palette authoritative for line edits."""


def integrate_scroll_surface(view: QAbstractScrollArea) -> None:
    """Keep the active Qt style and palette authoritative for item views."""


def configure_action_button(button: QToolButton) -> None:
    """Use compact system tool-button chrome instead of opaque command slabs."""

    button.setAutoRaise(True)
    button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
