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
from reasonnotes_widgets.controller import WidgetsController
from reasonnotes_widgets.main_window import ReasonNotesMainWindow
from reasonnotes_app.presenter import NotePresenter
from reasonnotes_app.service import NoteService
from reasonnotes_sync.repository import Repository


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="reasonnotes-kvantum-candidate")
    result.add_argument("--root", type=Path)
    result.add_argument("--inbox", type=Path)
    result.add_argument("--received-dir", type=Path)
    result.add_argument("--check-launch", action="store_true", help=argparse.SUPPRESS)
    return result


def main(arguments=None) -> int:
    options = parser().parse_args(arguments)
    paths = resolve_launch_paths(
        root=options.root,
        inbox=options.inbox,
        received_dir=options.received_dir,
    )
    application = create_application([sys.argv[0]])
    repository = Repository.open(
        paths.repository, local_device="linux", target_device="android"
    )
    controller = WidgetsController(
        NotePresenter(NoteService(repository, origin_device="linux"))
    )
    window = ReasonNotesMainWindow(controller)
    if options.check_launch:
        window.close()
        return 0
    window.show()
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
