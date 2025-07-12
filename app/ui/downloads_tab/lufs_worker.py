from PySide6.QtCore import QObject, QRunnable, Signal, Slot
import tempfile
import os

from yt_dlp import YoutubeDL

from app.core.logger import logger


class LUFSWorkerSignals(QObject):
    result = Signal(str)
    error = Signal(str)


class LUFSWorker(QRunnable):
    def __init__(self, url: str):
        super().__init__()
        self.url = url
        self.signals = LUFSWorkerSignals()

    @Slot()
    def run(self):
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                sample_path = os.path.join(tmpdir, "sample.%(ext)s")

                # Download a short sample using yt_dlp Python API
                ydl_opts = {
                    'format': 'bestaudio',
                    'outtmpl': sample_path,
                    'postprocessor_args': ['-t', '15'],  # Trim to 15s
                    'quiet': True,
                    'no_warnings': True,
                    'paths': {'home': tmpdir},
                    'noplaylist': True,
                }

                with YoutubeDL(ydl_opts) as ydl:
                    ydl.download([self.url])

                # Find the downloaded file
                sample_file = None
                for file in os.listdir(tmpdir):
                    if file.endswith((".m4a", ".webm", ".opus", ".mp3", ".aac", ".wav")):
                        sample_file = os.path.join(tmpdir, file)
                        break

                if not sample_file:
                    raise RuntimeError("Sample file not found after yt_dlp download.")

                # Analyze LUFS with FFmpeg
                lufs_cmd = [
                    "ffmpeg", "-i", sample_file,
                    "-filter_complex", "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=summary",
                    "-f", "null", "-"
                ]
                from subprocess import run, PIPE
                result = run(lufs_cmd, stdout=PIPE, stderr=PIPE, text=True)

                output = result.stderr

                logger.info("[LUFSWorker] Full LUFS analysis output:\n")
                logger.console(output)

                for line in output.splitlines():
                    if "Input Integrated" in line:
                        self.signals.result.emit(line.strip())
                        return

                self.signals.error.emit("LUFS data not found.")
        except Exception as e:
            self.signals.error.emit(str(e))