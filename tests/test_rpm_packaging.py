from __future__ import annotations

from pathlib import Path
import runpy
import subprocess
import sys
import tarfile
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
ACCEPTED_REVISION = "cdf63233d2956718e5353ed58ad230dad07aad91"


class RpmPackagingTests(unittest.TestCase):
    def prepare(self, directory: Path):
        topdir = directory / "rpm topdir"
        output = directory / "rpm output"
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/build-rpm.py"),
                "--prepare-only",
                "--topdir",
                str(topdir),
                "--output",
                str(output),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return topdir, output, result.stdout

    def test_prepare_archives_exact_accepted_revision(self):
        with tempfile.TemporaryDirectory() as temporary:
            topdir, _output, stdout = self.prepare(Path(temporary))
            archive = topdir / "SOURCES/reasonnotes-0.1.0.tar.gz"
            self.assertTrue(archive.is_file())
            with tarfile.open(archive) as bundle:
                names = set(bundle.getnames())
                member = bundle.extractfile(
                    "reasonnotes-0.1.0/linux-app/reasonnotes_widgets.py"
                )
                self.assertIsNotNone(member)
                archived_entrypoint = member.read()
            accepted_entrypoint = subprocess.run(
                ["git", "show", f"{ACCEPTED_REVISION}:linux-app/reasonnotes_widgets.py"],
                cwd=ROOT,
                capture_output=True,
                check=True,
            ).stdout
            self.assertEqual(archived_entrypoint, accepted_entrypoint)
            self.assertIn("reasonnotes-0.1.0/src/reasonnotes_sync/sync.py", names)
            self.assertIn(f"PREPARED_REVISION={ACCEPTED_REVISION}", stdout)

    def test_prepared_launcher_uses_stable_xdg_paths_and_preserves_arguments(self):
        with tempfile.TemporaryDirectory() as temporary:
            topdir, _output, _stdout = self.prepare(Path(temporary))
            launcher = topdir / "SOURCES/reasonnotes"
            launcher_module = runpy.run_path(str(launcher))

            command = launcher_module["command"](
                {"HOME": "/home/test user", "XDG_DATA_HOME": "/data/with spaces"},
                ["--check-launch"],
                libdir=Path("/usr/lib64/reasonnotes"),
            )

            self.assertEqual(
                command,
                [
                    "/usr/bin/python3",
                    "/usr/lib64/reasonnotes/linux-app/reasonnotes_widgets.py",
                    "--root",
                    "/data/with spaces/reasonnotes/repository",
                    "--inbox",
                    "/data/with spaces/reasonnotes/inbox",
                    "--check-launch",
                ],
            )

    def test_prepared_launcher_ignores_relative_xdg_data_home(self):
        with tempfile.TemporaryDirectory() as temporary:
            topdir, _output, _stdout = self.prepare(Path(temporary))
            launcher = topdir / "SOURCES/reasonnotes"
            launcher_module = runpy.run_path(str(launcher))

            command = launcher_module["command"](
                {"HOME": "/home/reason", "XDG_DATA_HOME": "relative"},
                [],
                libdir=Path("/usr/lib64/reasonnotes"),
            )

            self.assertEqual(command[3], "/home/reason/.local/share/reasonnotes/repository")
            self.assertEqual(command[5], "/home/reason/.local/share/reasonnotes/inbox")


if __name__ == "__main__":
    unittest.main()
