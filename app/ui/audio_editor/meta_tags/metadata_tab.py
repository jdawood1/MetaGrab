import os

import mutagen.id3
from PySide6.QtCore import Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.ui.audio_editor.meta_tags.components.img_cover_widget import CoverDropWidget
from app.ui.audio_editor.meta_tags.components.metadata_embedder import MetadataEmbedder
from app.ui.audio_editor.meta_tags.components.metadata_form_widget import MetadataFormWidget
from app.ui.audio_editor.meta_tags.components.text_drop_tooltip import MetadataHelpWidget
from app.ui.audio_editor.meta_tags.components.text_drop_widget import MetadataTextDropWidget


class MetadataTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("MetadataTab")
        self.audio_file_path = ""
        self.has_embedded_cover = False
        self.setAcceptDrops(True)
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(24)
        main_layout.setContentsMargins(30, 20, 30, 20)

        # Note about supported format
        note = QLabel("Drag and drop a .mp3 file anywhere in this panel.")
        note.setStyleSheet("color: #888; font-style: italic;")
        note.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(note)

        # --- Upper Section: Cover + Metadata Form ---
        top_container = QHBoxLayout()

        # Cover Art
        self.cover_widget = CoverDropWidget(self)
        cover_box = QGroupBox("Cover Art")
        cover_layout = QVBoxLayout(cover_box)
        cover_layout.addWidget(self.cover_widget, alignment=Qt.AlignCenter)
        top_container.addWidget(cover_box, 1)

        # Metadata Form + Text Drop + Help
        self.metadata_form = MetadataFormWidget(self)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        inner_container = QWidget()
        inner_layout = QVBoxLayout(inner_container)
        inner_layout.setSpacing(12)

        # Add metadata form
        inner_layout.addWidget(self.metadata_form)

        # Drag-and-drop widget with attached help icon
        text_help_container = QWidget()
        text_help_layout = QHBoxLayout(text_help_container)
        text_help_layout.setContentsMargins(0, 0, 0, 0)
        text_help_layout.setSpacing(6)
        text_help_layout.setAlignment(Qt.AlignCenter)

        self.text_drop_widget = MetadataTextDropWidget(self.metadata_form)
        self.help_widget = MetadataHelpWidget()
        self.help_widget.setFixedSize(24, 24)

        text_help_layout.addWidget(self.text_drop_widget)
        text_help_layout.addWidget(self.help_widget)
        inner_layout.addWidget(text_help_container)

        scroll_area.setWidget(inner_container)

        form_box = QGroupBox("Metadata")
        form_box_layout = QVBoxLayout(form_box)
        form_box_layout.addWidget(scroll_area)

        top_container.addWidget(form_box, 2)
        main_layout.addLayout(top_container)

        # --- Lower Section: File Info + Embed Button ---
        bottom_container = QHBoxLayout()
        bottom_container.setSpacing(12)

        self.file_label = QPushButton("Audio File: (not selected)")
        self.file_label.setObjectName("FileLabelButton")
        self.file_label.setProperty("hasFile", False)
        self.file_label.setStyleSheet("""
            QPushButton#FileLabelButton[hasFile="false"] {
                color: #ffffff;
                background-color: transparent;
                border: none;
            }
            QPushButton#FileLabelButton[hasFile="true"] {
                color: #6edc90;
                text-decoration: underline;
                background-color: transparent;
                border: none;
            }

            QPushButton#FileLabelButton:hover {
                color: #90caf9;
                text-decoration: underline;
            }
        """)

        self.file_label.setCursor(Qt.PointingHandCursor)
        self.file_label.mousePressEvent = self.choose_audio

        self.process_button = QPushButton("Embed Metadata")
        self.process_button.setFixedWidth(160)
        self.process_button.clicked.connect(self.process_metadata)

        bottom_container.addWidget(self.file_label)
        bottom_container.addStretch()
        bottom_container.addWidget(self.process_button)
        main_layout.addLayout(bottom_container)

    def choose_audio(self, event=None):
        path, _ = QFileDialog.getOpenFileName(self, "Select Audio File", "", "MP3 Files (*.mp3)")
        if path:
            self.load_audio_from_path(path)

    def load_audio_from_path(self, path):
        if not path.lower().endswith(".mp3"):
            QMessageBox.warning(self, "Invalid Format", "Only MP3 files are supported.")
            return

        self.audio_file_path = path
        self.file_label.setText(f"Audio File: {path}")
        self.file_label.setProperty("hasFile", True)
        self.file_label.style().unpolish(self.file_label)
        self.file_label.style().polish(self.file_label)
        self.has_embedded_cover = False
        self.text_drop_widget.reset()

        success = self.metadata_form.load_from_file(path)
        if not success:
            QMessageBox.information(self, "No Metadata", "This file has no metadata to import.")

        try:
            tags = mutagen.id3.ID3(path)
            for tag in tags.values():
                if isinstance(tag, mutagen.id3.APIC):
                    pixmap = QPixmap()
                    if pixmap.loadFromData(tag.data):
                        self.cover_widget.set_pixmap(pixmap)
                        self.has_embedded_cover = True
                    break
            else:
                QMessageBox.information(self, "No Cover Art", "No embedded cover was found.")
        except Exception as e:
            print(f"MetadataTab: Failed to load cover image: {e}")

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if os.path.isfile(path) and path.lower().endswith(".mp3"):
                self.load_audio_from_path(path)
                return

    def process_metadata(self):
        metadata = self.metadata_form.get_metadata()
        title = metadata.get("title", "").strip()

        if not self.audio_file_path:
            QMessageBox.warning(self, "Missing Input", "Please select an audio file first.")
            return

        if not title:
            QMessageBox.warning(
                self, "Missing Title", "Please enter a title before embedding metadata."
            )
            return

        cover_path = self.cover_widget.cover_path or None
        try:
            embedder = MetadataEmbedder(cover_path)
        except Exception as e:
            QMessageBox.warning(self, "Cover Art Error", str(e))
            return

        success = embedder.embed_metadata(file_path=self.audio_file_path, **metadata)

        if success:
            QMessageBox.information(self, "Success", "Metadata successfully embedded.")
            self.audio_file_path = ""
            self.file_label.setText("Audio File: (not selected)")
            self.file_label.setProperty("hasFile", False)
            self.file_label.style().unpolish(self.file_label)
            self.file_label.style().polish(self.file_label)

        else:
            QMessageBox.critical(self, "Failure", "Failed to embed metadata.")
