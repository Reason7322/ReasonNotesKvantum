#!/usr/bin/env python3
"""Isolated native Qt Widgets candidate entry point."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import subprocess
import sys
from threading import Lock

from PySide6.QtCore import QTimer


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
from reasonnotes_sync.current_store import CurrentNoteStore
from reasonnotes_sync.kdeconnect_linux import KdeConnectLinux
from reasonnotes_sync.sync import (
    return_current_acknowledgments,
    scan_inbox,
    sync_linux_confirmed,
)


DEVICE_ID_PATTERN = re.compile(r"[0-9a-f]{32}")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="reasonnotes-kvantum-candidate")
    result.add_argument("--root", type=Path)
    result.add_argument("--inbox", type=Path)
    result.add_argument(
        "--received-dir",
        type=Path,
        help="KDE Connect received folder (default: ~/Downloads)",
    )
    result.add_argument("--device-id")
    result.add_argument("--target-device", default="android")
    result.add_argument("--no-auto-receive", action="store_true")
    result.add_argument("--check-launch", action="store_true", help=argparse.SUPPRESS)
    result.add_argument("--runtime-probe-ms", type=int, help=argparse.SUPPRESS)
    material = result.add_mutually_exclusive_group()
    material.add_argument(
        "--native-window-material", action="store_true", help=argparse.SUPPRESS
    )
    material.add_argument(
        "--kitty-window-material", action="store_true", help=argparse.SUPPRESS
    )
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


def open_candidate_store(root: Path) -> CurrentNoteStore:
    """Open the isolated simplified store without touching legacy history."""
    return CurrentNoteStore.open(root, "linux")


def run_confirmed_sync(repository, paths, device_id, selection, receive_lock):
    if device_id is None:
        raise RuntimeError(
            "No single reachable KDE Connect device found. Pair the phone "
            "or launch with --device-id."
        )
    with receive_lock:
        paths.inbox.mkdir(parents=True, exist_ok=True)
        return sync_linux_confirmed(
            repository,
            paths.inbox,
            KdeConnectLinux(device_id),
            selected_note_ids=selection,
            received_dir=paths.received_dir,
        )


def main(arguments=None) -> int:
    options = parser().parse_args(arguments)
    paths = resolve_launch_paths(
        root=options.root,
        inbox=options.inbox,
        received_dir=options.received_dir,
    )
    if options.device_id is not None and not DEVICE_ID_PATTERN.fullmatch(options.device_id):
        raise SystemExit("--device-id must contain 32 lowercase hexadecimal characters")
    if options.runtime_probe_ms is not None and options.runtime_probe_ms < 1:
        raise SystemExit("--runtime-probe-ms must be positive")
    device_id = options.device_id or discover_device_id()
    application = create_application([sys.argv[0]])
    repository = open_candidate_store(paths.repository)
    paths.inbox.mkdir(parents=True, exist_ok=True)
    receive_lock = Lock()

    def scan_received():
        with receive_lock:
            paths.inbox.mkdir(parents=True, exist_ok=True)
            report = scan_inbox(
                repository, paths.inbox, "linux", received_dir=paths.received_dir
            )
            _requested, acknowledgment_errors = return_current_acknowledgments(
                repository, KdeConnectLinux(device_id)
            )
            if acknowledgment_errors:
                report = type(report)(
                    report.imported,
                    report.duplicates,
                    report.confirmed,
                    report.duplicate_receipts,
                    report.receipts_queued,
                    report.quarantined,
                    report.conflicts,
                    tuple((*report.errors, *acknowledgment_errors)),
                )
            return report

    def run_sync(selection):
        return run_confirmed_sync(
            repository,
            paths,
            device_id,
            selection,
            receive_lock,
        )

    controller = WidgetsController(
        NotePresenter(NoteService(repository, origin_device="linux"), run_sync)
    )
    controller.configure_incoming_scan(scan_received)
    probe_mode = options.runtime_probe_ms is not None
    window = ReasonNotesMainWindow(
        controller,
        deletion_pairing=None,
        native_window_material=options.native_window_material,
        kitty_window_material=options.kitty_window_material,
    )
    prepare_translucent_surface(window, platform_name=application.platformName())
    blur = QWidgetBlurController()
    runtime = ApplicationRuntime(
        repository,
        controller,
        relay=None,
        incoming_paths=(paths.inbox, paths.received_dir),
    )
    application.aboutToQuit.connect(runtime.stop)
    application.aboutToQuit.connect(blur.close)
    if options.check_launch:
        blur.close()
        window.close()
        return 0
    window.show()
    blur.attach(window)
    runtime.start(auto_receive=not options.no_auto_receive)
    if probe_mode:
        print(f"RUNTIME_STYLE={application.style().objectName().casefold()}")
        print(f"RUNTIME_PLATFORM={application.platformName().casefold()}")
        print(f"RUNTIME_BLUR_ACTIVE={int(blur.active)}")
        print(f"RUNTIME_BLUR_ERROR={blur.last_error}")
        print(f"RUNTIME_DATA_ROOT={paths.data_root}")
        print(f"RUNTIME_WINDOW_MATERIAL={window.window_material_mode}")
        print("RUNTIME_PURGE_RELAY=disabled-for-probe")
        sys.stdout.flush()
        QTimer.singleShot(options.runtime_probe_ms, application.quit)
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
