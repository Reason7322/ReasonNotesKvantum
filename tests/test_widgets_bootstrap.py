from pathlib import Path
from tempfile import TemporaryDirectory
import os
import subprocess
import sys
import unittest
from unittest.mock import patch


class WidgetsBootstrapTests(unittest.TestCase):
    def test_candidate_default_is_distinct_from_production(self):
        from reasonnotes_widgets.bootstrap import (
            candidate_data_directory,
            production_data_directory,
        )

        with TemporaryDirectory() as folder:
            home = Path(folder)
            with patch.dict(os.environ, {"HOME": str(home)}, clear=False):
                os.environ.pop("XDG_DATA_HOME", None)
                candidate = candidate_data_directory()
                production = production_data_directory()

        self.assertEqual(candidate, home / ".local/share/ReasonNotesKvantum-candidate")
        self.assertEqual(production, home / ".local/share/ReasonNotes")
        self.assertNotEqual(candidate, production)

    def test_xdg_default_and_explicit_paths_remain_isolated(self):
        from reasonnotes_widgets.bootstrap import resolve_launch_paths

        with TemporaryDirectory() as folder:
            base = Path(folder)
            xdg = base / "xdg-data"
            explicit_root = base / "fixture-repository"
            explicit_inbox = base / "fixture-inbox"
            received = base / "received"
            with patch.dict(
                os.environ,
                {"HOME": str(base / "home"), "XDG_DATA_HOME": str(xdg)},
                clear=False,
            ):
                defaults = resolve_launch_paths()
                explicit = resolve_launch_paths(
                    root=explicit_root, inbox=explicit_inbox, received_dir=received
                )

        self.assertEqual(
            defaults.repository,
            xdg / "ReasonNotesKvantum-candidate/repository",
        )
        self.assertEqual(defaults.inbox, xdg / "ReasonNotesKvantum-candidate/inbox")
        self.assertEqual(explicit.repository, explicit_root)
        self.assertEqual(explicit.inbox, explicit_inbox)
        self.assertEqual(explicit.received_dir, received)

    def test_production_repository_and_children_are_rejected(self):
        from reasonnotes_widgets.bootstrap import UnsafeProductionPath, resolve_launch_paths

        with TemporaryDirectory() as folder:
            home = Path(folder)
            production = home / ".local/share/ReasonNotes"
            with patch.dict(os.environ, {"HOME": str(home)}, clear=False):
                os.environ.pop("XDG_DATA_HOME", None)
                with self.assertRaises(UnsafeProductionPath):
                    resolve_launch_paths(root=production / "repository")
                with self.assertRaises(UnsafeProductionPath):
                    resolve_launch_paths(inbox=production / "inbox")

    def test_canonical_production_path_is_rejected_when_xdg_data_home_changes(self):
        from reasonnotes_widgets.bootstrap import UnsafeProductionPath, resolve_launch_paths

        with TemporaryDirectory() as folder:
            base = Path(folder)
            home = base / "home"
            canonical = home / ".local/share/ReasonNotes"
            environment = {
                "HOME": str(home),
                "XDG_DATA_HOME": str(base / "isolated-xdg"),
            }
            with self.assertRaises(UnsafeProductionPath):
                resolve_launch_paths(
                    root=canonical / "repository",
                    environ=environment,
                    home=home,
                )

    def test_qapplication_uses_installed_kvantum_style_and_distinct_identity(self):
        from reasonnotes_widgets.bootstrap import APP_ID, create_application

        with patch.dict(os.environ, {"QT_QPA_PLATFORM": "offscreen"}, clear=False):
            application = create_application(["reasonnotes-kvantum-test"])

        self.assertEqual(application.style().objectName().casefold(), "kvantum")
        self.assertEqual(application.applicationName(), "ReasonNotesKvantum")
        self.assertEqual(application.desktopFileName(), APP_ID)

    def test_qt6ct_dolphin_style_proxy_preserved_in_separate_process(self):
        """qt6ct-style over Kvantum must not be replaced by bare Kvantum."""
        project = Path(__file__).resolve().parents[1]
        with TemporaryDirectory() as folder:
            base = Path(folder)
            qt6ct = base / "qt6ct"
            qt6ct.mkdir(parents=True)
            (qt6ct / "qt6ct.conf").write_text(
                "[Appearance]\nstyle=kvantum\nicon_theme=YAMIS\n"
                "color_scheme_path=/usr/share/color-schemes/BreezeDark.colors\n"
                "custom_palette=true\n"
                "[Fonts]\ngeneral=\"Lato,11,-1,5,400,0,0,0,0,0,0,0,0,0,0,1,,0,0\"\n",
                encoding="utf-8",
            )
            environment = dict(os.environ)
            environment.update({
                "QT_QPA_PLATFORM": "offscreen",
                "QT_QPA_PLATFORMTHEME": "qt6ct",
                "XDG_CONFIG_HOME": str(base),
                "PYTHONPATH": str(project / "src"),
            })
            completed = subprocess.run([
                sys.executable, "-c",
                "from reasonnotes_widgets.bootstrap import create_application;"
                "from PySide6.QtWidgets import QProxyStyle;"
                "a=create_application(['probe']);"
                "s=a.style();b=s.baseStyle() if isinstance(s,QProxyStyle) else s;"
                "print(s.objectName(),b.objectName())"
            ], env=environment, capture_output=True, text=True, timeout=10)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        if "qt6ct-style" not in completed.stdout:
            self.skipTest("qt6ct platform theme plugin unavailable")
        self.assertIn("qt6ct-style kvantum", completed.stdout)

    def test_candidate_entrypoint_check_launch_does_not_shadow_package(self):
        project = Path(__file__).resolve().parents[1]
        environment = dict(os.environ)
        environment["QT_QPA_PLATFORM"] = "offscreen"
        environment["PYTHONPATH"] = str(project / "src")

        completed = subprocess.run(
            [sys.executable, str(project / "linux-app/reasonnotes_widgets.py"),
             "--check-launch"],
            env=environment,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == "__main__":
    unittest.main()
