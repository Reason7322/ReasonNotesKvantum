#!/usr/bin/env python3
"""Fail-closed preflight for an isolated ReasonNotes candidate launch."""

from __future__ import annotations

import argparse
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
import os
from pathlib import Path


ENVIRONMENT_ROOTS = (
    "HOME",
    "XDG_CONFIG_HOME",
    "XDG_DATA_HOME",
    "XDG_CACHE_HOME",
    "XDG_STATE_HOME",
)


class IsolationError(RuntimeError):
    """Raised when launch paths or processes can reach protected data."""


@dataclass(frozen=True, slots=True)
class IsolationReport:
    repository: Path
    inbox: Path
    received_dir: Path
    environment: dict[str, Path]
    conflicting_processes: tuple[tuple[int, tuple[str, ...]], ...]


def _resolved(path: Path | str) -> Path:
    return Path(path).expanduser().resolve(strict=False)


def _overlaps(first: Path, second: Path) -> bool:
    try:
        first.relative_to(second)
        return True
    except ValueError:
        try:
            second.relative_to(first)
            return True
        except ValueError:
            return False


def _effective_environment(environ: Mapping[str, str]) -> dict[str, Path]:
    if not environ.get("HOME"):
        raise IsolationError("HOME must be explicitly isolated")
    home = _resolved(environ["HOME"])
    defaults = {
        "HOME": home,
        "XDG_CONFIG_HOME": home / ".config",
        "XDG_DATA_HOME": home / ".local/share",
        "XDG_CACHE_HOME": home / ".cache",
        "XDG_STATE_HOME": home / ".local/state",
    }
    return {
        name: _resolved(environ.get(name, str(defaults[name])))
        for name in ENVIRONMENT_ROOTS
    }


def process_command_lines() -> tuple[tuple[int, tuple[str, ...]], ...]:
    """Read process command lines without changing process state."""
    rows: list[tuple[int, tuple[str, ...]]] = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            raw = (entry / "cmdline").read_bytes()
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
        arguments = tuple(
            part.decode(errors="replace") for part in raw.split(b"\0") if part
        )
        if arguments:
            rows.append((int(entry.name), arguments))
    return tuple(rows)


def _process_conflicts(
    command_lines: Iterable[tuple[int, Sequence[str]]],
    protected_roots: tuple[Path, ...],
    protected_executables: tuple[Path, ...],
) -> tuple[tuple[int, tuple[str, ...]], ...]:
    conflicts = []
    executable_names = {"reasonnotes", "reasonnotes-kvantum-candidate"}
    for pid, command in command_lines:
        arguments = tuple(command)
        if not arguments:
            continue
        matched = Path(arguments[0]).name in executable_names
        for token in arguments:
            token_path = _resolved(token)
            if token_path in protected_executables:
                matched = True
            if (
                token_path.name == "reasonnotes_widgets.py"
                and any(_overlaps(token_path, root) for root in protected_roots)
            ):
                matched = True
        if matched:
            conflicts.append((pid, arguments))
    return tuple(conflicts)


def verify_candidate_isolation(
    *,
    repository: Path,
    inbox: Path,
    received_dir: Path,
    environ: Mapping[str, str] | None = None,
    protected_roots: Sequence[Path] = (),
    protected_executables: Sequence[Path] = (),
    process_command_lines: Iterable[tuple[int, Sequence[str]]] | None = None,
) -> IsolationReport:
    values = dict(os.environ if environ is None else environ)
    environment = _effective_environment(values)
    requested = {
        "repository": Path(repository).expanduser(),
        "inbox": Path(inbox).expanduser(),
        "received directory": Path(received_dir).expanduser(),
    }
    resolved = {name: _resolved(path) for name, path in requested.items()}
    protected = tuple(_resolved(path) for path in protected_roots)
    executables = tuple(_resolved(path) for path in protected_executables)

    for label, path in (*resolved.items(), *environment.items()):
        for protected_path in protected:
            if _overlaps(path, protected_path):
                raise IsolationError(
                    f"{label} overlaps protected path: {path} <-> {protected_path}"
                )

    commands = (
        globals()["process_command_lines"]()
        if process_command_lines is None
        else tuple(process_command_lines)
    )
    conflicts = _process_conflicts(commands, protected, executables)
    if conflicts:
        pids = ", ".join(str(pid) for pid, _command in conflicts)
        raise IsolationError(f"Conflicting ReasonNotes process IDs: {pids}")

    return IsolationReport(
        repository=resolved["repository"],
        inbox=resolved["inbox"],
        received_dir=resolved["received directory"],
        environment=environment,
        conflicting_processes=conflicts,
    )


def _defaults(home: Path) -> tuple[tuple[Path, ...], tuple[Path, ...]]:
    roots = (
        home / ".local/share/ReasonNotes",
        home / ".local/share/ReasonNotesKvantum-candidate",
        home / ".local/opt/reasonnotes",
        home / ".local/opt/reasonnotes-kvantum-candidate",
    )
    executables = (
        home / ".local/bin/reasonnotes",
        home / ".local/bin/reasonnotes-kvantum-candidate",
    )
    return roots, executables


def main(arguments: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--inbox", type=Path, required=True)
    parser.add_argument("--received-dir", type=Path, required=True)
    options = parser.parse_args(arguments)
    real_home = Path.home()
    roots, executables = _defaults(real_home)
    report = verify_candidate_isolation(
        repository=options.repository,
        inbox=options.inbox,
        received_dir=options.received_dir,
        protected_roots=roots,
        protected_executables=executables,
    )
    print(f"REQUESTED_REPOSITORY={options.repository}")
    print(f"RESOLVED_REPOSITORY={report.repository}")
    print(f"REQUESTED_INBOX={options.inbox}")
    print(f"RESOLVED_INBOX={report.inbox}")
    print(f"REQUESTED_RECEIVED_DIR={options.received_dir}")
    print(f"RESOLVED_RECEIVED_DIR={report.received_dir}")
    for name in ENVIRONMENT_ROOTS:
        print(f"RESOLVED_{name}={report.environment[name]}")
    print("CONFLICTING_REASONNOTES_PROCESSES=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
