from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QApplication
import yt_dlp

from app.systems.download_system.utils.format_spec import FormatSpec
from app.systems.download_system.utils.download_utils import get_temp_sandbox_folder
from app.systems.download_system.utils.file_mover import move_downloaded_files
from app.core.logger import logger

active_download_threads = set()

class DownloadWorker(QThread):
    progress = Signal(dict)
    status = Signal(str, str)
    finished = Signal(str)
    error = Signal(str, str)
    cancelled = Signal(str)

    def __init__(self, url: str, format_choice: str = '1', normalize: bool = False):
        super().__init__()
        self.url = url
        self.format_choice = format_choice
        self.normalize = normalize
        self._is_cancelled = False
        active_download_threads.add(self)

    def stop(self):
        logger.warning(f"DownloadWorker: Cancelling download → {self.url}")
        self._is_cancelled = True  # Do NOT emit anything yet

    def _emit_safe(self, signal, *args):
        if QApplication.instance() is None:
            return
        try:
            signal.emit(*args)
        except RuntimeError:
            pass

    def run(self):
        sandbox = get_temp_sandbox_folder()
        logger.info(f"Using sandbox: {sandbox}")

        try:
            options = FormatSpec.get_options(self.format_choice, sandbox)

            def hook(d):
                if self._is_cancelled:
                    raise Exception("__CANCELLED__")  # special marker
                if d['status'] == 'downloading':
                    self._emit_safe(self.progress, d)
                    percent = d.get('_percent_str', '').strip()
                    self._emit_safe(self.status, self.url, f"Downloading... {percent}")
                elif d['status'] == 'finished':
                    self._emit_safe(self.status, self.url, "Processing...")

            options['progress_hooks'] = [hook]

            with yt_dlp.YoutubeDL(options) as ydl:
                ydl.download([self.url])

            moved = move_downloaded_files(sandbox)

            for src, info in moved.items():
                logger.info(f"{info['type'].capitalize()} destination: {src.name} → {info['dest']}")

            # Late cancellation: treat as a success
            self._emit_safe(self.status, self.url, "🔥 Completed")
            self._emit_safe(self.finished, self.url)

        except Exception as e:
            if str(e) == "__CANCELLED__":
                self._emit_safe(self.status, self.url, "⚠️ Cancelled")
            else:
                self._emit_safe(self.status, self.url, "❌ Failed")
                self._emit_safe(self.error, self.url, str(e))

        finally:
            active_download_threads.discard(self)