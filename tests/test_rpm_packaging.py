from __future__ import annotations

from pathlib import Path
import os
import runpy
import shlex
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

    def test_prepared_spec_declares_system_payload_and_fedora_runtime(self):
        with tempfile.TemporaryDirectory() as temporary:
            topdir, _output, _stdout = self.prepare(Path(temporary))
            spec = (topdir / "SPECS/reasonnotes.spec").read_text()

            for dependency in (
                "python3 >= 3.14",
                "python3-pyside6 >= 6.11",
                "kvantum",
                "qt6-qtwayland",
                "kde-connect",
            ):
                self.assertIn(f"Requires:       {dependency}\n", spec)
            for payload_path in (
                "%{_bindir}/reasonnotes",
                "%{_libdir}/reasonnotes/",
                "%{_datadir}/applications/org.reasonnotes.ReasonNotesKvantum.desktop",
                "%{_datadir}/icons/hicolor/scalable/apps/org.reasonnotes.ReasonNotesKvantum.svg",
            ):
                self.assertIn(payload_path, spec)
            self.assertIn(
                "%global debug_package %{nil}\n",
                spec,
                "the private single-RPM build must not emit an empty debugsource package",
            )
            self.assertIn(
                "%defattr(-,root,root,-)\n",
                spec,
                "the RPM payload must not inherit the unprivileged builder's ownership",
            )
            self.assertIn("License:        MIT\n", spec)
            description = spec.split("%description", 1)[1].split("%prep", 1)[0]
            self.assertNotIn("private", description.lower())

            desktop = topdir / "SOURCES/org.reasonnotes.ReasonNotesKvantum.desktop"
            validation = subprocess.run(
                ["desktop-file-validate", str(desktop)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(validation.returncode, 0, validation.stderr)

    def test_build_rejects_an_rpm_with_an_unexpected_output_name(self):
        with tempfile.TemporaryDirectory() as temporary:
            temporary_path = Path(temporary)
            topdir = temporary_path / "rpm topdir"
            output = temporary_path / "rpm output"
            fake_bin = temporary_path / "fake bin"
            fake_bin.mkdir()
            fake_rpmbuild = fake_bin / "rpmbuild"
            fake_rpmbuild.write_text(
                "#!/bin/sh\n"
                f"mkdir -p {shlex.quote(str(topdir / 'RPMS/x86_64'))}\n"
                f"touch {shlex.quote(str(topdir / 'RPMS/x86_64/reasonnotes-9.9-1.bad.x86_64.rpm'))}\n"
            )
            fake_rpmbuild.chmod(0o755)

            environment = dict(os.environ)
            environment["PATH"] = f"{fake_bin}:{environment['PATH']}"
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/build-rpm.py"),
                    "--topdir",
                    str(topdir),
                    "--output",
                    str(output),
                ],
                cwd=ROOT,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("expected one accepted-revision binary RPM", result.stderr)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
