import os
import tempfile
from pathlib import Path
from typing import List

from PySide6.QtCore import QThread, Signal

from app.core import processes as subprocess
from app.core.logger import logger


class AudioCombiner:
    """Combines multiple audio files into one using FFmpeg concat."""

    @staticmethod
    def combine(inputs: List[str], output_path: str) -> bool:
        if len(inputs) < 2:
            logger.error("AudioCombiner: Need at least two files to combine.")
            return False

        list_file_path = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as list_file:
                for input_file in inputs:
                    abs_path = Path(input_file).resolve()
                    safe_path = abs_path.as_posix().replace("'", "'\\''")
                    list_file.write(f"file '{safe_path}'\n")
                list_file_path = list_file.name

            cmd = [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                list_file_path,
                "-c",
                "copy",
                output_path,
            ]

            logger.info(f"AudioCombiner: Combining {len(inputs)} files into {output_path}")
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

            logger.info(f"AudioCombiner: Combine successful — saved to {output_path}")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"AudioCombiner: FFmpeg failed: {e}")
            return False

        finally:
            if list_file_path and os.path.exists(list_file_path):
                os.remove(list_file_path)
                logger.debug("AudioCombiner: Temp file list cleaned up.")


class CombineWorker(QThread):
    """QThread wrapper for background audio combining."""

    finished = Signal(bool, str)

    def __init__(self, input_paths: List[str], output_path: str):
        super().__init__()
        self.input_paths = input_paths
        self.output_path = output_path
        from app.ui.audio_editor.editing_tools.audio_workers import active_audio_threads

        active_audio_threads.add(self)

    def stop(self):
        pass  # The coordinated shutdown cancels the owned subprocess group.

    def run(self):
        from app.ui.audio_editor.editing_tools.audio_workers import active_audio_threads

        try:
            success = AudioCombiner.combine(self.input_paths, self.output_path)
            if not subprocess.closing.is_set():
                self.finished.emit(success, self.output_path)
        finally:
            active_audio_threads.discard(self)
