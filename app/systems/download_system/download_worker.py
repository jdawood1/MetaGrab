import json
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QApplication

from app.core.logger import logger
from app.systems.download_system.health import ensure_download_tools
from app.systems.download_system.selections import apply_selections
from app.systems.download_system.updater import is_extractor_failure, update_if_outdated
from app.systems.download_system.utils.download_utils import get_temp_sandbox_folder
from app.systems.download_system.utils.file_mover import move_downloaded_files
from app.systems.download_system.utils.format_spec import FormatSpec

active_download_threads = set()


class DownloadWorker(QThread):
    progress = Signal(dict)
    status = Signal(str, str)
    finished = Signal(str)
    error = Signal(str, str)
    cancelled = Signal(str)

    def __init__(
        self,
        url: str,
        format_choice: str = "1",
        normalize: bool = False,
        audio=None,
        caption=None,
        embed=False,
    ):
        super().__init__()
        self.url = url
        self.format_choice = format_choice
        self.normalize = normalize
        self.audio = audio
        self.caption = caption
        self.embed = embed
        self._is_cancelled = False
        self._process = None
        active_download_threads.add(self)

    def stop(self):
        logger.warning(f"DownloadWorker: Cancelling download → {self.url}")
        self._is_cancelled = True
        if self._process and self._process.poll() is None:
            self._process.terminate()

    def _emit_safe(self, signal, *args):
        if QApplication.instance() is None:
            return
        try:
            signal.emit(*args)
        except RuntimeError:
            pass

    def run(self):
        try:

            def report(message):
                logger.info(message)
                self._emit_safe(self.status, self.url, message)

            tool_options = ensure_download_tools(self.url, report, lambda: self._is_cancelled)
            if self._is_cancelled:
                raise RuntimeError("__CANCELLED__")
            sandbox = get_temp_sandbox_folder()
            logger.info(f"Using sandbox: {sandbox}")
            options = FormatSpec.get_options(self.format_choice, sandbox)
            options.update(tool_options)
            options = apply_selections(options, self.audio, self.caption, self.embed)

            for attempt in range(2):
                error = self._download(options)
                if self._is_cancelled:
                    raise RuntimeError("__CANCELLED__")
                if error is None:
                    break
                if attempt == 0 and is_extractor_failure(error):
                    self._emit_safe(self.status, self.url, "Checking downloader update...")
                    retry, explanation = update_if_outdated()
                    logger.info(explanation)
                    if retry:
                        self._emit_safe(self.status, self.url, "Downloader updated. Retrying...")
                        continue
                    error += "\n" + explanation
                raise RuntimeError(error)

            self._emit_safe(self.status, self.url, "Exporting files…")
            moved = move_downloaded_files(sandbox)

            for src, info in moved.items():
                logger.info(f"{info['type'].capitalize()} destination: {src.name} → {info['dest']}")

            # Late cancellation: treat as a success
            self._emit_safe(self.status, self.url, "🔥 Completed")
            self._emit_safe(self.finished, self.url)

        except Exception as e:
            if str(e) == "__CANCELLED__":
                self._emit_safe(self.status, self.url, "⚠️ Cancelled")
                self._emit_safe(self.cancelled, self.url)
            else:
                logger.error(f"Download failed: {e}")
                self._emit_safe(self.error, self.url, str(e))

        finally:
            active_download_threads.discard(self)

    def _download(self, options):
        if self._is_cancelled:
            return "Cancelled"
        if getattr(sys, "frozen", False):
            # A frozen executable cannot launch Python modules through sys.executable.
            from app.systems.download_system.anizone import create_downloader

            def hook(data):
                if self._is_cancelled:
                    raise RuntimeError("__CANCELLED__")
                self._emit_safe(
                    self.progress, {**data, "title": data.get("info_dict", {}).get("title")}
                )

            options = {
                **options,
                "progress_hooks": [hook],
                "postprocessor_hooks": [
                    lambda data: self._emit_safe(
                        self.status,
                        self.url,
                        "Processing: " + str(data.get("postprocessor") or "media"),
                    )
                ],
            }
            try:
                with create_downloader(options) as downloader:
                    result = downloader.download([self.url])
                return None if not result else "Downloader failed."
            except Exception as exc:
                return str(exc)
        errors = []
        warnings = []
        with subprocess.Popen(
            [sys.executable, "-m", "app.systems.download_system.download_runner"],
            cwd=Path(__file__).resolve().parents[3],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        ) as process:
            self._process = process
            process.stdin.write(json.dumps({"url": self.url, "options": options}) + "\n")
            process.stdin.close()
            for line in process.stdout:
                if self._is_cancelled:
                    process.terminate()
                try:
                    event = json.loads(line)
                except ValueError:
                    logger.debug(line.strip())
                    continue
                kind, payload = event["kind"], event["payload"]
                if kind == "progress":
                    self._emit_safe(self.progress, payload)
                elif kind == "processing":
                    self._emit_safe(self.status, self.url, "Processing: " + str(payload))
                elif kind == "error":
                    errors.append(payload)
                elif kind == "warning":
                    warnings.append(payload)
                    logger.warning(payload)
            code = process.wait()
            self._process = None
        if code:
            return "\n".join(warnings + errors) or f"Downloader exited with code {code}."
        return None
