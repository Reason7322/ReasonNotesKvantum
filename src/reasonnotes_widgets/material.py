"""Application layout surfaces derived from the active Qt/Kvantum palette.

Kvantum still draws the actual controls. These widgets only establish a
coherent, softly separated reading and navigation hierarchy, without QSS,
bundled theme resources, or window-sized opaque overlays.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import QWidget


def tinted(color: QColor, alpha: int, *, brighten: int = 0) -> QColor:
    """Preserve system hue and clamp an additive translucency layer."""
    result = QColor(color)
    if brighten:
        result = result.lighter(100 + brighten)
    result.setAlpha(max(0, min(255, alpha)))
    return result


class NavigationRail(QWidget):
    """Small translucent tint and a thin edge, not an opaque sidebar slab."""

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        palette = self.palette()
        surface = palette.window().color()
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0.0, tinted(surface, 108, brighten=8))
        gradient.setColorAt(0.55, tinted(surface, 90))
        gradient.setColorAt(1.0, tinted(surface, 114))
        painter.fillRect(event.rect(), gradient)
        separator = tinted(palette.text().color(), 28)
        painter.setPen(QPen(separator, 1))
        painter.drawLine(self.width() - 1, 18, self.width() - 1, self.height() - 18)
        painter.end()


class GlassCard(QWidget):
    """A quiet frosted writing/settings surface with a themed outline."""

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        bounds = self.rect().adjusted(1, 1, -2, -2)
        palette = self.palette()
        base = palette.base().color()
        window = palette.window().color()
        top = tinted(base, 88, brighten=12)
        bottom = tinted(window, 62, brighten=5)
        fill = QLinearGradient(bounds.topLeft(), bounds.bottomLeft())
        fill.setColorAt(0, top)
        fill.setColorAt(1, bottom)
        painter.setPen(QPen(tinted(palette.text().color(), 35), 1))
        painter.setBrush(fill)
        painter.drawRoundedRect(bounds, 13, 13)
        # The upper reflection reads as a glass edge without extra controls.
        painter.setPen(QPen(tinted(palette.light().color(), 42), 1))
        painter.drawLine(bounds.left() + 18, bounds.top() + 1,
                         bounds.right() - 18, bounds.top() + 1)
        painter.end()


class SearchWell(QWidget):
    """A small, native-theme-tinted search surround, never a black slab."""

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(1, 1, -2, -2)
        color = self.palette().base().color()
        painter.setPen(QPen(tinted(self.palette().text().color(), 33), 1))
        painter.setBrush(tinted(color, 72))
        painter.drawRoundedRect(rect, 8, 8)
        painter.end()


class TitleRule(QWidget):
    """Single quiet line establishing an editable heading."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(2)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        line = QLinearGradient(0, 0, self.width(), 0)
        highlight = self.palette().highlight().color()
        line.setColorAt(0.0, tinted(highlight, 98))
        line.setColorAt(0.65, tinted(highlight, 30))
        line.setColorAt(1.0, tinted(highlight, 0))
        painter.fillRect(self.rect(), line)
        painter.end()
