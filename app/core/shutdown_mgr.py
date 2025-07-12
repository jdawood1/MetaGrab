import time
from typing import Callable, List
from app.core.logger import logger
from app.ui.topbar_widget.utils.tor_switches import active_tor_runnables
from app.systems.download_system.download_worker import active_download_threads
from app.ui.audio_editor.editing_tools.audio_workers import active_audio_threads


class ShutdownManager:
    def __init__(self):
        self._components: List[Callable[[], None]] = []
        self._pre_shutdown_tasks: List[Callable[[], None]] = []

    def register(self, shutdown_callable: Callable[[], None]):
        """Register a shutdown function (e.g. tor_manager.stop)."""
        self._components.append(shutdown_callable)
        logger.debug(f"ShutdownManager: Registered {shutdown_callable.__name__}")

    def register_pre_task(self, pre_callable: Callable[[], None]):
        """Register a task to run before shutdown (e.g. thread wait)."""
        self._pre_shutdown_tasks.append(pre_callable)
        logger.debug(f"ShutdownManager: Registered pre-task {pre_callable.__name__}")

    def wait_for_tor_runnables(self, timeout=5):
        """Wait for TorControlRunnable tasks to finish before shutdown."""
        logger.info("ShutdownManager: Waiting for Tor tasks to finish...")
        start = time.time()

        while active_tor_runnables and (time.time() - start) < timeout:
            time.sleep(0.1)

        if active_tor_runnables:
            logger.warning(f"TorControl: {len(active_tor_runnables)} thread(s) still active at shutdown.")
        else:
            logger.debug("TorControl: All threads exited cleanly.")

    def wait_for_downloads(self, timeout=5):
        """Cancel and wait for download threads (QThread) to exit."""
        logger.info("ShutdownManager: Waiting for download threads to finish...")
        start = time.time()

        for worker in list(active_download_threads):
            logger.warning(f"ShutdownManager: Cancelling active download: {worker.url}")
            worker.stop()

        while active_download_threads and (time.time() - start) < timeout:
            time.sleep(0.1)

        if active_download_threads:
            logger.warning(f"{len(active_download_threads)} download thread(s) still active.")
        else:
            logger.debug("All downloads finished before shutdown.")

    def wait_for_audio_threads(self, timeout=5):
        """Cancel and wait for audio processing threads to exit."""
        logger.info("ShutdownManager: Waiting for audio threads to finish...")
        start = time.time()

        for worker in list(active_audio_threads):
            logger.warning(f"ShutdownManager: Cancelling active audio thread for: {worker.output_path}")
            worker.stop()

        while active_audio_threads and (time.time() - start) < timeout:
            time.sleep(0.1)

        if active_audio_threads:
            logger.warning(f"{len(active_audio_threads)} audio thread(s) still active at shutdown.")
        else:
            logger.debug("All audio threads finished before shutdown.")


    def shutdown(self):
        logger.info("ShutdownManager: Running pre-shutdown tasks...")
        for task in self._pre_shutdown_tasks:
            try:
                task()
                logger.debug(f"ShutdownManager: Executed pre-task {task.__name__}")
            except Exception as e:
                logger.warning(f"ShutdownManager: Error in pre-task {task.__name__}: {e}")

        logger.info("ShutdownManager: Running shutdown sequence...")
        for shutdown_fn in reversed(self._components):
            try:
                shutdown_fn()
                logger.debug(f"ShutdownManager: Executed {shutdown_fn.__name__}")
            except Exception as e:
                logger.warning(f"ShutdownManager: Error in {shutdown_fn.__name__}: {e}")