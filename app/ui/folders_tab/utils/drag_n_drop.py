import shutil
from pathlib import Path

from PySide6.QtCore import QFileInfo, QMimeData, Qt, QUrl, Signal
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import QFileIconProvider, QListWidget, QPushButton

from app.core.logger import logger
from app.ui.dialog_box_builder import confirm_overwrite


class DropTargetButton(QPushButton):
    """A QPushButton that accepts the file drops and emits a signal."""

    fileDropped = Signal(object)  # emits (folder_path, [dropped_file_paths])

    def __init__(self, label: str, folder_path, parent=None):
        super().__init__(label, parent)
        self.folder_path = folder_path
        self.setAcceptDrops(True)
        self.setCursor(Qt.PointingHandCursor)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        event.accept()

    def dropEvent(self, event):
        paths = [url.toLocalFile() for url in event.mimeData().urls()]
        self.fileDropped.emit((self.folder_path, paths))
        event.acceptProposedAction()


class FileListWidget(QListWidget):
    """Custom QListWidget to handle drag-and-drop and right-click preview."""

    def __init__(self, parent_window):
        super().__init__()
        self.parent_window = parent_window
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if not urls:
            return

        for url in urls:
            source_path = Path(url.toLocalFile())
            dest_path = self.parent_window.current_dir / source_path.name

            try:
                if source_path.resolve() == dest_path.resolve():
                    continue

                if dest_path.exists():
                    if not confirm_overwrite(self, dest_path):
                        continue

                if source_path.is_file():
                    shutil.copy2(source_path, dest_path)
                elif source_path.is_dir():
                    shutil.copytree(source_path, dest_path, dirs_exist_ok=True)

            except Exception as e:
                logger.error(f"Failed to copy {source_path}: {e}")

        self.parent_window.refresh_list()

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if not item:
            return

        selected_path = self.parent_window.selected_file_path()
        if selected_path and selected_path.exists():
            mime = QMimeData()
            mime.setUrls([QUrl.fromLocalFile(str(selected_path))])

            drag = QDrag(self)
            drag.setMimeData(mime)

            # Get native icon for drag visual
            icon_provider = QFileIconProvider()
            icon = icon_provider.icon(QFileInfo(str(selected_path)))
            pixmap = icon.pixmap(64, 64)
            drag.setPixmap(pixmap)
            drag.setHotSpot(pixmap.rect().center())

            drag.exec(Qt.CopyAction)
