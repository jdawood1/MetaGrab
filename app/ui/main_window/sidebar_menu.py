from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon

from app.core.resource_path import resource_path

class SidebarMenu(QWidget):
    """Left sidebar menu for navigation."""

    browser_clicked = Signal()
    downloads_clicked = Signal()
    audio_editor_clicked = Signal()
    video_studio_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(220)
        self.setObjectName("SidebarMenu")

        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignTop)
        self.layout.setContentsMargins(12, 12, 12, 12)
        self.layout.setSpacing(6)

        self.buttons = []

        self.layout.addWidget(self.create_section_label("Library"))

        self.browser_btn = self.create_button("Folders", "folders.svg")
        self.downloads_btn = self.create_button("Downloads", "downloads.svg")
        self.audio_editor_btn = self.create_button("Audio Editor", "audio.svg")
        self.video_studio_btn = self.create_button("Video Studio", "video.svg")

        for btn in [
            self.browser_btn,
            self.downloads_btn,
            self.audio_editor_btn,
            self.video_studio_btn,
        ]:
            self.layout.addWidget(btn)
            self.buttons.append(btn)

        self.browser_btn.clicked.connect(lambda: self.activate_button(self.browser_btn, self.browser_clicked))
        self.downloads_btn.clicked.connect(lambda: self.activate_button(self.downloads_btn, self.downloads_clicked))
        self.audio_editor_btn.clicked.connect(lambda: self.activate_button(self.audio_editor_btn, self.audio_editor_clicked))
        self.video_studio_btn.clicked.connect(lambda: self.activate_button(self.video_studio_btn, self.video_studio_clicked))

        self.activate_button(self.browser_btn, self.browser_clicked)

    def create_button(self, text: str, icon_filename: str) -> QPushButton:
        try:
            icon_path = resource_path(f"assets/icons/{icon_filename}")
        except Exception:
            icon_path = ""
        button = QPushButton(text)
        button.setIcon(QIcon(icon_path))
        button.setIconSize(QSize(20, 20))
        button.setCursor(Qt.PointingHandCursor)
        button.setMinimumHeight(44)
        return button

    def create_section_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setAlignment(Qt.AlignLeft)
        return label

    def activate_button(self, selected_button, signal):
        for btn in self.buttons:
            btn.setProperty("selected", btn is selected_button)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        signal.emit()