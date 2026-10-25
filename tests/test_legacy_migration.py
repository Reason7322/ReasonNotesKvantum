from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from uuid import UUID

from reasonnotes_sync.current_store import CurrentNoteStore
from reasonnotes_sync.envelope import Revision
from reasonnotes_sync.legacy_migration import migrate_legacy_repository
from reasonnotes_sync.repository import Repository
from reasonnotes_sync.state_envelope import StateEnvelope


LIVE = UUID("11111111-1111-4111-8111-111111111111")
CONFLICT = UUID("22222222-2222-4222-8222-222222222222")
DELETED = UUID("33333333-3333-4333-8333-333333333333")
NOW = datetime(2026, 10, 24, 14, 0, tzinfo=timezone.utc)


class LegacyMigrationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.legacy_root = self.base / "legacy"
        self.staging = self.base / "migration" / "v2.staging"
        self.active = self.base / "migration" / "v2"

    def repository(self):
        return Repository.open(self.legacy_root)

    @staticmethod
    def import_revision(repository: Repository, revision: Revision):
        outcome = repository.import_bytes(revision.serialize(), revision.transport_filename())
        if outcome.kind not in ("imported", "duplicate"):
            raise AssertionError(outcome)

    def test_migrates_live_note_conflict_and_deletion_then_erases_legacy_history(self):
        legacy = self.repository()
        legacy.create_revision(LIVE, "# Live title\n\nLive body", "android", NOW)
        base = legacy.create_revision(CONFLICT, "# Base\n\nbase", "android", NOW)
        local = Revision.create(
            CONFLICT,
            (base.revision_id,),
            "android",
            NOW + timedelta(seconds=1),
            False,
            "# Local\n\nlocal body",
        )
        remote = Revision.create(
            CONFLICT,
            (base.revision_id,),
            "linux",
            NOW + timedelta(seconds=2),
            False,
            "# Remote\n\nremote body",
        )
        self.import_revision(legacy, local)
        self.import_revision(legacy, remote)
        deleted_base = legacy.create_revision(
            DELETED, "# Erase me\n\nsecret", "android", NOW
        )
        tombstone = Revision.create(
            DELETED,
            (deleted_base.revision_id,),
            "android",
            NOW + timedelta(seconds=3),
            True,
            "",
        )
        self.import_revision(legacy, tombstone)

        report = migrate_legacy_repository(self.legacy_root, self.staging, self.active)

        self.assertEqual((1, 1, 1), (report.live_notes, report.conflicts, report.deletions))
        migrated = CurrentNoteStore.open(self.active, "linux")
        self.assertEqual("Live title", migrated.get(LIVE).title)
        self.assertEqual("Live body", migrated.get(LIVE).body)
        self.assertEqual(2, len(migrated.conflict(CONFLICT).candidates))
        self.assertIsNone(migrated.get(DELETED))
        stale = StateEnvelope.upsert(DELETED, (), "android", NOW, "Erase me", "secret")
        self.assertEqual("rejected-deleted", migrated.apply(stale).kind)
        self.assertFalse(self.legacy_root.exists())

    def test_converted_state_ids_match_android_migration_fixture(self):
        legacy = self.repository()
        legacy.create_revision(
            LIVE, "# Live title\n\nLive body", "android", NOW
        )

        migrate_legacy_repository(self.legacy_root, self.staging, self.active)

        state = CurrentNoteStore.open(self.active, "linux").get(LIVE)
        self.assertEqual((), state.parent_change_ids)
        self.assertEqual(
            "9902d12d9692f3866c1267c089c02ae85d17a5f97f78e9a394d56130ddba3b60",
            state.change_id,
        )

    def test_incomplete_staging_is_rebuilt_and_does_not_become_active_early(self):
        legacy = self.repository()
        legacy.create_revision(LIVE, "# Title\n\nBody", "android", NOW)
        self.staging.mkdir(parents=True)
        (self.staging / "partial.txt").write_text("incomplete", encoding="utf-8")

        migrate_legacy_repository(self.legacy_root, self.staging, self.active)

        self.assertTrue(self.active.is_dir())
        self.assertFalse(self.staging.exists())
        self.assertFalse((self.active / "partial.txt").exists())
        self.assertIsNotNone(CurrentNoteStore.open(self.active, "linux").get(LIVE))

    def test_existing_valid_active_store_finishes_retiring_legacy(self):
        legacy = self.repository()
        legacy.create_revision(LIVE, "# Title\n\nBody", "android", NOW)
        migrate_legacy_repository(self.legacy_root, self.staging, self.active)
        self.assertFalse(self.legacy_root.exists())

        # Recreate the exact old store to model a crash after activation and
        # before retirement, then prove the active store is validated first.
        legacy = self.repository()
        legacy.create_revision(LIVE, "# Title\n\nBody", "android", NOW)

        report = migrate_legacy_repository(self.legacy_root, self.staging, self.active)

        self.assertEqual(1, report.live_notes)
        self.assertFalse(self.legacy_root.exists())
        self.assertIsNotNone(CurrentNoteStore.open(self.active, "linux").get(LIVE))

    def test_missing_ancestry_refuses_without_switching_or_removing_legacy(self):
        legacy = self.repository()
        incomplete = Revision.create(
            LIVE, ("f" * 64,), "android", NOW, False, "# Title\n\nBody"
        )
        self.import_revision(legacy, incomplete)

        with self.assertRaisesRegex(RuntimeError, "missing ancestry"):
            migrate_legacy_repository(self.legacy_root, self.staging, self.active)

        self.assertFalse(self.active.exists())
        self.assertTrue(self.legacy_root.is_dir())

    def test_refused_migration_does_not_create_generated_legacy_views(self):
        incomplete = Revision.create(
            LIVE, ("f" * 64,), "android", NOW, False, "# Title\n\nBody"
        )
        history = self.legacy_root / "history" / str(LIVE)
        history.mkdir(parents=True)
        (history / f"{incomplete.revision_id}.md").write_bytes(incomplete.serialize())

        with self.assertRaisesRegex(RuntimeError, "missing ancestry"):
            migrate_legacy_repository(self.legacy_root, self.staging, self.active)

        self.assertEqual(["history"], sorted(path.name for path in self.legacy_root.iterdir()))
        self.assertFalse(self.active.exists())

    def test_malformed_history_refuses_without_switching(self):
        legacy = self.repository()
        directory = self.legacy_root / "history" / str(LIVE)
        directory.mkdir(parents=True, exist_ok=True)
        (directory / f"{'a' * 64}.md").write_text("not a revision", encoding="utf-8")

        with self.assertRaisesRegex(RuntimeError, "malformed legacy history"):
            migrate_legacy_repository(self.legacy_root, self.staging, self.active)

        self.assertTrue(self.legacy_root.is_dir())
        self.assertFalse(self.active.exists())

    def test_more_than_two_live_heads_refuses_without_switching(self):
        legacy = self.repository()
        base = legacy.create_revision(LIVE, "# Base\n\nbase", "android", NOW)
        for index in range(3):
            self.import_revision(
                legacy,
                Revision.create(
                    LIVE,
                    (base.revision_id,),
                    f"device-{index}",
                    NOW + timedelta(seconds=index + 1),
                    False,
                    f"# Head {index}\n\nbody {index}",
                ),
            )

        with self.assertRaisesRegex(RuntimeError, "more than two heads"):
            migrate_legacy_repository(self.legacy_root, self.staging, self.active)

        self.assertTrue(self.legacy_root.is_dir())
        self.assertFalse(self.active.exists())


if __name__ == "__main__":
    unittest.main()
