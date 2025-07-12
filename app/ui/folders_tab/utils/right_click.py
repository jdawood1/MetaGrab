from PySide6.QtWidgets import QMenu, QMessageBox
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt
from pathlib import Path

from app.ui.dialog_box_builder import get_text, show_info, confirm_delete
from app.ui.folders_tab.utils.metadata_preview import get_audio_metadata

AUDIO_EXTENSIONS = {'.mp3', '.flac', '.wav', '.m4a', '.aac', '.ogg', '.webm'}


class ContextMenuHandler:
    def __init__(self, parent_window):
        self.parent = parent_window

    def show_menu(self, widget, pos):
        item = widget.itemAt(pos)
        menu = QMenu(widget)

        if not item:
            paste_action = QAction("Paste", widget)
            menu.addAction(paste_action)

            if menu.exec(widget.mapToGlobal(pos)) == paste_action:
                self.parent.handle_paste()
            return

        path = item.data(Qt.UserRole)
        if not path or not path.exists():
            return

        actions = {
            "Preview Info": lambda: self.parent.preview_item(item),
            "Show in Finder": self.parent.show_in_finder,
            "Rename...": lambda: self._show_rename_dialog(widget, path),
            "Delete": lambda: self._confirm_and_delete(widget, path)
        }

        if path.suffix.lower() in AUDIO_EXTENSIONS:
            actions["Meta Tags"] = lambda: self._show_audio_metadata(widget, path, pos)

        for name, callback in actions.items():
            if name == "Delete":
                menu.addSeparator()
            action = QAction(name, widget)
            menu.addAction(action)
            action.triggered.connect(callback)

        menu.exec(widget.mapToGlobal(pos))

    def _show_audio_metadata(self, widget, path: Path, pos):
        text = get_audio_metadata(path, widget)
        if text.lower().startswith("error") or "file not found" in text.lower():
            QMessageBox.information(widget, "Audio Metadata", text)
        else:
            self.parent.preview_box.set_text(text)
            self.parent.preview_box.show_at(widget.mapToGlobal(pos))

    def _show_rename_dialog(self, parent, path: Path):
        new_name = get_text(parent, "Rename File", "Enter a new filename", path.name)
        if new_name and new_name != path.name:
            try:
                new_path = path.parent / new_name
                path.rename(new_path)
                self.parent.refresh_list()
            except Exception as e:
                show_info(parent, "Rename Failed", f"Failed to rename file:\n{e}")

    def _confirm_and_delete(self, parent, path: Path):
        if confirm_delete(parent, path):
            self.parent.delete_selected()