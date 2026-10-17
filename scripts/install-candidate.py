#!/usr/bin/env python3
"""Install an isolated, versioned ReasonNotesKvantum candidate.

This installer owns only candidate-named paths.  It never migrates notes,
changes the production launcher, or switches the production desktop entry.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys


APP_ID = "org.reasonnotes.ReasonNotesKvantum"
VERSION_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")


class UnsafeInstallTarget(ValueError):
    """Raised when an install target overlaps a protected production path."""


@dataclass(frozen=True, slots=True)
class InstallResult:
    release: Path
    current: Path
    launcher: Path
    desktop: Path


def _within(path: Path, parent: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(parent.resolve(strict=False))
    except ValueError:
        return False
    return True


def _validate_targets(
    install_root: Path,
    launcher_path: Path,
    desktop_path: Path,
    *,
    home: Path,
) -> None:
    protected = (
        home / ".local/opt/reasonnotes",
        home / ".local/bin/reasonnotes",
        home / ".local/share/ReasonNotes",
        home / ".local/share/applications/org.reasonnotes.ReasonNotes.desktop",
    )
    for candidate in (install_root, launcher_path, desktop_path):
        if any(
            _within(candidate, path) or _within(path, candidate)
            for path in protected
        ):
            raise UnsafeInstallTarget(
                f"Candidate install target overlaps protected production path: {candidate}"
            )


def _copy_release(source_root: Path, staging: Path) -> None:
    ignored = shutil.ignore_patterns(
        "__pycache__", "*.pyc", "*.pyo", "libreasonnotes_wayland_blur.so"
    )
    for directory in ("src", "linux-app", "docs", "packaging"):
        shutil.copytree(source_root / directory, staging / directory, ignore=ignored)
    (staging / "scripts").mkdir()
    for script in ("build-wayland-blur.py", "install-candidate.py"):
        shutil.copy2(source_root / "scripts" / script, staging / "scripts" / script)
    for filename in ("README.md", "pyproject.toml"):
        shutil.copy2(source_root / filename, staging / filename)


def _replace_symlink(link: Path, target: Path) -> None:
    temporary = link.with_name(f".{link.name}.tmp-{os.getpid()}")
    temporary.unlink(missing_ok=True)
    temporary.symlink_to(target)
    os.replace(temporary, link)


def _replace_text(path: Path, contents: str, *, executable: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_text(contents)
    if executable:
        temporary.chmod(0o755)
    os.replace(temporary, path)


def activate_release(install_root: Path, version: str) -> Path:
    """Point the candidate-only ``current`` link at an existing release."""

    if not VERSION_PATTERN.fullmatch(version):
        raise ValueError(f"Unsafe release version: {version!r}")
    install_root = Path(install_root).expanduser()
    release = install_root / "releases" / version
    if not release.is_dir():
        raise FileNotFoundError(f"Candidate release is not installed: {release}")
    install_root.mkdir(parents=True, exist_ok=True)
    _replace_symlink(install_root / "current", Path("releases") / version)
    return release


def install_candidate(
    *,
    source_root: Path,
    install_root: Path,
    launcher_path: Path,
    desktop_path: Path,
    version: str,
    build_native: bool = True,
    home: Path | None = None,
) -> InstallResult:
    """Create and activate one immutable candidate release."""

    source_root = Path(source_root).resolve()
    install_root = Path(install_root).expanduser()
    launcher_path = Path(launcher_path).expanduser()
    desktop_path = Path(desktop_path).expanduser()
    user_home = Path.home() if home is None else Path(home)
    _validate_targets(
        install_root, launcher_path, desktop_path, home=user_home.expanduser()
    )
    if not VERSION_PATTERN.fullmatch(version):
        raise ValueError(f"Unsafe release version: {version!r}")
    if not (source_root / "linux-app/reasonnotes_widgets.py").is_file():
        raise FileNotFoundError(f"Candidate source tree is incomplete: {source_root}")

    releases = install_root / "releases"
    release = releases / version
    if release.exists() or release.is_symlink():
        raise FileExistsError(f"Candidate release already exists: {release}")
    releases.mkdir(parents=True, exist_ok=True)
    staging = releases / f".{version}.staging-{os.getpid()}"
    if staging.exists():
        raise FileExistsError(f"Candidate staging path already exists: {staging}")
    try:
        staging.mkdir()
        _copy_release(source_root, staging)
        if build_native:
            subprocess.run(
                [
                    sys.executable,
                    str(staging / "scripts/build-wayland-blur.py"),
                    "--target",
                    str(staging / "linux-app/native"),
                ],
                check=True,
            )
        os.replace(staging, release)
    except BaseException:
        if staging.exists():
            shutil.rmtree(staging)
        raise

    activate_release(install_root, version)
    current = install_root / "current"
    entrypoint = current / "linux-app/reasonnotes_widgets.py"
    launcher = (
        "#!/bin/sh\n"
        "set -eu\n"
        f"exec /usr/bin/python3 {shlex.quote(str(entrypoint))} \"$@\"\n"
    )
    _replace_text(launcher_path, launcher, executable=True)

    template = (
        source_root / "packaging/org.reasonnotes.ReasonNotesKvantum.desktop"
    ).read_text()
    desktop = template.replace("@CANDIDATE_LAUNCHER@", str(launcher_path)).replace(
        "@CANDIDATE_ICON@", str(current / "linux-app/icons/reasonnotes-yamis.svg")
    )
    _replace_text(desktop_path, desktop)
    return InstallResult(release, current, launcher_path, desktop_path)


def _default_version(source_root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=source_root,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def main(arguments=None) -> int:
    source_root = Path(__file__).resolve().parents[1]
    home = Path.home()
    parser = argparse.ArgumentParser(prog="install-reasonnotes-kvantum-candidate")
    parser.add_argument("--source-root", type=Path, default=source_root)
    parser.add_argument(
        "--install-root",
        type=Path,
        default=home / ".local/opt/reasonnotes-kvantum-candidate",
    )
    parser.add_argument(
        "--launcher",
        type=Path,
        default=home / ".local/bin/reasonnotes-kvantum-candidate",
    )
    parser.add_argument(
        "--desktop",
        type=Path,
        default=(
            home
            / ".local/share/applications/org.reasonnotes.ReasonNotesKvantum.desktop"
        ),
    )
    parser.add_argument("--version")
    parser.add_argument("--activate", metavar="VERSION")
    options = parser.parse_args(arguments)
    if options.activate:
        release = activate_release(options.install_root, options.activate)
        print(f"ACTIVATED_CANDIDATE={release}")
        return 0
    version = options.version or _default_version(options.source_root)
    result = install_candidate(
        source_root=options.source_root,
        install_root=options.install_root,
        launcher_path=options.launcher,
        desktop_path=options.desktop,
        version=version,
        home=home,
    )
    print(f"INSTALLED_CANDIDATE={result.release}")
    print(f"CANDIDATE_LAUNCHER={result.launcher}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
