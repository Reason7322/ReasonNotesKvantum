"""Optional compositor blur for the native Qt Widgets top-level surface.

The helper uses Qt's existing Wayland connection and the compositor's
``ext-background-effect-v1`` protocol.  It never changes compositor or
Kvantum configuration.  Unsupported sessions receive an opaque palette
fallback so the application remains readable.
"""

from __future__ import annotations

import ctypes
import logging
from pathlib import Path

from PySide6.QtCore import QObject, Property, Qt, Signal, Slot, qVersion
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QWidget


_LOG = logging.getLogger(__name__)
_NATIVE_LIBRARY = (
    Path(__file__).resolve().parents[2]
    / "linux-app"
    / "native"
    / "libreasonnotes_wayland_blur.so"
)


def prepare_translucent_surface(
    window: QWidget, *, platform_name: str | None = None
) -> bool:
    """Prepare a Wayland top-level for an alpha-bearing framebuffer.

    Qt requires ``WA_TranslucentBackground`` before the native surface is
    created.  The actual compositor effect is attached after ``show()`` when
    ``winId()`` identifies the live ``wl_surface``.
    """

    platform = platform_name
    if platform is None:
        application = QGuiApplication.instance()
        platform = application.platformName() if application is not None else ""
    if platform.casefold() != "wayland":
        return False
    window.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
    window.setAutoFillBackground(False)
    return True


class QWidgetBlurController(QObject):
    """Own one native compositor effect for one top-level QWidget."""

    active_changed = Signal(bool)

    def __init__(self, library_path: Path | None = None, parent=None):
        super().__init__(parent)
        self.library_path = (
            Path(library_path) if library_path is not None else _NATIVE_LIBRARY
        )
        self._library = None
        self._handle = None
        self._window: QWidget | None = None
        self._active = False
        self._last_error = ""

    @Property(bool, notify=active_changed)
    def active(self) -> bool:
        return self._active

    @property
    def window(self) -> QWidget | None:
        return self._window

    @property
    def last_error(self) -> str:
        return self._last_error

    def attach(self, window: QWidget) -> None:
        """Attach after the top-level is shown and has a native surface."""

        if self._window is not None:
            raise RuntimeError("Wayland blur may be attached to one window only")
        self._window = window
        self.refresh()

    def _set_active(self, active: bool) -> None:
        if active == self._active:
            return
        self._active = active
        self.active_changed.emit(active)
        if self._window is not None:
            self._window.update()

    def _load_native(self) -> bool:
        if self._library is not None:
            return True
        try:
            library = ctypes.CDLL(str(self.library_path))
            library.rn_blur_enable.argtypes = [
                ctypes.c_void_p,
                ctypes.c_void_p,
                ctypes.c_void_p,
                ctypes.POINTER(ctypes.c_int),
            ]
            library.rn_blur_enable.restype = ctypes.c_void_p
            library.rn_blur_disable.argtypes = [ctypes.c_void_p]
            library.rn_blur_disable.restype = None
        except (OSError, AttributeError) as error:
            self._last_error = f"Native Wayland blur helper unavailable: {error}"
            _LOG.warning("%s", self._last_error)
            return False
        self._library = library
        return True

    def _opaque_fallback(self) -> None:
        if self._window is None:
            return
        palette = self._window.palette()
        color = palette.window().color()
        color.setAlpha(255)
        palette.setColor(palette.ColorRole.Window, color)
        self._window.setPalette(palette)
        self._window.setAutoFillBackground(True)

    @Slot()
    def refresh(self) -> None:
        if self._window is None:
            return
        application = QGuiApplication.instance()
        if application is None or application.platformName().casefold() != "wayland":
            self.disable()
            self._last_error = "Compositor blur is available only on Wayland"
            self._opaque_fallback()
            return
        major_minor = tuple(int(part) for part in qVersion().split(".")[:2])
        if major_minor < (6, 9):
            self.disable()
            self._last_error = "Qt Wayland surface pointers require Qt 6.9+"
            self._opaque_fallback()
            return
        if self._handle is not None:
            return
        if not self._load_native():
            self._opaque_fallback()
            return
        try:
            native = application.nativeInterface()
            display = int(native.display())
            compositor = int(native.compositor())
            surface = int(self._window.winId())
            if not all((display, compositor, surface)):
                raise RuntimeError("Qt Wayland surface not initialized")
            result = ctypes.c_int(-99)
            handle = self._library.rn_blur_enable(
                display, compositor, surface, ctypes.byref(result)
            )
            if not handle or result.value != 0:
                self._last_error = (
                    "Wayland compositor blur not available: "
                    f"code {result.value}"
                )
                _LOG.info("%s", self._last_error)
                self._opaque_fallback()
                return
        except (AttributeError, RuntimeError, TypeError, ValueError, OverflowError) as error:
            self._last_error = f"Wayland compositor blur failed: {error}"
            _LOG.warning("%s", self._last_error)
            self._opaque_fallback()
            return
        self._handle = handle
        self._last_error = ""
        self._window.setAutoFillBackground(False)
        self._set_active(True)

    def disable(self) -> None:
        self._set_active(False)
        if self._handle is None:
            return
        self._library.rn_blur_disable(self._handle)
        self._handle = None

    def close(self) -> None:
        """Release the effect before Qt destroys the surface and display."""

        self.disable()
        self._window = None
