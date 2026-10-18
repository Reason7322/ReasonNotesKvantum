from importlib.util import module_from_spec, spec_from_file_location
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_installer():
    path = PROJECT_ROOT / "scripts/install-candidate.py"
    spec = spec_from_file_location("reasonnotes_candidate_installer", path)
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CandidateInstallTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.home = Path(self.temporary.name)
        self.install_root = self.home / ".local/opt/reasonnotes-kvantum-candidate"
        self.launcher = self.home / ".local/bin/reasonnotes-kvantum-candidate"
        self.desktop = (
            self.home
            / ".local/share/applications/org.reasonnotes.ReasonNotesKvantum.desktop"
        )
        self.production_launcher = self.home / ".local/bin/reasonnotes"
        self.production_data = self.home / ".local/share/ReasonNotes"
        self.production_launcher.parent.mkdir(parents=True)
        self.production_data.mkdir(parents=True)
        self.production_launcher.write_bytes(b"production-launcher")
        (self.production_data / "marker").write_bytes(b"production-data")
        self.installer = load_installer()

    def install(self, version="candidate-one"):
        return self.installer.install_candidate(
            source_root=PROJECT_ROOT,
            install_root=self.install_root,
            launcher_path=self.launcher,
            desktop_path=self.desktop,
            version=version,
            build_native=False,
            home=self.home,
        )

    def assert_production_untouched(self):
        self.assertEqual(self.production_launcher.read_bytes(), b"production-launcher")
        self.assertEqual(
            (self.production_data / "marker").read_bytes(), b"production-data"
        )

    def test_versioned_install_is_distinct_and_leaves_production_untouched(self):
        result = self.install()

        self.assertEqual(result.release, self.install_root / "releases/candidate-one")
        self.assertTrue((result.release / "linux-app/reasonnotes_widgets.py").is_file())
        self.assertTrue((result.release / "src/reasonnotes_app/service.py").is_file())
        self.assertEqual((self.install_root / "current").resolve(), result.release)
        self.assertTrue(os.access(self.launcher, os.X_OK))
        self.assertIn(str(self.install_root / "current"), self.launcher.read_text())
        self.assertIn(str(self.launcher), self.desktop.read_text())
        self.assertNotIn("ReasonNotes/", self.launcher.read_text())
        self.assertFalse((result.release / ".config/Kvantum").exists())
        self.assert_production_untouched()

    def test_existing_release_is_never_overwritten(self):
        release = self.install().release
        marker = release / "preserve-me"
        marker.write_text("original")

        with self.assertRaises(FileExistsError):
            self.install()

        self.assertEqual(marker.read_text(), "original")
        self.assert_production_untouched()

    def test_prior_release_is_retained_and_can_be_reactivated(self):
        first = self.install("candidate-one").release
        second = self.install("candidate-two").release
        self.assertEqual((self.install_root / "current").resolve(), second)

        self.installer.activate_release(self.install_root, "candidate-one")

        self.assertTrue(first.is_dir())
        self.assertTrue(second.is_dir())
        self.assertEqual((self.install_root / "current").resolve(), first)
        self.assert_production_untouched()

    def test_installed_launcher_runs_with_isolated_default_data(self):
        self.install()
        data_home = self.home / "candidate-data"
        environment = dict(os.environ)
        environment.update(
            HOME=str(self.home),
            XDG_DATA_HOME=str(data_home),
            QT_QPA_PLATFORM="offscreen",
        )

        result = subprocess.run(
            [str(self.launcher), "--check-launch"],
            env=environment,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((data_home / "ReasonNotesKvantum-candidate").is_dir())
        self.assertFalse((data_home / "ReasonNotes").exists())
        self.assert_production_untouched()

    def test_production_named_targets_are_rejected(self):
        with self.assertRaises(self.installer.UnsafeInstallTarget):
            self.installer.install_candidate(
                source_root=PROJECT_ROOT,
                install_root=self.home / ".local/opt/reasonnotes",
                launcher_path=self.production_launcher,
                desktop_path=self.desktop,
                version="unsafe",
                build_native=False,
                home=self.home,
            )
        self.assert_production_untouched()

    def test_broad_parent_target_that_could_replace_production_is_rejected(self):
        with self.assertRaises(self.installer.UnsafeInstallTarget):
            self.installer.install_candidate(
                source_root=PROJECT_ROOT,
                install_root=self.home / ".local/opt",
                launcher_path=self.launcher,
                desktop_path=self.desktop,
                version="unsafe-parent",
                build_native=False,
                home=self.home,
            )
        self.assert_production_untouched()

    def test_activation_rejects_production_root_and_preserves_current_link(self):
        production_root = self.home / ".local/opt/reasonnotes"
        release = production_root / "releases/production-version"
        release.mkdir(parents=True)
        old_release = production_root / "releases/old-version"
        old_release.mkdir()
        current = production_root / "current"
        current.symlink_to(Path("releases/old-version"))

        with self.assertRaises(self.installer.UnsafeInstallTarget):
            self.installer.activate_release(
                production_root, "production-version", home=self.home
            )

        self.assertEqual(os.readlink(current), "releases/old-version")
        self.assert_production_untouched()


if __name__ == "__main__":
    unittest.main()
