from PySide6.QtWidgets import QListWidgetItem
from app.core.logger import logger

class DownloadTaskTracker:
    """Tracks active downloads and updates QListWidget items."""

    FORMAT_NAMES = {
        '1': 'MP3', '2': 'FLAC', '3': 'MP4', '4': 'AudioOnly', '5': 'VideoOnly',
        '6': 'MKV', '7': 'WEBM', '8': 'AVI', '9': 'MOV', '10': 'M4A', '11': 'OPUS',
        '12': 'AAC', '13': 'WAV',
    }

    def __init__(self, name: str, list_widget):
        self.name = name
        self.list_widget = list_widget
        self._tasks = {}  # task_key → {'item': QListWidgetItem, 'worker': QThread}

    def _get_display_format(self, format_choice: str) -> str:
        return self.FORMAT_NAMES.get(str(format_choice), f"Format-{format_choice}")

    def _make_key(self, url: str, format_choice: str) -> str:
        fmt = self._get_display_format(format_choice)
        return f"{url} [{fmt}]"

    def register_task(self, url: str, format_choice: str, worker):
        """Add a new task and its associated worker + UI item."""
        task_key = self._make_key(url, format_choice)

        if task_key in self._tasks:
            logger.info(f"[TaskTracker] Duplicate task: {task_key}")
            return None  # Already tracked

        item = QListWidgetItem(f"{task_key} ⏳ Starting...")
        self.list_widget.addItem(item)

        self._tasks[task_key] = {
            'item': item,
            'worker': worker
        }

        return task_key

    def update_status(self, task_key, message: str):
        entry = self._tasks.get(task_key)
        if entry:
            current = entry['item'].text()
            if any(tag in current for tag in ("🔥 Completed", "❌ Failed", "⚠️ Cancelled")):
                return  # Don't overwrite final states

            entry['item'].setText(f"{task_key} {message}")

            # Remove cancelled/failed tasks from tracking
            if any(tag in message for tag in ("❌ Failed", "⚠️ Cancelled")):
                self._tasks.pop(task_key, None)
                logger.info(f"[TaskTracker] Removed task from tracker: {task_key}")

    def mark_complete(self, task_key):
        self.update_status(task_key, "🔥 Completed")

    def mark_failed(self, task_key):
        self.update_status(task_key, "❌ Failed")

    def mark_cancelled(self, task_key):
        self.update_status(task_key, "⚠️ Cancelled by user")

    def force_unregister(self, task_key: str):
        """Untrack a task to allow re-downloads."""
        if task_key in self._tasks:
            self._tasks.pop(task_key, None)