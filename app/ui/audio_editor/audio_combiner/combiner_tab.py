from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QLineEdit, QProgressBar
)
from pathlib import Path
from app.core.logger import logger
from app.ui.audio_editor.audio_combiner.combine_audio import CombineWorker
from app.ui.audio_editor.audio_combiner.file_drop_container import FileDropContainer
from app.ui.audio_editor.audio_combiner.audio_preview_widget import AudioPreviewWidget


class CombineAudioTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("CombineAudioTab")
        self.worker = None
        self.user_modified_output = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.addStretch(1)

        # File input area
        self.file_drop_container = FileDropContainer()
        self.file_drop_container.files_updated.connect(self._on_files_updated)
        layout.addWidget(self.file_drop_container)

        # Output path selection row
        output_row = QHBoxLayout()
        self.output_path = QLineEdit()
        self.output_path.setPlaceholderText("Save combined file as...")
        self.output_path.textEdited.connect(self._mark_output_as_user_modified)

        save_btn = QPushButton("Save As")
        save_btn.clicked.connect(self.browse_output_file)

        output_row.addWidget(self.output_path)
        output_row.addWidget(save_btn)
        layout.addStretch(1)
        layout.addLayout(output_row)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Combine button
        self.combine_btn = QPushButton("Combine Audio")
        self.combine_btn.clicked.connect(self.combine_audio)
        layout.addWidget(self.combine_btn)

        # Preview widget for live audio
        self.preview_widget = AudioPreviewWidget()
        layout.addWidget(self.preview_widget)
        layout.addStretch(1)

    def _mark_output_as_user_modified(self):
        self.user_modified_output = True

    def _on_files_updated(self):
        files = self.file_drop_container.get_file_paths()

        if not files:
            self.preview_widget.clear_preview()
            return

        # Set the default output path if not manually changed
        if not self.user_modified_output:
            first_file = Path(files[0])
            default_output = first_file.parent / f"{first_file.stem}_combined.mp3"
            self.output_path.setText(str(default_output))
            self.user_modified_output = False

        # Set a live preview
        self.preview_widget.set_preview_files(files)

    def browse_output_file(self):
        initial_dir = str(Path(self.output_path.text()).parent) if self.output_path.text().strip() else ""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save As", initial_dir, "MP3 Files (*.mp3)"
        )
        if file_path:
            if not file_path.lower().endswith(".mp3"):
                file_path += ".mp3"
            self.output_path.setText(file_path)
            self.user_modified_output = True

    def combine_audio(self):
        file_list = self.file_drop_container.get_file_paths()
        output_path = self.output_path.text().strip()

        if len(file_list) < 2:
            logger.error("Please add at least two audio files.")
            return

        if not output_path:
            logger.error("Please specify an output path.")
            return

        logger.info("[Starting combine process...")
        self.combine_btn.setVisible(False)
        self.progress_bar.setVisible(True)

        self.worker = CombineWorker(file_list, output_path)
        self.worker.finished.connect(self.handle_combine_finished)
        self.worker.start()

    def handle_combine_finished(self, success: bool, output_path: str):
        self.progress_bar.setVisible(False)
        self.combine_btn.setVisible(True)

        if success:
            logger.info(f"Combined file saved to: {output_path}")
            # Optional: switch preview to a final file
            self.preview_widget.set_audio_file(output_path)
        else:
            logger.error("Failed to combine audio files.")