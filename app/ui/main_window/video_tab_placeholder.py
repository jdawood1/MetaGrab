from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QFont
from app.core.resource_path import resource_path

class VideoStudioPlaceholder(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("VideoStudioPlaceholder")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        try:
            icon_path = resource_path("assets/icons/edit_video.svg")
            pixmap = QPixmap(icon_path).scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon = QLabel()
            icon.setPixmap(pixmap)
            icon.setAlignment(Qt.AlignCenter)
            layout.addWidget(icon)
        except Exception:
            # Fail silently
            pass

        # Main label
        title = QLabel("Video Studio Coming Soon")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Subtext
        subtitle = QLabel("This section will allow you to edit, trim, and enhance video files.")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #BBBBBB; margin-top: 4px;")
        layout.addWidget(subtitle)

        self.setStyleSheet("""
            #VideoStudioPlaceholder {
                background-color: #181818;
                color: #E0E0E0;
            }
            QLabel {
                font-size: 14px;
            }
        """)