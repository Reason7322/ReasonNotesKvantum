#!/usr/bin/env python3
"""Isolated native Qt Widgets candidate entry point."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import subprocess
import sys
from threading import Lock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "src"
if str(SOURCE_ROOT) in sys.path:
    sys.path.remove(str(SOURCE_ROOT))
sys.path.insert(0, str(SOURCE_ROOT))

from reasonnotes_widgets.bootstrap import create_application, resolve_launch_paths
from reasonnotes_widgets.controller import WidgetsController
from reasonnotes_widgets.main_window import ReasonNotesMainWindow
from reasonnotes_widgets.runtime import ApplicationRuntime
from reasonnotes_widgets.wayland_blur import (
    QWidgetBlurController,
    prepare_translucent_surface,
)
from reasonnotes_app.presenter import NotePresenter
from reasonnotes_app.service import NoteService
from reasonnotes_sync.repository import Repository
from reasonnotes_sync.foreground_purge import PurgeRelay, shared_key
from reasonnotes_sync.kdeconnect_linux import KdeConnectLinux
from reasonnotes_sync.receipt_return import return_pending_receipts
from reasonnotes_sync.sync import scan_inbox, sync_linux


DEVICE_ID_PATTERN = re.compile(r"[0-9a-f]{32}")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="reasonnotes-kvantum-candidate")
    result.add_argument("--root", type=Path)
    result.add_argument("--inbox", type=Path)
    result.add_argument("--received-dir", type=Path)
    result.add_argument("--device-id")
    result.add_argument("--target-device", default="android")
    result.add_argument("--no-auto-receive", action="store_true")
    result.add_argument("--check-launch", action="store_true", help=argparse.SUPPRESS)
    return result


def discover_device_id(command_runner=subprocess.run) -> str | None:
    try:
        result = command_runner(
            ["kdeconnect-cli", "--list-available", "--id-only"],
            env=KdeConnectLinux.environment(), capture_output=True, text=True,
            timeout=3, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode:
        return None
    available = {
        line.strip() for line in result.stdout.splitlines()
        if DEVICE_ID_PATTERN.fullmatch(line.strip())
    }
    return next(iter(available)) if len(available) == 1 else None


def main(arguments=None) -> int:
    options = parser().parse_args(arguments)
    paths = resolve_launch_paths(
        root=options.root,
        inbox=options.inbox,
        received_dir=options.received_dir,
    )
    if options.device_id is not None and not DEVICE_ID_PATTERN.fullmatch(options.device_id):
        raise SystemExit("--device-id must contain 32 lowercase hexadecimal characters")
    device_id = options.device_id or discover_device_id()
    application = create_application([sys.argv[0]])
    repository = Repository.open(
        paths.repository, local_device="linux", target_device=options.target_device
    )
    receive_lock = Lock()

    def scan_received():
        with receive_lock:
            paths.inbox.mkdir(parents=True, exist_ok=True)
            report = scan_inbox(
                repository, paths.inbox, "linux", received_dir=paths.received_dir
            )
            if not options.check_launch and device_id is not None:
                return_pending_receipts(repository, KdeConnectLinux(device_id))
            return report

    def run_sync(selection):
        if device_id is None:
            raise RuntimeError(
                "No single reachable KDE Connect device found. Pair the phone "
                "or launch with --device-id."
            )
        with receive_lock:
            paths.inbox.mkdir(parents=True, exist_ok=True)
            return sync_linux(
                repository, paths.inbox, KdeConnectLinux(device_id),
                selected_note_ids=selection, received_dir=paths.received_dir,
            )

    controller = WidgetsController(
        NotePresenter(NoteService(repository, origin_device="linux"), run_sync)
    )
    controller.configure_incoming_scan(scan_received)
    window = ReasonNotesMainWindow(controller)
    prepare_translucent_surface(window, platform_name=application.platformName())
    blur = QWidgetBlurController()
    relay = None if options.check_launch else PurgeRelay(
        repository, shared_key(paths.data_root / "delete-sync-key")
    )
    runtime = ApplicationRuntime(repository, controller, relay=relay)
    application.aboutToQuit.connect(runtime.stop)
    application.aboutToQuit.connect(blur.close)
    if options.check_launch:
        blur.close()
        window.close()
        return 0
    window.show()
    blur.attach(window)
    runtime.start(auto_receive=not options.no_auto_receive)
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
