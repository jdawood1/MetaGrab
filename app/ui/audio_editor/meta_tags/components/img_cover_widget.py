from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QCursor, QDragEnterEvent, QDropEvent, QMouseEvent, QPixmap
from PySide6.QtWidgets import QFileDialog, QLabel, QPushButton


class CoverDropWidget(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CoverDropWidget")

        self.setAcceptDrops(True)
        self.setFixedSize(200, 200)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setAlignment(Qt.AlignCenter)
        self.setText("Drop or Click to Add Cover")
        self.cover_path = ""

        self.installEventFilter(self)

        # Clear ("X") button
        self.clear_button = QPushButton("X", self)
        self.clear_button.setObjectName("CoverClearButton")
        self.clear_button.hide()
        self.clear_button.setStyleSheet("""
            QPushButton#CoverClearButton {
                background-color: transparent;
                color: #aaa;
                border: none;
                padding: 0;
            }
            QPushButton#CoverClearButton:hover {
                color: red;
                background-color: transparent;
            }
        """)

        self.clear_button.setFixedSize(20, 20)
        self.clear_button.move(self.width() - 24, 4)
        self.clear_button.clicked.connect(self.reset)
        self.setStyleSheet("""
            QLabel#CoverDropWidget {
                border: 2px dashed #888;
                background-color: #222;
                color: #aaa;
                border-radius: 10px;
            }
        
            QLabel#CoverDropWidget[hovering="true"] {
                border: 2px dashed #58a6ff;
                background-color: #2a2a2a;
            }
        
            QLabel#CoverDropWidget[dragging="true"] {
                border: 2px solid #66ff66;
                background-color: #1e1e1e;
            }
        """)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.clear_button.move(self.width() - 24, 4)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Enter:
            self.setProperty("hovering", True)
            self._refresh_style()
            self.clear_button.show()
        elif event.type() == QEvent.Leave:
            self.setProperty("hovering", False)
            self._refresh_style()
            self.clear_button.hide()
        return super().eventFilter(obj, event)

    def _refresh_style(self):
        self.style().unpolish(self)
        self.style().polish(self)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            self.setProperty("dragging", True)
            self._refresh_style()
            event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self.setProperty("dragging", False)
        self._refresh_style()

    def dropEvent(self, event: QDropEvent):
        self.setProperty("dragging", False)
        self._refresh_style()
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                self.set_cover(path)
                break

    def mousePressEvent(self, event: QMouseEvent):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Cover Image", "", "Images (*.jpg *.jpeg *.png)"
        )
        if path:
            self.set_cover(path)

    def set_cover(self, path: str):
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            self.setPixmap(pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.setText("")
            self.cover_path = path

    def set_pixmap(self, pixmap: QPixmap):
        if not pixmap.isNull():
            self.setPixmap(pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.setText("")
            self.cover_path = ""

    def reset(self):
        self.setPixmap(QPixmap())
        self.cover_path = ""
        self.setText("Drop or Click to Add Cover")
