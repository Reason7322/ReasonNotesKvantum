"""Foreground-only application lifecycle services."""

from __future__ import annotations

from uuid import UUID

from PySide6.QtCore import QObject, QTimer


class ApplicationRuntime(QObject):
    def __init__(self, repository, controller, *, relay=None, parent=None):
        super().__init__(parent)
        self.repository = repository
        self.controller = controller
        self.relay = relay
        self._changes_seen = relay.changes if relay is not None else 0
        self._stopped = False
        self.relay_error = ""
        self.purge_timer = QTimer(self)
        self.purge_timer.setInterval(600)
        self.purge_timer.timeout.connect(self.poll_purge)

    def start(self, *, auto_receive: bool) -> None:
        if self.relay is not None:
            try:
                self.relay.start()
            except OSError as error:
                self.relay_error = str(error)
            else:
                self.purge_timer.start()
        if auto_receive:
            QTimer.singleShot(
                0,
                lambda: self.controller.start_incoming_scan(
                    self.controller._incoming_scanner
                )
                if self.controller._incoming_scanner is not None
                else None,
            )

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
        self.purge_timer.stop()
        if self.relay is not None:
            self.relay.stop()
