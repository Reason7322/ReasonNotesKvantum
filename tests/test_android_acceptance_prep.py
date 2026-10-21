from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from uuid import UUID

from reasonnotes_app.service import NoteService
from reasonnotes_sync.delivery import DeliveryLedger, DeliveryState
from reasonnotes_sync.repository import Repository
from reasonnotes_widgets.bootstrap import UnsafeProductionPath


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = PROJECT_ROOT / "scripts/prepare-android-acceptance.py"


def _load_script():
    spec = spec_from_file_location("reasonnotes_android_acceptance_prep", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {SCRIPT}")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AndroidAcceptancePreparationTests(unittest.TestCase):
    def test_production_target_is_rejected_before_it_is_created(self):
        module = _load_script()
        with TemporaryDirectory() as folder:
            home = Path(folder) / "home"
            production = home / ".local/share/ReasonNotes"

            with self.assertRaises(UnsafeProductionPath):
                module.prepare_fixture(production, home=home)

            self.assertFalse(production.exists())

    def test_nonempty_workspace_is_refused_without_altering_it(self):
        module = _load_script()
        with TemporaryDirectory() as folder:
            workspace = Path(folder) / "fixture"
            workspace.mkdir()
            marker = workspace / "keep.txt"
            marker.write_text("preserve me\n", encoding="utf-8")

            with self.assertRaises(FileExistsError):
                module.prepare_fixture(workspace, home=Path(folder) / "home")

            self.assertEqual(marker.read_text(encoding="utf-8"), "preserve me\n")
            self.assertEqual(tuple(workspace.iterdir()), (marker,))

    def test_manifest_and_seeded_history_are_reproducible_and_offline(self):
        module = _load_script()
        with TemporaryDirectory() as folder:
            workspace = Path(folder) / "fixture"
            manifest = module.prepare_fixture(workspace, home=Path(folder) / "home")

            persisted = json.loads(
                (workspace / "android-acceptance-manifest.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(persisted, manifest)
            self.assertEqual(manifest["format"], 1)
            self.assertEqual(manifest["workspace"], str(workspace.resolve()))
            self.assertEqual(
                [note["role"] for note in manifest["notes"]],
                ["unicode-round-trip", "conflict", "deletion"],
            )
            self.assertEqual(
                sorted(manifest["paths"]),
                ["inbox", "received", "repository"],
            )

            repository = Repository.open(
                Path(manifest["paths"]["repository"]),
                local_device="linux",
                target_device="android",
            )
            service = NoteService(repository, origin_device="linux")
            bodies = {
                note["role"]: service.open_note(UUID(note["note_id"]))
                for note in manifest["notes"]
            }
            self.assertIn("Zażółć gęślą jaźń", bodies["unicode-round-trip"])
            self.assertIn("independently", bodies["conflict"])
            self.assertIn("Delete", bodies["deletion"])
            self.assertEqual(len(repository.revisions()), 3)
            for note in manifest["notes"]:
                status = repository.graph().status(UUID(note["note_id"]))
                self.assertEqual(len(status.head_ids), 1)
                self.assertFalse(status.conflicted)

            self.assertEqual(tuple(Path(manifest["paths"]["inbox"]).iterdir()), ())
            self.assertEqual(tuple(Path(manifest["paths"]["received"]).iterdir()), ())
            ledger = DeliveryLedger(Path(manifest["paths"]["repository"]))
            entries = ledger.entries("android")
            self.assertEqual(len(entries), 3)
            self.assertTrue(
                all(
                    entry.state == DeliveryState.PENDING
                    and entry.attempts == 0
                    and entry.last_requested_utc is None
                    for entry in entries
                )
            )


if __name__ == "__main__":
    unittest.main()
