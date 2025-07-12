import shutil
import subprocess
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QListWidgetItem, QApplication, QFileIconProvider
)
from PySide6.QtCore import Qt, QPoint, QEvent, QObject, QFileInfo
from PySide6.QtGui import QCursor, QGuiApplication, QColor
from send2trash import send2trash
from app.core.logger import logger
from app.core.settings import ORIGINALS_DIR, EXPORTS_DIR
from app.ui.dialog_box_builder import show_info, confirm_overwrite
from app.ui.folders_tab.utils.drag_n_drop import DropTargetButton
from app.ui.folders_tab.utils.preview_box import PreviewBox
from app.ui.folders_tab.utils.drag_n_drop import FileListWidget
from app.ui.folders_tab.utils.right_click import ContextMenuHandler

class GlobalClickFilter(QObject):
    def __init__(self, preview_box):
        super().__init__()
        self.preview_box = preview_box

    def eventFilter(self, obj, event):
        if event.type() in (QEvent.MouseButtonPress, QEvent.FocusOut, QEvent.WindowDeactivate):
            if self.preview_box.isVisible():
                self.preview_box.hide()
        return False


class FolderWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("FolderWindow")

        self.originals_dir = ORIGINALS_DIR
        self.exports_dir = EXPORTS_DIR
        self.last_custom_dir = None
        self.current_dir = self.exports_dir

        self._setup_ui()
        self.refresh_list()

        self.preview_box = PreviewBox(self)
        self.click_filter = GlobalClickFilter(self.preview_box)
        QApplication.instance().installEventFilter(self.click_filter)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Navigation
        nav_row = QHBoxLayout()
        self.back_button = QPushButton("Back")
        self.back_button.clicked.connect(self.go_back)

        self.toggle_exports_btn = DropTargetButton("View Downloads", self.exports_dir)
        self.toggle_originals_btn = DropTargetButton("View Originals", self.originals_dir)

        self.toggle_exports_btn.clicked.connect(self.show_exports)
        self.toggle_originals_btn.clicked.connect(self.show_originals)

        # Connect drag-drop signal to handler
        self.toggle_exports_btn.fileDropped.connect(self.handle_external_drop)
        self.toggle_originals_btn.fileDropped.connect(self.handle_external_drop)

        nav_row.addWidget(self.back_button)
        nav_row.addStretch()
        nav_row.addWidget(self.toggle_exports_btn)
        nav_row.addWidget(self.toggle_originals_btn)
        layout.addLayout(nav_row)

        # Header
        self.header = QLabel("Downloaded Files")
        self.header.setObjectName("HeaderLabel")
        self.header.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.header)

        # File List
        self.list_widget = FileListWidget(self)
        layout.addWidget(self.list_widget)
        self.list_widget.itemDoubleClicked.connect(self.open_selected)

        self.context_menu = ContextMenuHandler(self)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(
            lambda pos: self.context_menu.show_menu(self.list_widget, pos)
        )

        # Bottom Button Bar
        button_bar = QHBoxLayout()
        self.show_in_finder_button = QPushButton("Show in Finder")
        self.delete_button = QPushButton("Delete")
        self.delete_button.setObjectName("DeleteButton")
        self.refresh_button = QPushButton("↻ Refresh")

        button_bar.addWidget(self.show_in_finder_button)
        button_bar.addWidget(self.delete_button)
        button_bar.addStretch()
        button_bar.addWidget(self.refresh_button)
        layout.addLayout(button_bar)

        # Signals
        self.show_in_finder_button.clicked.connect(self.show_in_finder)
        self.refresh_button.clicked.connect(self.refresh_list)
        self.delete_button.clicked.connect(self.delete_selected)

    def refresh_list(self):
        self.last_hovered_item = None
        self.list_widget.clear()

        if not self.current_dir.exists():
            logger.warning(f"Directory not found: {self.current_dir}")
            self.list_widget.addItem("(Folder is missing)")
            return

        entries = [
            f for f in self.current_dir.iterdir()
            if not f.name.startswith(".") and not f.name.startswith("~$")
        ]

        if not entries:
            self.list_widget.addItem("(No files or folders yet)")
            return

        entries.sort(key=lambda x: (not x.is_dir(), x.name.lower()))
        icon_provider = QFileIconProvider()

        for entry in entries:
            item = QListWidgetItem(entry.name)
            item.setData(Qt.UserRole, entry)

            item.setIcon(icon_provider.icon(QFileInfo(str(entry))))

            font = item.font()
            if entry.is_dir():
                font.setBold(True)
                item.setForeground(QColor("#FFD700"))  # Yellow
            item.setFont(font)

            self.list_widget.addItem(item)

        self.header.setText(self.current_dir.name)


    def selected_file_path(self) -> Path | None:
        item = self.list_widget.currentItem()
        return item.data(Qt.UserRole) if item else None

    def open_selected(self):
        path = self.selected_file_path()
        if not path or not path.exists():
            logger.warning("No valid selection to open.")
            return

        if path.is_dir():
            self.current_dir = path
            self.refresh_list()
        else:
            try:
                subprocess.run(["open", str(path)], check=True)
                logger.info(f"Opened file: {path}")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to open file (subprocess error): {e}")
            except Exception as e:
                logger.error(f"Unexpected error opening file: {e}")

    def show_in_finder(self):
        path = self.selected_file_path()
        if path and path.exists():
            subprocess.run(["open", "-R", str(path)])
            logger.info(f"Revealed in Finder: {path}")
        else:
            logger.warning("No valid file to reveal.")

    def delete_selected(self):
        path = self.selected_file_path()
        if not path or not path.exists():
            logger.warning("No valid selection to delete.")
            return

        try:
            send2trash(str(path))
            logger.info(f"Moved to Trash: {path}")
        except Exception as e:
            logger.error(f"Failed to move to Trash: {path} - {e}")
        finally:
            self.refresh_list()

    def go_back(self):
        base_dirs = [self.originals_dir, self.exports_dir]
        parent = self.current_dir.parent.resolve()

        if any(parent == base or str(parent).startswith(str(base)) for base in base_dirs):
            self.current_dir = parent
            self.refresh_list()

    def show_originals(self):
        self.current_dir = self.originals_dir
        self.refresh_list()

    def show_exports(self):
        self.current_dir = self.exports_dir
        self.refresh_list()

    def preview_item(self, item):
        try:
            path = item.data(Qt.UserRole)
            if not path or not path.exists():
                return

            self.last_hovered_item = item
            self.preview_box.preview_path(path)

            cursor_pos = QCursor.pos()
            screen = self.screen().availableGeometry()
            box_size = self.preview_box.sizeHint()
            offset = 20

            x = min(cursor_pos.x() + offset, screen.right() - box_size.width() - offset)
            y = min(cursor_pos.y() + offset, screen.bottom() - box_size.height() - offset)

            self.preview_box.show_at(QPoint(x, y))

        except RuntimeError as e:
            logger.warning(f"Preview popup failed: {e}")

    def handle_external_drop(self, drop_info):
        target_dir, dropped_paths = drop_info

        for path_str in dropped_paths:
            path = Path(path_str)
            dest = target_dir / path.name

            if dest.exists():
                if not confirm_overwrite(self, dest):
                    continue

            try:
                if path.is_file():
                    shutil.copy2(path, dest)
                elif path.is_dir():
                    shutil.copytree(path, dest, dirs_exist_ok=True)
                logger.info(f"Copied {path} → {dest}")
            except Exception as e:
                logger.error(f"Failed to copy {path} to {dest}: {e}")

        self.refresh_list()

    def handle_paste(self):
        clipboard = QGuiApplication.clipboard()
        mime = clipboard.mimeData()

        if not mime.hasUrls():
            show_info(self, "Nothing to Paste", "The clipboard doesn't contain valid file paths.")
            return

        paths = [Path(url.toLocalFile()) for url in mime.urls()]
        logger.info(f"Pasting {len(paths)} item(s) into: {self.current_dir}")

        for src in paths:
            if not src.exists():
                logger.warning(f"Skipped non-existent path: {src}")
                continue

            dest = self.current_dir / src.name
            if dest.exists() and not confirm_overwrite(self, dest):
                continue

            try:
                if src.is_file():
                    shutil.copy2(src, dest)
                elif src.is_dir():
                    shutil.copytree(src, dest, dirs_exist_ok=True)
                logger.info(f"Pasted: {src.name}")
            except Exception as e:
                logger.error(f"Failed to paste {src} → {dest}: {e}")

        self.refresh_list()