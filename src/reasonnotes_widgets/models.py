"""Small event-driven models consumed by native Qt item views."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QAbstractListModel, QByteArray, QModelIndex, QObject, Qt


class MappingListModel(QAbstractListModel):
    """List model whose custom roles map directly to immutable row dictionaries."""

    def __init__(
        self,
        role_names: tuple[str, ...],
        *,
        display_role: str,
        parent: QObject | None = None,
    ):
        super().__init__(parent)
        self._role_names = role_names
        self._display_role = display_role
        self._roles = {
            int(Qt.ItemDataRole.UserRole) + index + 1: QByteArray(name.encode("utf-8"))
            for index, name in enumerate(role_names)
        }
        self._rows: list[dict[str, Any]] = []

    def roleNames(self):
        return self._roles

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._rows)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._rows):
            return None
        row = self._rows[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            return row.get(self._display_role)
        name = self._roles.get(int(role))
        if name is None:
            return None
        return row.get(bytes(name).decode("utf-8"))

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        return (
            Qt.ItemFlag.ItemIsEnabled
            | Qt.ItemFlag.ItemIsSelectable
            | Qt.ItemFlag.ItemNeverHasChildren
        )

    def replace(self, rows) -> bool:
        normalized = [dict(row) for row in rows]
        if normalized == self._rows:
            return False
        self.beginResetModel()
        self._rows = normalized
        self.endResetModel()
        return True

    def row(self, index: int) -> dict[str, Any]:
        if not 0 <= index < len(self._rows):
            return {}
        return dict(self._rows[index])

    def note_id_at(self, index: int) -> str | None:
        value = self.row(index).get("noteId")
        return value if isinstance(value, str) else None


class NoteListModel(MappingListModel):
    def __init__(self, parent: QObject | None = None):
        super().__init__(
            ("noteId", "title", "preview", "conflicted", "modifiedUtc",
             "deliveryStatus", "bulkSelected"),
            display_role="title",
            parent=parent,
        )


class SyncListModel(MappingListModel):
    def __init__(self, parent: QObject | None = None):
        super().__init__(
            ("noteId", "title", "preview", "selected", "deliveryStatus"),
            display_role="title",
            parent=parent,
        )


class ConflictListModel(MappingListModel):
    def __init__(self, parent: QObject | None = None):
        super().__init__(
            ("revisionId", "originDevice", "deleted", "body"),
            display_role="originDevice",
            parent=parent,
        )
