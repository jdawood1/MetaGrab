import io
import unittest
from unittest.mock import patch

from app.systems.download_system import updater


class DownloaderUpdaterTests(unittest.TestCase):
    def setUp(self):
        updater._CHECKED = False

    def test_only_extraction_failures_trigger_repair(self):
        self.assertTrue(updater.is_extractor_failure("ERROR: The page needs to be reloaded."))
        for error in ["HTTP Error 403", "ffmpeg not found", "Sign in to confirm your age"]:
            self.assertFalse(updater.is_extractor_failure(error))

    def test_bundled_app_does_not_run_pip(self):
        with (
            patch.object(updater.sys, "frozen", True, create=True),
            patch.object(updater.subprocess, "run") as run,
        ):
            self.assertFalse(updater.update_if_outdated()[0])
            run.assert_not_called()

    def test_system_python_does_not_run_pip(self):
        with (
            patch.object(updater.sys, "prefix", updater.sys.base_prefix),
            patch.object(updater.subprocess, "run") as run,
        ):
            self.assertFalse(updater.update_if_outdated()[0])
            run.assert_not_called()

    @patch.object(updater.sys, "prefix", "test-virtual-environment")
    def test_updates_old_version_once(self):
        probe = updater.subprocess.CompletedProcess([], 0, "2025.3.31\n", "")
        success = updater.subprocess.CompletedProcess([], 0, "", "")
        with (
            patch.object(updater.subprocess, "run", side_effect=[probe, success]) as run,
            patch.object(
                updater, "urlopen", return_value=io.BytesIO(b'{"info":{"version":"2026.10.1"}}')
            ),
        ):
            self.assertTrue(updater.update_if_outdated()[0])
            command = run.call_args_list[1].args[0]
            self.assertIn("yt-dlp[default]", command)
            self.assertIn("--isolated", command)
            self.assertFalse(updater.update_if_outdated()[0])
            self.assertEqual(run.call_count, 2)

    @patch.object(updater.sys, "prefix", "test-virtual-environment")
    def test_current_version_is_not_reinstalled(self):
        probe = updater.subprocess.CompletedProcess([], 0, "2026.10.1\n", "")
        with (
            patch.object(updater.subprocess, "run", return_value=probe) as run,
            patch.object(
                updater, "urlopen", return_value=io.BytesIO(b'{"info":{"version":"2026.10.1"}}')
            ),
        ):
            self.assertFalse(updater.update_if_outdated()[0])
            self.assertEqual(run.call_count, 1)

    @patch.object(updater.sys, "prefix", "test-virtual-environment")
    def test_network_failure_is_reported_without_pip(self):
        probe = updater.subprocess.CompletedProcess([], 0, "2025.3.31\n", "")
        with (
            patch.object(updater.subprocess, "run", return_value=probe) as run,
            patch.object(updater, "urlopen", side_effect=OSError("offline")),
        ):
            retry, message = updater.update_if_outdated()
            self.assertFalse(retry)
            self.assertIn("offline", message)
            self.assertEqual(run.call_count, 1)
