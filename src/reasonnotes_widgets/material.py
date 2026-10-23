"""Application layout surfaces derived from the active Qt/Kvantum palette.

Kvantum still draws the actual controls. These widgets only establish a
coherent, softly separated reading and navigation hierarchy, without QSS,
bundled theme resources, or window-sized opaque overlays.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import (
    QColor,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import QStyle, QStyleOption, QWidget


class _NativeStyleSurface:
    """Let the active Qt style own this widget's complete surface."""

    def _initialize_native_style_surface(self) -> None:
        self._native_style_enabled = False

    @property
    def native_style_enabled(self) -> bool:
        return self._native_style_enabled

    def set_native_style_enabled(self, enabled: bool) -> None:
        self._native_style_enabled = bool(enabled)
        self.update()

    def _paint_native_style_surface(self, painter: QPainter) -> None:
        option = QStyleOption()
        option.initFrom(self)
        self.style().drawPrimitive(
            QStyle.PrimitiveElement.PE_Widget,
            option,
            painter,
            self,
        )


def tinted(color: QColor, alpha: int, *, brighten: int = 0) -> QColor:
    """Preserve system hue and clamp an additive translucency layer."""
    result = QColor(color)
    if brighten:
        result = result.lighter(100 + brighten)
    result.setAlpha(max(0, min(255, alpha)))
    return result


class NavigationRail(_NativeStyleSurface, QWidget):
    """Small translucent tint without a painted boundary edge."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._initialize_native_style_surface()
        self._material_fill_enabled = True

    @property
    def material_fill_enabled(self) -> bool:
        return self._material_fill_enabled

    def set_material_fill_enabled(self, enabled: bool) -> None:
        self._material_fill_enabled = bool(enabled)
        self.update()

    def paintEvent(self, event) -> None:
        if self._native_style_enabled:
            # Replace, rather than overlay, the parent's window material in
            # the navigation rail. The active Kvantum Base brush carries its
            # own theme-defined transparency; no application color or alpha.
            painter = QPainter(self)
            painter.setCompositionMode(
                QPainter.CompositionMode.CompositionMode_Source
            )
            painter.fillRect(event.rect(), self.palette().base())
            painter.end()
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        palette = self.palette()
        if self._material_fill_enabled:
            surface = palette.window().color()
            gradient = QLinearGradient(0, 0, 0, self.height())
            gradient.setColorAt(0.0, tinted(surface, 108, brighten=8))
            gradient.setColorAt(0.55, tinted(surface, 90))
            gradient.setColorAt(1.0, tinted(surface, 114))
            painter.fillRect(event.rect(), gradient)
        painter.end()


class GlassCard(_NativeStyleSurface, QWidget):
    """A quiet frosted writing/settings surface with a themed outline."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._initialize_native_style_surface()
        self._material_fill_enabled = True

    @property
    def material_fill_enabled(self) -> bool:
        return self._material_fill_enabled

    def set_material_fill_enabled(self, enabled: bool) -> None:
        self._material_fill_enabled = bool(enabled)
        self.update()

    def paintEvent(self, event) -> None:
        if self._native_style_enabled:
            # The parent already carries the native material: no card-sized
            # extra PE_Widget layer and no custom gradient/fixed color.
            return
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
        painter.setBrush(
            fill if self._material_fill_enabled else Qt.BrushStyle.NoBrush
        )
        painter.drawRoundedRect(bounds, 13, 13)
        if not self._material_fill_enabled:
            # The Kitty-equivalent sheet is already one continuous material,
            # so a transparent card needs its separation from the boundary
            # itself. Concentric strokes fading inward over a few pixels
            # read as a glass rim; clipping to the card shape keeps them off
            # the surrounding sheet, and the interior stays fill-free.
            depth = QPainterPath()
            depth.addRoundedRect(bounds, 13, 13)
            painter.setClipPath(depth)
            light = palette.light().color()
            steps = 9
            for step in range(steps):
                alpha = int(18 * (steps - step) / steps)
                width = 2 * (step + 1)
                painter.setPen(QPen(tinted(light, max(alpha, 1)), width))
                painter.drawRoundedRect(bounds, 13, 13)
            painter.setClipping(False)
        # The upper reflection reads as a glass edge without extra controls.
        painter.setPen(QPen(tinted(palette.light().color(), 42), 1))
        painter.drawLine(bounds.left() + 18, bounds.top() + 1,
                         bounds.right() - 18, bounds.top() + 1)
        painter.end()


class SearchWell(_NativeStyleSurface, QWidget):
    """A small, native-theme-tinted search surround, never a black slab."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._initialize_native_style_surface()

    def paintEvent(self, event) -> None:
        if self._native_style_enabled:
            # This is a layout surround, not another independent window.
            return
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
