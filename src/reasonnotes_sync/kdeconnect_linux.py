"""Narrow Linux KDE Connect command and receive-signal adapter."""

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote, urlparse


COMMAND_TIMEOUT_SECONDS = 10


@dataclass(frozen=True, slots=True)
class TransferRequest:
    accepted: bool
    completion_observed: bool
    detail: str


def _run(arguments, *, env):
    try:
        return subprocess.run(
            arguments,
            env=env,
            capture_output=True,
            text=True,
            check=False,
            timeout=COMMAND_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(
            arguments,
            124,
            "",
            f"KDE Connect command timed out after {COMMAND_TIMEOUT_SECONDS} seconds",
        )
    except OSError as error:
        return subprocess.CompletedProcess(
            arguments,
            127,
            "",
            f"KDE Connect command failed to start: {error}",
        )


class KdeConnectLinux:
    def __init__(self, device_id: str, command_runner=None):
        if not re.fullmatch(r"[0-9a-f]{32}", device_id):
            raise ValueError("KDE Connect device ID must be 32 lowercase hexadecimal characters")
        self.device_id = device_id
        self.command_runner = _run if command_runner is None else command_runner

    @staticmethod
    def environment() -> dict[str, str]:
        return {
            **os.environ,
            "XDG_RUNTIME_DIR": "/run/user/1000",
            "DBUS_SESSION_BUS_ADDRESS": "unix:path=/run/user/1000/bus",
        }

    def reachable(self) -> bool:
        result = self.command_runner(
            ("kdeconnect-cli", "--list-available", "--id-only"),
            env=self.environment(),
        )
        if result.returncode != 0:
            return False
        return self.device_id in {line.strip() for line in result.stdout.splitlines()}

    def request_transfer(self, path: Path) -> TransferRequest:
        result = self.command_runner(
            (
                "kdeconnect-cli",
                "--device",
                self.device_id,
                "--share",
                str(Path(path)),
            ),
            env=self.environment(),
        )
        if result.returncode == 0:
            return TransferRequest(True, False, "KDE Connect transfer request accepted")
        detail = result.stderr.strip() or result.stdout.strip() or "KDE Connect request failed"
        return TransferRequest(False, False, detail)

    def request_transfers(self, paths: Iterable[Path]) -> TransferRequest:
        values = tuple(Path(path).resolve().as_uri() for path in paths)
        if not values:
            raise ValueError("at least one transfer path is required")
        result = self.command_runner(
            (
                "gdbus",
                "call",
                "--session",
                "--dest",
                "org.kde.kdeconnect",
                "--object-path",
                f"/modules/kdeconnect/devices/{self.device_id}/share",
                "--method",
                "org.kde.kdeconnect.device.share.shareUrls",
                json.dumps(values),
            ),
            env=self.environment(),
        )
        if result.returncode == 0:
            return TransferRequest(
                True,
                False,
                f"KDE Connect batch transfer request accepted ({len(values)} files)",
            )
        detail = (
            result.stderr.strip()
            or result.stdout.strip()
            or "KDE Connect batch request failed"
        )
        return TransferRequest(False, False, detail)

    def received_paths(self, lines: Iterable[str]) -> Iterator[Path]:
        object_path = f"/modules/kdeconnect/devices/{self.device_id}/share:"
        for line in lines:
            if object_path not in line or "shareReceived" not in line:
                continue
            match = re.search(r"['\"](file:[^'\"]+)['\"]", line)
            if match is None:
                continue
            parsed = urlparse(match.group(1))
            if parsed.scheme != "file" or parsed.netloc not in ("", "localhost"):
                continue
            yield Path(unquote(parsed.path))
