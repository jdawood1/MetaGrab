from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QListWidgetItem

class DownloadContextMenu:
    """Context menu with Clear Selected and Clear All actions for the download list."""

    def __init__(self, parent, task_tracker):
        self.parent = parent  # QListWidget
        self.task_tracker = task_tracker
        self._setup_menu()

    def _setup_menu(self):
        self.menu = QMenu(self.parent)

        self.clear_selected_action = QAction("Clear Selected", self.parent)
        self.clear_all_action = QAction("Clear All", self.parent)

        self.menu.addAction(self.clear_selected_action)

        # Use actual separator now that it's visible
        self.menu.addSeparator()

        self.menu.addAction(self.clear_all_action)

        self.clear_selected_action.triggered.connect(self.clear_selected)
        self.clear_all_action.triggered.connect(self.clear_all)

    def show(self, position):
        self.menu.exec(self.parent.mapToGlobal(position))

    def clear_selected(self):
        selected_items = self.parent.selectedItems()
        for item in selected_items:
            task_key = self._extract_task_key(item)
            self.task_tracker.force_unregister(task_key)
            self.parent.takeItem(self.parent.row(item))

    def clear_all(self):
        for i in reversed(range(self.parent.count())):
            item = self.parent.item(i)
            task_key = self._extract_task_key(item)
            self.task_tracker.force_unregister(task_key)
            self.parent.takeItem(i)

    def _extract_task_key(self, item: QListWidgetItem) -> str:
        """Extract task key from item text (before the emoji/status marker)."""
        text = item.text()
        for marker in ("⏳", "🔥", "❌", "🚫"):
            if marker in text:
                return text.split(marker)[0].strip()
        return text.strip()