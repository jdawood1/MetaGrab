import os
import unittest
from unittest.mock import Mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QListWidget

from app.ui.downloads_tab.download_window import DownloadsWindow
from app.ui.downloads_tab.task_tracker import DownloadTaskTracker


class DownloadProgressTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.list = QListWidget()
        self.tracker = DownloadTaskTracker("test", self.list)
        self.worker = Mock()
        self.worker.isRunning.return_value = False
        self.first = self.tracker.register_task("https://example.org/one", "1", self.worker)
        self.second = self.tracker.register_task("https://example.org/two", "3", self.worker)

    def tearDown(self):
        self.list.close()

    def test_interleaved_progress_is_independent(self):
        self.tracker.update_progress(
            self.first, {"status": "downloading", "downloaded_bytes": 25, "total_bytes": 100}
        )
        self.tracker.update_progress(
            self.second, {"status": "downloading", "downloaded_bytes": 80, "total_bytes": 100}
        )
        self.assertEqual(self.tracker._tasks[self.first]["progress"].value(), 25)
        self.assertEqual(self.tracker._tasks[self.second]["progress"].value(), 80)
        self.tracker.mark_complete(self.first)
        self.assertEqual(self.tracker._tasks[self.second]["progress"].value(), 80)
        self.assertEqual(self.tracker.summary()[1], 1)

    def test_terminal_row_ignores_late_progress(self):
        self.tracker.mark_failed(self.first, "Network error")
        self.tracker.update_progress(self.first, {"_percent_str": "70%"})
        self.assertEqual(self.tracker._tasks[self.first]["state"], "failed")
        self.assertEqual(self.tracker._tasks[self.first]["action"].text(), "Retry")

    def test_clear_does_not_remove_active_or_running_worker(self):
        self.assertFalse(self.tracker.force_unregister(self.first))
        self.tracker.mark_complete(self.first)
        self.worker.isRunning.return_value = True
        self.assertFalse(self.tracker.force_unregister(self.first))
        self.worker.isRunning.return_value = False
        self.assertTrue(self.tracker.force_unregister(self.first))

    def test_actions_target_their_own_id(self):
        cancel = Mock()
        retry = Mock()
        self.tracker.cancel_requested.connect(cancel)
        self.tracker.retry_requested.connect(retry)
        self.tracker._tasks[self.second]["action"].click()
        cancel.assert_called_once_with(self.second)
        self.tracker.mark_failed(self.first)
        self.tracker._tasks[self.first]["action"].click()
        retry.assert_called_once_with(self.first)

    def test_unknown_length_and_processing_are_indeterminate(self):
        self.tracker.update_progress(self.first, {"status": "downloading"})
        self.assertEqual(self.tracker._tasks[self.first]["progress"].maximum(), 0)
        self.tracker.update_progress(self.first, {"status": "finished"})
        self.assertEqual(self.tracker._tasks[self.first]["state"], "processing")

    def test_finishing_one_does_not_disable_cancel_for_other(self):
        window = DownloadsWindow()
        one, two = Mock(), Mock()
        one.isRunning.return_value = two.isRunning.return_value = False
        a = window.task_tracker.register_task("one", "1", one)
        b = window.task_tracker.register_task("two", "3", two)
        window.active_workers = {a: one, b: two}
        window.on_task_finished(a)
        self.assertTrue(window.cancel_button.isEnabled())
        window.cancel_download(b)
        two.stop.assert_called_once()
        one.stop.assert_not_called()
        window.handle_worker_cancelled(b)
        self.assertFalse(window.cancel_button.isEnabled())
        window.close()

    def test_same_url_uses_distinct_attempt_ids(self):
        another = self.tracker.register_task("https://example.org/one", "1", self.worker)
        self.assertNotEqual(self.first, another)
