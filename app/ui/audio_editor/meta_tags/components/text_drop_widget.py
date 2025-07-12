import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFileDialog
from PySide6.QtCore import Qt


class MetadataTextDropWidget(QWidget):
    def __init__(self, metadata_form_widget, parent=None):
        super().__init__(parent)
        self.setObjectName("MetadataDropWidget")
        self.setAcceptDrops(True)
        self.metadata_form = metadata_form_widget
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        self.label = QLabel("Drop or Click to Load Metadata (.txt)")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("color: #AAAAAA; font-style: italic; padding: 10px;")

        layout.addWidget(self.label)
        self.setStyleSheet("border: 2px dashed #666; border-radius: 10px;")
        self.setMinimumHeight(100)
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            path, _ = QFileDialog.getOpenFileName(self, "Select Metadata File", "", "Text Files (*.txt)")
            if path:
                self.apply_metadata_from_txt(path)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].toLocalFile().lower().endswith('.txt'):
                event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if not urls:
            return

        txt_path = urls[0].toLocalFile()
        if os.path.isfile(txt_path):
            self.apply_metadata_from_txt(txt_path)

    def apply_metadata_from_txt(self, path: str):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            parsed = self.parse_metadata_text(content)
            self.metadata_form.set_metadata(parsed)

            self.label.setText("Metadata loaded from file")
        except Exception as e:
            self.label.setText(f"Failed to read metadata: {e}")

    def reset(self):
        self.label.setText("Drop or Click to Load Metadata (.txt)")

    def parse_metadata_text(self, text: str) -> dict:
        metadata = {}
        lines = text.splitlines()
        known_keys = {
            'title', 'artist', 'album', 'album artist', 'genre', 'year',
            'track', 'composer', 'comment', 'explicit', 'bpm', 'lyrics'
        }

        i = 0
        while i < len(lines):
            line = lines[i]
            if ':' not in line:
                i += 1
                continue

            key, value = line.split(':', 1)
            key = key.strip().lower()
            value = value.strip()

            if key == 'lyrics':
                lyrics_lines = [value]
                i += 1
                while i < len(lines):
                    lyrics_lines.append(lines[i].rstrip())
                    i += 1
                metadata['lyrics'] = '\n'.join(lyrics_lines)
                break  # Lyrics is last
            elif key in known_keys:
                mapped_key = {
                    'album artist': 'album_artist',
                    'track': 'track_number'
                }.get(key, key)
                metadata[mapped_key] = value
            i += 1

        return metadata
