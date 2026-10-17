"""Keep the Qt event loop alive until owned work has really stopped."""

import time

from PySide6.QtCore import QEvent, QObject, QThread, QThreadPool, QTimer, QUrl
from PySide6.QtMultimedia import QMediaPlayer

from app.core import processes
from app.core.logger import logger
from app.systems.download_system.download_worker import active_download_threads
from app.ui.audio_editor.editing_tools.audio_workers import active_audio_threads
from app.ui.topbar_widget.utils.tor_switches import active_tor_runnables


class ShutdownManager:
    def __init__(self):
        self._components = []
        self._pre_shutdown_tasks = []
        self._started = False
        self.complete = False
        self._workers = []
        self._timer = None

    def register(self, callback):
        if callback not in self._components:
            self._components.append(callback)

    def register_pre_task(self, callback):
        if callback not in self._pre_shutdown_tasks:
            self._pre_shutdown_tasks.append(callback)

    def _snapshot(self):
        return list(active_download_threads | active_audio_threads)

    def request(self, window):
        if self._started:
            return
        self._started = True
        self._window = window
        window.setEnabled(False)
        window.setWindowTitle("MetaGrab — stopping background work…")
        for timer in window.findChildren(QTimer):
            timer.stop()
        for player in window.findChildren(QMediaPlayer):
            player.stop()
            player.setSource(QUrl())
        self._workers = self._snapshot()
        processes.cancel_all()
        # Cancel bootstrap before waiting for its runnable.
        window.tor_manager.controller.cancel_bootstrap()
        window.tor_manager.controller.stop()
        for worker in self._workers:
            worker.stop()
        self._pools = list(window.findChildren(QThreadPool))
        self._pools.append(QThreadPool.globalInstance())
        self._since = time.monotonic()
        self._timer = QTimer(window)
        self._timer.timeout.connect(self._poll)
        self._timer.start(50)

    def _poll(self):
        if time.monotonic() - self._since > 2:
            processes.cancel_all(force=True)
        threads_done = all(not worker.isRunning() and worker.wait(0) for worker in self._workers)
        pools_done = all(pool.waitForDone(0) for pool in self._pools)
        if not threads_done or not pools_done or active_tor_runnables:
            return  # Never destroy a worker that is still running.
        self._timer.stop()
        from PySide6.QtWidgets import QWidget

        for widget in self._window.findChildren(QWidget):
            for name in ("_preview_temp_dir",):
                temporary = getattr(widget, name, None)
                if temporary is not None:
                    temporary.cleanup()
            worker = getattr(widget, "_current_preview_worker", None)
            temporary = getattr(worker, "temp_dir", None)
            if temporary is not None:
                temporary.cleanup()
        self._finish()
        self._window.close()

    def _finish(self):
        if self.complete:
            return
        for callback in reversed(self._components):
            try:
                callback()
            except Exception as exc:
                logger.warning(f"Shutdown cleanup failed: {exc}")
        self.complete = True
        self._workers.clear()

    def _wait_threads(self, workers, timeout):
        workers = list(workers)
        for worker in workers:
            worker.stop()
        deadline = time.monotonic() + timeout
        for worker in workers:
            if worker is QThread.currentThread():
                continue
            if not worker.wait(max(0, int((deadline - time.monotonic()) * 1000))):
                raise RuntimeError("Worker has not stopped; shutdown must keep waiting.")

    def wait_for_downloads(self, timeout=5):
        self._wait_threads(active_download_threads, timeout)

    def wait_for_audio_threads(self, timeout=5):
        self._wait_threads(active_audio_threads, timeout)

    def wait_for_tor_runnables(self, timeout=5):
        deadline = time.monotonic() + timeout
        while active_tor_runnables and time.monotonic() < deadline:
            time.sleep(0.05)
        if active_tor_runnables:
            raise RuntimeError("Tor work has not stopped.")

    def shutdown(self):
        if self.complete:
            return
        processes.cancel_all(force=True)
        for task in self._pre_shutdown_tasks:
            task()
        if not QThreadPool.globalInstance().waitForDone(5000):
            raise RuntimeError("Background pool has not stopped.")
        self._finish()


class QuitGuard(QObject):
    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.window = window

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Quit and not self.window.shutdown_manager.complete:
            self.window.close()
            return True
        return False
