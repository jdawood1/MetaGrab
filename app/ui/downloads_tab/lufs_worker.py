import json
import sys
from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, Signal, Slot

from app.core import processes as subprocess
from app.core.logger import logger
from app.systems.download_system.health import ensure_download_tools
from app.systems.download_system.utils.privacy_config import get_privacy_options


class LUFSWorkerSignals(QObject):
    result = Signal(object)
    error = Signal(str)


class LUFSWorker(QRunnable):
    def __init__(self, url: str):
        super().__init__()
        self.url = url
        self.signals = LUFSWorkerSignals()

    @Slot()
    def run(self):
        try:
            tools = ensure_download_tools(self.url, logger.info)
            privacy = get_privacy_options()
            result = subprocess.run(
                (
                    [sys.executable, "--metagrab-worker", "analysis"]
                    if getattr(sys, "frozen", False)
                    else [sys.executable, "-m", "app.systems.download_system.analysis_runner"]
                ),
                cwd=Path(__file__).resolve().parents[3],
                input=json.dumps({"url": self.url, "tools": tools, "privacy": privacy}) + "\n",
                capture_output=True,
                text=True,
                timeout=240,
            )
            response = None
            for line in reversed(result.stdout.splitlines()):
                try:
                    candidate = json.loads(line)
                    if isinstance(candidate, dict) and (
                        "report" in candidate or "error" in candidate
                    ):
                        response = candidate
                        break
                except ValueError:
                    continue
            if response is None:
                raise RuntimeError("Analysis process failed: " + result.stderr[-1200:])
            if "error" in response:
                raise RuntimeError(response["error"])
            report = response
            if not subprocess.closing.is_set():
                self.signals.result.emit(report)
        except subprocess.TimeoutExpired:
            if not subprocess.closing.is_set():
                self.signals.error.emit(
                    "Analysis exceeded four minutes. Please retry or use another source."
                )
        except Exception as exc:
            if not subprocess.closing.is_set():
                self.signals.error.emit(str(exc))
