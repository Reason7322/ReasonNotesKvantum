#!/usr/bin/env python3
"""Isolated native Qt Widgets candidate entry point."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "src"
if str(SOURCE_ROOT) in sys.path:
    sys.path.remove(str(SOURCE_ROOT))
sys.path.insert(0, str(SOURCE_ROOT))

from reasonnotes_widgets.bootstrap import create_application, resolve_launch_paths


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="reasonnotes-kvantum-candidate")
    result.add_argument("--root", type=Path)
    result.add_argument("--inbox", type=Path)
    result.add_argument("--received-dir", type=Path)
    result.add_argument("--check-launch", action="store_true", help=argparse.SUPPRESS)
    return result


def main(arguments=None) -> int:
    options = parser().parse_args(arguments)
    resolve_launch_paths(
        root=options.root,
        inbox=options.inbox,
        received_dir=options.received_dir,
    )
    create_application([sys.argv[0]])
    if options.check_launch:
        return 0
    raise RuntimeError("The Widgets main window is not constructed yet")


if __name__ == "__main__":
    raise SystemExit(main())
