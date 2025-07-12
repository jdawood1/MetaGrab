from PySide6.QtCore import QRunnable, Slot, QObject, Signal
import subprocess, json, re, os, signal
from pathlib import Path


class LufsSignalEmitter(QObject):
    finished = Signal(Path, dict)


class LufsRunner(QRunnable):
    def __init__(self, file_path: Path):
        super().__init__()
        self.file_path = file_path
        self.signals = LufsSignalEmitter()
        self._process = None
        self._terminated = False

    @Slot()
    def run(self):
        if self._terminated:
            return

        try:
            cmd = [
                "ffmpeg",
                "-i", str(self.file_path),
                "-af", "loudnorm=print_format=json",
                "-f", "null", "-"
            ]
            self._process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            _, stderr = self._process.communicate(timeout=60)

            if self._terminated:
                return

            json_blocks = re.findall(r'{[\s\S]+?input_i[\s\S]+?}', stderr)
            if not json_blocks:
                raise ValueError("No valid LUFS JSON block found.")

            data = json.loads(json_blocks[0])
            result = {
                "input_i": data.get("input_i", "?"),
                "input_tp": data.get("input_tp", "?"),
                "input_lra": data.get("input_lra", "?"),
                "input_thresh": data.get("input_thresh", "?")
            }

        except subprocess.TimeoutExpired:
            self._terminate_process()
            result = {"error": "LUFS analysis timed out."}
        except Exception as e:
            result = {"error": f"LUFS analysis failed: {e}"}
        finally:
            self._process = None

        self.signals.finished.emit(self.file_path, result)

    def terminate(self):
        self._terminated = True
        self._terminate_process()

    def _terminate_process(self):
        if self._process and self._process.poll() is None:
            try:
                if os.name == 'nt':
                    self._process.send_signal(signal.CTRL_BREAK_EVENT)
                else:
                    self._process.terminate()
                self._process.wait(timeout=5)
            except Exception:
                self._process.kill()