#!/usr/bin/env python3
"""Create a deterministic, offline fixture for physical Android acceptance.

This utility deliberately prepares only local immutable note history.  It does
not discover peers, invoke KDE Connect, send files, or import incoming data.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from uuid import UUID


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from reasonnotes_app.service import NoteService  # noqa: E402
from reasonnotes_sync.repository import Repository  # noqa: E402
from reasonnotes_widgets.bootstrap import resolve_launch_paths  # noqa: E402


MANIFEST_NAME = "android-acceptance-manifest.json"
FIXTURE_TIME = datetime(2026, 10, 21, 12, 0, tzinfo=timezone.utc)
SEEDS = (
    (
        "unicode-round-trip",
        UUID("f40dd429-390c-54a1-a62e-9adca52f3290"),
        "# Zażółć gęślą jaźń\n\nŁódź — Android round trip ✓\n",
    ),
    (
        "conflict",
        UUID("7e41799f-59af-5a3f-ab00-0602746ae9bf"),
        "# Conflict seed\n\nEdit this note independently on both devices while offline.\n",
    ),
    (
        "deletion",
        UUID("15e5645b-c94c-54e0-b466-4cb49d431c90"),
        "# Delete after round trip\n\nDelete this note from Linux after Android confirms receipt.\n",
    ),
)


def prepare_fixture(workspace: Path, *, home: Path | None = None) -> dict:
    """Create a new isolated fixture and return its persisted manifest.

    The production-path check happens before any directory is created.  An
    existing non-empty workspace is also rejected so prior acceptance evidence
    can never be silently overwritten.
    """
    workspace = Path(workspace).expanduser().resolve(strict=False)
    paths = resolve_launch_paths(
        root=workspace / "repository",
        inbox=workspace / "inbox",
        received_dir=workspace / "received",
        home=home,
    )

    if workspace.exists() and any(workspace.iterdir()):
        raise FileExistsError(f"acceptance workspace is not empty: {workspace}")

    workspace.mkdir(parents=True, exist_ok=True)
    paths.inbox.mkdir()
    paths.received_dir.mkdir()

    identifiers = iter(seed[1] for seed in SEEDS)
    repository = Repository.open(
        paths.repository,
        local_device="linux",
        target_device="android",
    )
    service = NoteService(
        repository,
        origin_device="linux",
        clock=lambda: FIXTURE_TIME,
        note_id_factory=lambda: next(identifiers),
    )

    notes = []
    for role, expected_id, body in SEEDS:
        note_id = service.create_note(body)
        if note_id != expected_id:
            raise RuntimeError("fixture note identity changed unexpectedly")
        notes.append(
            {
                "body_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
                "note_id": str(note_id),
                "role": role,
            }
        )

    manifest = {
        "format": 1,
        "notes": notes,
        "paths": {
            "inbox": str(paths.inbox.resolve()),
            "received": str(paths.received_dir.resolve()),
            "repository": str(paths.repository.resolve()),
        },
        "transport_activity": False,
        "workspace": str(workspace),
    }
    manifest_path = workspace / MANIFEST_NAME
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Prepare an isolated ReasonNotes Android acceptance fixture."
    )
    parser.add_argument(
        "workspace",
        type=Path,
        help="new or empty directory; production ReasonNotes paths are refused",
    )
    arguments = parser.parse_args(argv)
    manifest = prepare_fixture(arguments.workspace)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
