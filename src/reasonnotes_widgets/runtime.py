"""Foreground-only application lifecycle services."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from uuid import UUID

from PySide6.QtCore import QFileSystemWatcher, QObject, QTimer


class ApplicationRuntime(QObject):
    def __init__(
        self,
        repository,
        controller,
        *,
        relay=None,
        incoming_paths: Iterable[Path] = (),
        parent=None,
    ):
        super().__init__(parent)
        self.repository = repository
        self.controller = controller
        self.relay = relay
        self.incoming_paths = tuple(
            dict.fromkeys(str(Path(path).resolve()) for path in incoming_paths)
        )
        self._changes_seen = relay.changes if relay is not None else 0
        self._stopped = False
        self._auto_receive = False
        self.relay_error = ""
        self.purge_timer = QTimer(self)
        self.purge_timer.setInterval(600)
        self.purge_timer.timeout.connect(self.poll_purge)
        self.receive_watcher = QFileSystemWatcher(self)
        self.receive_watcher.directoryChanged.connect(self.schedule_incoming_scan)
        self.receive_debounce = QTimer(self)
        self.receive_debounce.setSingleShot(True)
        self.receive_debounce.setInterval(400)
        self.receive_debounce.timeout.connect(self.poll_incoming)

    def start(self, *, auto_receive: bool) -> None:
        self._auto_receive = auto_receive
        if self.relay is not None:
            try:
                self.relay.start()
            except OSError as error:
                self.relay_error = str(error)
            else:
                self.purge_timer.start()
        if auto_receive:
            existing = [path for path in self.incoming_paths if Path(path).is_dir()]
            if existing:
                self.receive_watcher.addPaths(existing)
            QTimer.singleShot(0, self.poll_incoming)

    def schedule_incoming_scan(self, _path: str = "") -> None:
        if self._auto_receive and not self._stopped:
            self.receive_debounce.start()

    def poll_incoming(self) -> None:
        if not self._auto_receive or self._stopped:
            return
        scanner = self.controller._incoming_scanner
        if scanner is None:
            return
        if not self.controller.start_incoming_scan(scanner):
            self.receive_debounce.start()

    def poll_purge(self) -> None:
        if self.relay is None or self.relay.changes == self._changes_seen:
            return
        self._changes_seen = self.relay.changes
        active = self.controller.presenter.active_note_id
        if active is not None and self.repository.is_purged(UUID(active)):
            presenter = self.controller.presenter
            presenter.active_note_id = None
            presenter._active_head_ids = ()
            presenter.draft = ""
            presenter.dirty = False
            presenter.conflict_view = None
        self.controller.presenter.refresh()
        self.controller.refresh_models()
        self.controller._notify(draft=True, conflict=True, refresh_models=False)

    def stop(self) -> None:
        if self._stopped:
            return
        self._stopped = True
        self._auto_receive = False
        self.purge_timer.stop()
        self.receive_debounce.stop()
        watched = self.receive_watcher.directories()
        if watched:
            self.receive_watcher.removePaths(watched)
        if self.relay is not None:
            self.relay.stop()
