import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.core import settings
from app.systems.download_system.utils import file_mover
from app.ui.folders_tab.folder_window import FolderWindow


class FolderAccessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_denied_listing_does_not_crash_window(self):
        with patch.object(FolderWindow, "_refresh_list", side_effect=PermissionError("denied")):
            window = FolderWindow()
        self.assertIn("Cannot access", window.folder_status.text())
        self.assertEqual(window.header.text(), "Folder access needed")
        window.close()

    def test_export_preference_persists_without_losing_other_settings(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "config"
            config.mkdir()
            preference = config / "user_settings.json"
            preference.write_text('{"home_ip": "example"}')
            with (
                patch.object(settings, "CONFIG_DIR", config),
                patch.object(settings, "USER_SETTINGS_FILE", preference),
                patch.object(settings, "EXPORTS_DIR", settings.EXPORTS_DIR),
            ):
                self.assertEqual(settings.set_exports_dir(root), root.resolve())
                self.assertEqual(settings.load_user_settings()["home_ip"], "example")
                self.assertEqual(settings.load_user_settings()["exports_dir"], str(root.resolve()))

    def test_unwritable_preference_does_not_change_destination(self):
        before = settings.EXPORTS_DIR
        with (
            tempfile.TemporaryDirectory() as directory,
            patch.object(settings, "save_user_settings", return_value=False),
        ):
            with self.assertRaises(OSError):
                settings.set_exports_dir(directory)
        self.assertEqual(settings.EXPORTS_DIR, before)

    def test_export_failure_is_reported_and_source_is_kept(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "sample.srt"
            source.write_text("caption")
            with (
                patch.object(file_mover.shutil, "move", side_effect=PermissionError("denied")),
                patch.object(settings, "EXPORTS_DIR", root / "exports"),
            ):
                with self.assertRaisesRegex(RuntimeError, "Could not save"):
                    file_mover.move_downloaded_files(root)
            self.assertTrue(source.exists())

    def test_chosen_folder_updates_view_and_drop_target(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            with patch.object(FolderWindow, "_refresh_list"):
                window = FolderWindow()
            with (
                patch(
                    "app.ui.folders_tab.folder_window.QFileDialog.getExistingDirectory",
                    return_value=directory,
                ),
                patch.object(settings, "set_exports_dir", return_value=target),
            ):
                window.choose_export_folder()
            self.assertEqual(window.current_dir, target)
            self.assertEqual(window.toggle_exports_btn.folder_path, target)
            window.close()
