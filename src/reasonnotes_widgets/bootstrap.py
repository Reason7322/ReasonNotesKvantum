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
    data_root = candidate_data_directory(environ, home=home).expanduser()
    paths = LaunchPaths(
        data_root=data_root,
        repository=(Path(root).expanduser() if root is not None else data_root / "repository"),
        inbox=(Path(inbox).expanduser() if inbox is not None else data_root / "inbox"),
        received_dir=(
            Path(received_dir).expanduser()
            if received_dir is not None
            else data_root / "received"
        ),
    )
    protected = protected_production_directories(environ, home=home)
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


def create_application(argv: Sequence[str] | None = None) -> QApplication:
    """Create the Widgets process and install the system Kvantum QStyle."""
    QCoreApplication.setOrganizationName("ReasonNotes")
    QCoreApplication.setOrganizationDomain("reasonnotes.local")
    QCoreApplication.setApplicationName("ReasonNotesKvantum")
    application = QApplication.instance()
    if application is None:
        application = QApplication(list(argv or ["reasonnotes-kvantum"]))
    application.setApplicationName("ReasonNotesKvantum")
    application.setDesktopFileName(APP_ID)
    style = QStyleFactory.create("kvantum")
    if style is None:
        available = ", ".join(QStyleFactory.keys())
        raise RuntimeError(
            "The installed Qt 6 Kvantum style is required "
            f"(available styles: {available or 'none'})."
        )
    application.setStyle(style)
    if application.style().objectName().casefold() != "kvantum":
        raise RuntimeError("Qt rejected the installed Kvantum style")
    return application
