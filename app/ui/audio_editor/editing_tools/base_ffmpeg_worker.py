from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QApplication

from app.core import processes as subprocess
from app.core.logger import logger


class BaseFFmpegWorker(QThread):
    finished = Signal(bool, str)

    def __init__(self, cmd: list[str], output_path: str, enable_logging: bool = False):
        super().__init__()
        self.cmd = cmd
        self.output_path = output_path
        self._cancelled = False
        self._process = None
        self.enable_logging = enable_logging

    def cancelled(self) -> bool:
        return self._cancelled

    def stop(self):
        self._cancelled = True
        if self._process and self._process.poll() is None:
            subprocess.stop(self._process)

    def _emit_safe(self, signal, *args):
        if QApplication.instance() and not subprocess.closing.is_set():
            try:
                signal.emit(*args)
            except RuntimeError:
                pass

    def run(self):
        logger.debug(f"[{self.__class__.__name__}] Starting FFmpeg process: {' '.join(self.cmd)}")

        try:
            self._process = subprocess.Popen(
                self.cmd,
                stdout=None if not self.enable_logging else subprocess.PIPE,
                stderr=None if not self.enable_logging else subprocess.PIPE,
            )
            _, stderr = self._process.communicate()

            success = self._process.returncode == 0 and not self._cancelled

            if self.enable_logging and stderr:
                logger.debug(stderr.decode(errors="replace")[-16000:])

            logger.info(
                f"[{self.__class__.__name__}] Finished: {'Success' if success else 'Failure'} - {self.output_path}"
            )
            self._emit_safe(self.finished, success, self.output_path)

        except Exception as e:
            logger.error(f"[{self.__class__.__name__}] Exception during FFmpeg run: {e}")
            self._emit_safe(self.finished, False, self.output_path)
        finally:
            if self._process is not None:
                subprocess.stop(self._process)
                for pipe in (self._process.stdout, self._process.stderr):
                    if pipe:
                        pipe.close()
                self._process = None
