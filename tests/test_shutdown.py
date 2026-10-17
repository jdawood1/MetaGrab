import gc
import os
import sys
import threading
import time
import unittest
import weakref
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QCoreApplication, QEvent, QThread
from PySide6.QtWidgets import QApplication, QListWidget, QTextEdit

from app.core import processes
from app.core.logger.ui_logger import UILogger
from app.core.shutdown_mgr import ShutdownManager
from app.ui.downloads_tab.task_tracker import DownloadTaskTracker


class ShutdownTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        processes.closing.clear()

    def tearDown(self):
        processes.cancel_all(force=True)
        processes.closing.clear()

    def test_cleanup_is_idempotent(self):
        manager = ShutdownManager()
        callback = Mock()
        manager.register(callback)
        manager._finish()
        manager.shutdown()
        callback.assert_called_once()

    def test_shutdown_joins_threads_and_does_not_ignore_timeout(self):
        manager = ShutdownManager()
        worker = Mock()
        worker.wait.return_value = False
        with self.assertRaisesRegex(RuntimeError, "keep waiting"):
            manager._wait_threads([worker], 0)
        worker.stop.assert_called_once()
        worker.wait.assert_called_once()

    def test_window_stays_open_until_worker_has_really_finished(self):
        from PySide6.QtTest import QTest
        from PySide6.QtWidgets import QWidget

        window = QWidget()
        window.tor_manager = Mock()
        worker = Mock()
        worker.isRunning.return_value = True
        worker.wait.return_value = True
        manager = ShutdownManager()
        manager._snapshot = lambda: [worker]
        window.show()
        manager.request(window)
        manager._poll()
        self.assertFalse(manager.complete)
        self.assertTrue(window.isVisible())
        worker.isRunning.return_value = False
        QTest.qWait(100)
        self.assertTrue(manager.complete)
        self.assertFalse(window.isVisible())
        worker.wait.assert_called_with(0)

    def test_stubborn_child_is_killed_and_reaped(self):
        process = processes.Popen(
            [
                sys.executable,
                "-c",
                "import signal,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); print('ready',flush=True); time.sleep(60)",
            ],
            stdout=processes.PIPE,
            text=True,
        )
        self.assertEqual(process.stdout.readline().strip(), "ready")
        processes.stop(process, timeout=0.1)
        self.assertIsNotNone(process.poll())
        self.assertNotIn(process, processes._processes)
        process.stdout.close()

    @unittest.skipUnless(os.name == "posix", "POSIX process groups")
    def test_cancellation_reaches_owned_grandchild_but_not_unrelated_process(self):
        unrelated = __import__("subprocess").Popen(
            [sys.executable, "-c", "import time; time.sleep(60)"]
        )
        program = (
            "import subprocess,sys,time; "
            "p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); "
            "print(p.pid,flush=True); time.sleep(60)"
        )
        with processes.Popen(
            [sys.executable, "-c", program], stdout=processes.PIPE, text=True
        ) as parent:
            child_pid = int(parent.stdout.readline())
            processes.stop(parent, timeout=0.2)
            self.assertIsNone(unrelated.poll())
            # A terminated orphan may briefly remain a zombie pending OS reaping.
            import psutil

            deadline = time.monotonic() + 2
            while time.monotonic() < deadline:
                if not psutil.pid_exists(child_pid):
                    break
                try:
                    if psutil.Process(child_pid).status() == psutil.STATUS_ZOMBIE:
                        break
                except psutil.NoSuchProcess:
                    break
                time.sleep(0.02)
            else:
                self.fail("Owned descendant remained alive")
        unrelated.terminate()
        unrelated.wait(timeout=5)

    def test_helper_children_stay_in_supervisors_group(self):
        import subprocess

        command = (
            "import os,sys; from app.core import processes; "
            "p=processes.Popen([sys.executable,'-c','import time; time.sleep(60)']); "
            "print(os.getpgrp(),os.getpgid(p.pid),flush=True); p.wait()"
        )
        with processes.Popen(
            [sys.executable, "-c", command],
            env={**os.environ, "METAGRAB_HELPER": "1"},
            stdout=subprocess.PIPE,
            text=True,
        ) as process:
            parent_group, child_group = map(int, process.stdout.readline().split())
            self.assertEqual(parent_group, process.pid)
            self.assertEqual(child_group, process.pid)
            processes.stop(process)

    def test_vanished_process_permission_error_is_harmless(self):
        process = processes.Popen([sys.executable, "-c", "pass"])
        process.wait(timeout=5)
        with (
            patch("app.core.processes.os.killpg", side_effect=PermissionError),
            patch("app.core.processes.os.getpgid", side_effect=ProcessLookupError),
        ):
            processes.stop(process)
        self.assertNotIn(process, processes._processes)

    def test_live_process_permission_error_is_preserved(self):
        process = processes.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
        try:
            with patch("app.core.processes.os.killpg", side_effect=PermissionError):
                with self.assertRaises(PermissionError):
                    process.terminate()
        finally:
            processes.stop(process)

    def test_preview_drops_error_callback_during_shutdown(self):
        from app.ui.audio_editor.audio_combiner.preview_build_worker import PreviewBuildWorker

        worker = PreviewBuildWorker([])
        messages = []
        worker.signals.finished.connect(lambda *args: messages.append(args))

        def cancelled(*args, **kwargs):
            processes.closing.set()
            raise RuntimeError("__CANCELLED__")

        try:
            with patch(
                "app.ui.audio_editor.audio_combiner.preview_build_worker.subprocess.run",
                side_effect=cancelled,
            ):
                worker.run()
            self.assertEqual(messages, [])
        finally:
            worker.temp_dir.cleanup()

    def test_analysis_drops_timeout_callback_during_shutdown(self):
        from app.ui.downloads_tab.lufs_worker import LUFSWorker

        worker = LUFSWorker("http://localhost/test.wav")
        messages = []
        worker.signals.error.connect(messages.append)

        def timed_out(*args, **kwargs):
            processes.closing.set()
            raise processes.TimeoutExpired("analysis", 240)

        with (
            patch("app.ui.downloads_tab.lufs_worker.ensure_download_tools", return_value={}),
            patch("app.ui.downloads_tab.lufs_worker.get_privacy_options", return_value={}),
            patch("app.ui.downloads_tab.lufs_worker.subprocess.run", side_effect=timed_out),
        ):
            worker.run()
        self.assertEqual(messages, [])

    def test_closed_application_rejects_new_subprocess(self):
        processes.closing.set()
        with self.assertRaisesRegex(RuntimeError, "__CANCELLED__"):
            processes.Popen([sys.executable, "-c", "pass"])

    def test_captured_output_does_not_deadlock(self):
        result = processes.run(
            [sys.executable, "-c", "import sys; sys.stderr.write('x'*200000); print('done')"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        self.assertEqual(result.stdout.strip(), "done")
        self.assertEqual(len(result.stderr), 200000)

    def test_logger_delivers_on_main_thread_and_drops_late_messages(self):
        logger = UILogger()
        widget = QTextEdit()
        logger.register_target("main", widget)
        calls = []
        original = logger._write_to_widget

        def record(*args):
            calls.append(QThread.currentThread())
            original(*args)

        logger._write_to_widget = record
        thread = threading.Thread(target=lambda: logger.info("worker message"))
        thread.start()
        thread.join()
        self.assertEqual(widget.toPlainText(), "")
        self.app.processEvents()
        self.assertEqual(widget.toPlainText().strip(), "worker message")
        self.assertEqual(calls, [self.app.thread()])
        logger.info("late message")
        logger.shutdown()
        self.app.processEvents()
        self.assertNotIn("late message", widget.toPlainText())
        widget.close()

    def test_completed_history_releases_workers_when_cleared(self):
        widget = QListWidget()
        tracker = DownloadTaskTracker("memory", widget)
        references = []
        for number in range(100):
            worker = QThread()
            references.append(weakref.ref(worker))
            key = tracker.register_task(str(number), "1", worker)
            tracker.mark_complete(key)
            item = tracker._tasks[key]["item"]
            self.assertTrue(tracker.force_unregister(key))
            widget.takeItem(widget.row(item))
            del item, worker
            QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        gc.collect()
        self.assertFalse(any(reference() for reference in references))
        widget.close()
