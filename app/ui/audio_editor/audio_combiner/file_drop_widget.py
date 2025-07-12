from PySide6.QtWidgets import QLabel, QFileDialog, QPushButton
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QMouseEvent, QCursor
from PySide6.QtCore import Qt, QEvent


class FileDropWidget(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("FileDropWidget")

        self.setAcceptDrops(True)
        self.setFixedSize(175, 125)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setAlignment(Qt.AlignCenter)
        self.setWordWrap(True)
        self.setText("Drop or Click to Select File")
        self.file_path = ""
        self.file_changed_callback = None  # Optional external callback

        # Remove button (optional enhancement)
        self.remove_button = QPushButton("X", self)
        self.remove_button.setObjectName("FileDropRemoveButton")

        self.remove_button.setFixedSize(18, 18)
        self.remove_button.move(self.width() - 22, 4)
        self.remove_button.clicked.connect(self._on_remove_clicked)
        self.remove_button.hide()

        # Track hover state to show remove button
        self.installEventFilter(self)

        self.setStyleSheet("""
            QLabel#FileDropWidget {
                border: 2px dashed #888;
                background-color: #222;
                color: #aaa;
                border-radius: 10px;
            }
        
            QLabel#FileDropWidget[hovering="true"] {
                border: 2px dashed #58a6ff;
                background-color: #2a2a2a;
            }
        
            QLabel#FileDropWidget[dragging="true"] {
                border: 2px solid #66ff66;
                background-color: #1e1e1e;
            }
        """)


    def eventFilter(self, obj, event):
        if event.type() == QEvent.Enter:
            self.setProperty("hovering", True)
            self._refresh_style()
            self.remove_button.show()
        elif event.type() == QEvent.Leave:
            self.setProperty("hovering", False)
            self._refresh_style()
            self.remove_button.hide()
        return super().eventFilter(obj, event)

    def _refresh_style(self):
        self.style().unpolish(self)
        self.style().polish(self)

    def _on_remove_clicked(self):
        self.reset()
        if self.file_changed_callback:
            self.file_changed_callback()

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            self.setProperty("dragging", True)
            self.style().unpolish(self)
            self.style().polish(self)
            event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self._reset_style()


    def dropEvent(self, event: QDropEvent):
        self._reset_style()
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith(('.mp3', '.wav', '.flac', '.m4a', '.aac', '.opus')):
                self.set_file(path)
                break

    def mousePressEvent(self, event: QMouseEvent):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Audio File", "", "Audio Files (*.mp3 *.wav *.flac *.m4a *.aac *.opus)"
        )
        if path:
            self.set_file(path)

    def set_file(self, path: str):
        if path == self.file_path:
            return
        self.file_path = path
        self.setText(path.split("/")[-1])
        if self.file_changed_callback:
            self.file_changed_callback()

    def reset(self):
        self.file_path = ""
        self.setText("Drop or Click to Select File")
        self.show()  # Re-show in case it was hidden
        if self.file_changed_callback:
            self.file_changed_callback()

    def has_file(self) -> bool:
        return bool(self.file_path)

    def _reset_style(self):
        self.setProperty("dragging", False)
        self.style().unpolish(self)
        self.style().polish(self)