import re
import uuid
from collections import Counter

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidgetItem,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class DownloadTaskTracker(QObject):
    """Own a separate row and lifecycle for every download attempt."""

    changed = Signal()
    cancel_requested = Signal(str)
    retry_requested = Signal(str)
    TERMINAL = {"completed", "failed", "cancelled"}

    FORMAT_NAMES = {
        "1": "MP3",
        "2": "FLAC",
        "3": "MP4",
        "4": "AudioOnly",
        "5": "VideoOnly",
        "6": "MKV",
        "7": "WEBM",
        "8": "AVI",
        "9": "MOV",
        "10": "M4A",
        "11": "OPUS",
        "12": "AAC",
        "13": "WAV",
    }

    def __init__(self, name, list_widget):
        super().__init__(list_widget)
        self.name = name
        self.list_widget = list_widget
        self._tasks = {}

    def register_task(self, url, format_choice, worker):
        key = uuid.uuid4().hex
        fmt = self.FORMAT_NAMES.get(str(format_choice), str(format_choice))
        row = QWidget()
        layout = QVBoxLayout(row)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(6)
        top = QHBoxLayout()
        title = QLabel(f"{url} [{fmt}]")
        title.setWordWrap(True)
        title.setToolTip(url)
        action = QPushButton("Cancel")
        action.setFixedWidth(85)
        top.addWidget(title, 1)
        top.addWidget(action)
        layout.addLayout(top)
        progress = QProgressBar()
        progress.setRange(0, 0)
        progress.setFixedHeight(18)
        layout.addWidget(progress)
        status = QLabel("Starting…")
        status.setWordWrap(True)
        layout.addWidget(status)
        item = QListWidgetItem()
        item.setData(Qt.UserRole, key)
        item.setSizeHint(row.sizeHint())
        self.list_widget.addItem(item)
        self.list_widget.setItemWidget(item, row)
        self._tasks[key] = dict(
            item=item,
            row=row,
            worker=worker,
            url=url,
            fmt=fmt,
            title=title,
            progress=progress,
            status=status,
            action=action,
            state="starting",
        )
        action.clicked.connect(lambda: self._activate(key))
        self.changed.emit()
        return key

    def _activate(self, key):
        entry = self._tasks.get(key)
        if not entry:
            return
        if entry["state"] in {"failed", "cancelled"}:
            self.retry_requested.emit(key)
        elif entry["state"] not in self.TERMINAL:
            self.cancel_requested.emit(key)

    def update_status(self, key, message):
        entry = self._tasks.get(key)
        if not entry or entry["state"] in self.TERMINAL:
            return
        if entry["state"] == "cancelling":
            return
        if "Completed" in message or "Cancelled" in message:
            return  # Dedicated outcome signals finalize the row.
        entry["status"].setText(message)
        if any(
            word in message.lower() for word in ("processing", "merging", "converting", "exporting")
        ):
            entry["state"] = "processing"
            entry["progress"].setRange(0, 0)
        self.changed.emit()

    def update_progress(self, key, data):
        entry = self._tasks.get(key)
        if not entry or entry["state"] in self.TERMINAL or entry["state"] == "cancelling":
            return
        if data.get("title"):
            entry["title"].setText(f"{data['title']} [{entry['fmt']}]")
        if data.get("status") == "finished":
            self.update_status(key, "Processing…")
            return
        entry["state"] = "downloading"
        total = data.get("total_bytes") or data.get("total_bytes_estimate")
        done = data.get("downloaded_bytes")
        percent = 100 * done / total if total and done is not None else None
        if percent is None:
            match = re.search(r"(\d+(?:\.\d+)?)%", data.get("_percent_str") or "")
            percent = float(match.group(1)) if match else None
        if percent is None:
            entry["progress"].setRange(0, 0)
        else:
            entry["progress"].setRange(0, 100)
            entry["progress"].setValue(max(0, min(100, int(percent))))
        details = ["Downloading current stream"]
        if data.get("speed"):
            details.append(f"{data['speed'] / 1024**2:.2f} MiB/s")
        if data.get("eta") is not None:
            seconds = max(0, int(data["eta"]))
            details.append(f"{seconds // 60}:{seconds % 60:02} remaining")
        entry["status"].setText(" · ".join(details))
        self.changed.emit()

    def mark_cancelling(self, key):
        entry = self._tasks.get(key)
        if entry and entry["state"] not in self.TERMINAL:
            entry["state"] = "cancelling"
            entry["status"].setText("Cancelling…")
            entry["action"].setEnabled(False)
            self.changed.emit()

    def _finish(self, key, state, error=None):
        entry = self._tasks.get(key)
        if not entry or entry["state"] in self.TERMINAL:
            return
        entry["state"] = state
        entry["status"].setText(
            state.capitalize() + (f": {error.splitlines()[0][:140]}" if error else "")
        )
        entry["status"].setToolTip(error or state.capitalize())
        entry["progress"].setRange(0, 100)
        entry["progress"].setValue(100 if state == "completed" else 0)
        entry["action"].setText("Done" if state == "completed" else "Retry")
        entry["action"].setEnabled(state != "completed")
        self.changed.emit()

    def mark_complete(self, key):
        self._finish(key, "completed")

    def mark_failed(self, key, error=None):
        self._finish(key, "failed", error)

    def mark_cancelled(self, key):
        self._finish(key, "cancelled")

    def summary(self):
        counts = Counter(entry["state"] for entry in self._tasks.values())
        active = sum(value for key, value in counts.items() if key not in self.TERMINAL)
        parts = [f"{active} active"]
        parts += [
            f"{counts[state]} {state}"
            for state in ("downloading", "processing", "completed", "failed", "cancelled")
            if counts[state]
        ]
        return " · ".join(parts), active

    def force_unregister(self, key):
        entry = self._tasks.get(key)
        if entry and (entry["state"] not in self.TERMINAL or entry["worker"].isRunning()):
            return False
        self._tasks.pop(key, None)
        self.changed.emit()
        return True
