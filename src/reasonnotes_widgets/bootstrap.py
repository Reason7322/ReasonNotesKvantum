"""Candidate-safe process bootstrap and system Kvantum activation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import os
from pathlib import Path

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication, QStyleFactory


APP_ID = "org.reasonnotes.ReasonNotesKvantum"
CANDIDATE_NAME = "ReasonNotesKvantum-candidate"
PRODUCTION_NAME = "ReasonNotes"


class UnsafeProductionPath(ValueError):
    """Raised when a candidate launch points at protected production data."""


@dataclass(frozen=True, slots=True)
class LaunchPaths:
    data_root: Path
    repository: Path
    inbox: Path
    received_dir: Path


def _data_home(
    environ: Mapping[str, str] | None = None, *, home: Path | None = None
) -> Path:
    values = os.environ if environ is None else environ
    user_home = Path(values.get("HOME", str(Path.home()))) if home is None else Path(home)
    configured = values.get("XDG_DATA_HOME", "")
    if configured and Path(configured).expanduser().is_absolute():
        return Path(configured).expanduser()
    return user_home.expanduser() / ".local/share"


def candidate_data_directory(
    environ: Mapping[str, str] | None = None, *, home: Path | None = None
) -> Path:
    return _data_home(environ, home=home) / CANDIDATE_NAME


def production_data_directory(
    environ: Mapping[str, str] | None = None, *, home: Path | None = None
) -> Path:
    return _data_home(environ, home=home) / PRODUCTION_NAME


def protected_production_directories(
    environ: Mapping[str, str] | None = None, *, home: Path | None = None
) -> tuple[Path, ...]:
    values = os.environ if environ is None else environ
    user_home = (
        Path(values.get("HOME", str(Path.home())))
        if home is None
        else Path(home)
    )
    roots = {
        user_home.expanduser() / ".local/share" / PRODUCTION_NAME,
        production_data_directory(values, home=user_home),
    }
    return tuple(sorted(roots, key=str))


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(parent.resolve(strict=False))
    except ValueError:
        return False
    return True


def resolve_launch_paths(
    *,
    root: Path | None = None,
    inbox: Path | None = None,
    received_dir: Path | None = None,
    environ: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> LaunchPaths:
    """Resolve candidate paths and fail closed on the live production tree."""
    values = os.environ if environ is None else environ
    user_home = (
        Path(values.get("HOME", str(Path.home())))
        if home is None
        else Path(home)
    ).expanduser()
    data_root = candidate_data_directory(values, home=user_home).expanduser()
    paths = LaunchPaths(
        data_root=data_root,
        repository=(Path(root).expanduser() if root is not None else data_root / "repository"),
        inbox=(Path(inbox).expanduser() if inbox is not None else data_root / "inbox"),
        received_dir=(
            Path(received_dir).expanduser()
            if received_dir is not None
            else user_home / "Downloads"
        ),
    )
    protected = protected_production_directories(values, home=user_home)
    for label, path in (
        ("repository", paths.repository),
        ("inbox", paths.inbox),
        ("received directory", paths.received_dir),
    ):
        if any(_is_within(path, root) for root in protected):
            raise UnsafeProductionPath(
                f"Candidate {label} may not use protected production data: {path}"
            )
    return paths


def style_chain_names(style) -> tuple[str, ...]:
    """Return the active style wrapper chain, including its leaf style."""
    names: list[str] = []
    seen: set[int] = set()
    current = style
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        names.append(current.objectName().casefold())
        base_style = getattr(current, "baseStyle", None)
        current = base_style() if callable(base_style) else None
    return tuple(names)


def ensure_kvantum_style(application) -> None:
    """Preserve a qt6ct wrapper over Kvantum, or install Kvantum explicitly."""
    if "kvantum" in style_chain_names(application.style()):
        return
    kvantum = QStyleFactory.create("kvantum")
    if kvantum is None:
        available = ", ".join(QStyleFactory.keys())
        raise RuntimeError(
            "The installed Qt 6 Kvantum style is required "
            f"(available styles: {available or 'none'})."
        )
    application.setStyle(kvantum)
    if "kvantum" not in style_chain_names(application.style()):
        raise RuntimeError("Qt rejected the installed Kvantum style")


def create_application(argv: Sequence[str] | None = None) -> QApplication:
    """Create the Widgets process and retain the system Kvantum style chain."""
    QCoreApplication.setOrganizationName("ReasonNotes")
    QCoreApplication.setOrganizationDomain("reasonnotes.local")
    QCoreApplication.setApplicationName("ReasonNotesKvantum")
    application = QApplication.instance()
    if application is None:
        application = QApplication(list(argv or ["reasonnotes-kvantum"]))
    application.setApplicationName("ReasonNotesKvantum")
    application.setDesktopFileName(APP_ID)
    # Dolphin receives qt6ct-style from the platform theme, with Kvantum as
    # its base style. Preserve that chain so the system font, icon theme and
    # palette remain authoritative. Environments without qt6ct retain the
    # original strict Kvantum fallback.
    ensure_kvantum_style(application)
    return application
