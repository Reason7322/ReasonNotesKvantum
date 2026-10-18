"""Native Qt widget surfaces using the active system QStyle.

The parent application must use the real qt6ct->Kvantum style chain where
available. No hard-coded colors, app-owned theme, QSS, or decorative drawing.
"""

from __future__ import annotations

from PySide6.QtWidgets import QFrame
from PySide6.QtGui import QPalette


class NavigationRail(QFrame):
    """The native framed sidebar, retaining the resizable layout."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.NoFrame)


class GlassCard(QFrame):
    """Native framed writing/settings region, not custom-painted glass."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Plain)
        # Qt draws the real Kvantum Base brush, not a fake LiquidGlass layer.
        self.setBackgroundRole(QPalette.ColorRole.Base)
        self.setAutoFillBackground(True)


class SearchWell(QFrame):
    """Native inset for the frameless search control."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Plain)
        # The transparent native line edit uses its surrounding frame here,
        # while the parent's window material remains visible.
        self.setAutoFillBackground(False)


class TitleRule(QFrame):
    """Qt/Kvantum-rendered divider, never a handwritten gradient."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.HLine)
        self.setFrameShadow(QFrame.Shadow.Sunken)
        self.setFixedHeight(2)
