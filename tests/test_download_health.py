import subprocess
import unittest
from unittest.mock import patch

from app.systems.download_system import health


class DownloadHealthTests(unittest.TestCase):
    def test_youtube_host_matching(self):
        self.assertTrue(health.is_youtube("https://www.youtube.com/watch?v=abc"))
        self.assertTrue(health.is_youtube("https://youtu.be/abc"))
        self.assertFalse(health.is_youtube("https://youtube.com.example.org/abc"))

    @patch.object(health, "find_tool", side_effect=lambda name: "/tools/" + name)
    @patch.object(health, "usable_deno", return_value=True)
    @patch.object(health.subprocess, "run", return_value=subprocess.CompletedProcess([], 0))
    @patch.object(health, "run_command")
    def test_healthy_youtube_uses_explicit_runtime_without_install(self, command, *mocks):
        result = health.ensure_download_tools("https://youtu.be/abc", lambda msg: None)
        self.assertEqual(result["js_runtimes"], {"deno": {"path": "/tools/deno"}})
        command.assert_not_called()

    @patch.object(health.sys, "platform", "darwin")
    @patch.object(health, "find_tool", return_value=None)
    @patch.object(health, "run_command")
    def test_no_homebrew_explains_missing_tools(self, command, find):
        with self.assertRaisesRegex(RuntimeError, "requires Homebrew"):
            health.ensure_download_tools("https://youtu.be/abc", lambda msg: None)
        command.assert_not_called()

    @patch.object(health.sys, "platform", "darwin")
    @patch.object(health, "find_tool", side_effect=lambda name: "/opt/homebrew/bin/" + name)
    @patch.object(health, "usable_deno", side_effect=[False, True])
    @patch.object(health.subprocess, "run", return_value=subprocess.CompletedProcess([], 0))
    @patch.object(health, "run_command")
    def test_old_deno_is_repaired_then_rechecked(self, command, *mocks):
        health.ensure_download_tools("https://youtu.be/abc", lambda msg: None)
        self.assertEqual(command.call_args.args[0], ["/opt/homebrew/bin/brew", "install", "deno"])

    @patch.object(health, "find_tool", side_effect=lambda name: "/tools/" + name)
    @patch.object(health, "usable_deno")
    @patch.object(health.subprocess, "run")
    def test_other_sites_do_not_require_youtube_components(self, probe, deno, find):
        result = health.ensure_download_tools("https://example.org/file", lambda msg: None)
        self.assertNotIn("js_runtimes", result)
        deno.assert_not_called()
        probe.assert_not_called()

    def test_cancel_before_preflight(self):
        with self.assertRaisesRegex(RuntimeError, "__CANCELLED__"):
            health.ensure_download_tools("https://youtu.be/abc", lambda msg: None, lambda: True)
        # The repair lock must be released even when cancelled.
        self.assertTrue(health._REPAIR_LOCK.acquire(blocking=False))
        health._REPAIR_LOCK.release()

    @patch.object(health.sys, "prefix", "test-venv")
    @patch.object(health, "find_tool", side_effect=lambda name: "/tools/" + name)
    @patch.object(health, "usable_deno", return_value=True)
    @patch.object(
        health.subprocess,
        "run",
        side_effect=[
            subprocess.CompletedProcess([], 1),
            subprocess.CompletedProcess([], 0),
        ],
    )
    @patch.object(health, "run_command")
    def test_missing_python_support_is_installed_and_verified(self, command, *mocks):
        health.ensure_download_tools("https://youtu.be/abc", lambda msg: None)
        self.assertIn("yt-dlp[default]", command.call_args.args[0])

    @patch.object(health, "run_command", return_value="deno 2.2.0\nv8 1.0")
    def test_unsupported_runtime_version(self, command):
        self.assertFalse(health.usable_deno("/tools/deno", lambda: False))
