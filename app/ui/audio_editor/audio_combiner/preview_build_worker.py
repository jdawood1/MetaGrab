import tempfile
import traceback
from pathlib import Path

from mutagen.mp3 import MP3
from PySide6.QtCore import QObject, QRunnable, Signal, Slot

from app.core import processes as subprocess


class PreviewWorkerSignals(QObject):
    finished = Signal(str, list)

    def __init__(self, parent=None):
        super().__init__(parent)


class PreviewBuildWorker(QRunnable):
    def __init__(self, file_paths: list[str]):
        super().__init__()
        self.file_paths = file_paths
        self.temp_dir = tempfile.TemporaryDirectory(prefix="metagrab-preview-")
        self.signals = PreviewWorkerSignals()

    @Slot()
    def run(self):
        try:
            if subprocess.closing.is_set():
                return
            temp_dir = Path(self.temp_dir.name)
            concat_txt = temp_dir / "preview_concat.txt"
            preview_mp3 = temp_dir / "preview_combined.mp3"

            with concat_txt.open("w", encoding="utf-8") as f:
                for path in self.file_paths:
                    escaped = Path(path).as_posix().replace("'", "'\\''")
                    f.write(f"file '{escaped}'\n")

            durations = []
            for path in self.file_paths:
                try:
                    audio = MP3(path)
                    durations.append(audio.info.length)
                except Exception:
                    durations.append(0.0)

            cumulative_ms = [int(sum(durations[:i]) * 1000) for i in range(1, len(durations))]

            cmd = [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_txt),
                "-c",
                "copy",
                str(preview_mp3),
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            if subprocess.closing.is_set():
                return
            if preview_mp3.exists():
                self.signals.finished.emit(str(preview_mp3), cumulative_ms)
            else:
                self.signals.finished.emit("", [])

        except Exception:
            if not subprocess.closing.is_set():
                traceback.print_exc()
                self.signals.finished.emit("", [])
