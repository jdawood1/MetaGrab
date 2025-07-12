from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QLineEdit, QPushButton,
    QFileDialog, QGroupBox, QCheckBox, QMessageBox, QComboBox,
    QStackedLayout, QProgressBar, QScrollArea
)
from PySide6.QtGui import QDragEnterEvent, QDropEvent

from app.ui.audio_editor.editing_tools.audio_presets import AudioNormalizePresets, AudioFormatPresets, parse_time_input
from app.ui.audio_editor.editing_tools.audio_workers import UnifiedProcessWorker


class EditingToolsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("EditingToolsTab")
        self.input_path = ""
        self.output_path = ""
        self.setAcceptDrops(True)
        self._setup_ui()

    def _setup_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)

        container = QWidget()
        scroll.setWidget(container)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(24)

        # File selector
        layout.addWidget(self._build_file_groupbox())

        # Crop section
        self.crop_checkbox = QCheckBox("Apply Crop")
        self.crop_start = QLineEdit()
        self.crop_end = QLineEdit()
        self.crop_start.setPlaceholderText("Start (e.g. 1:20, 2m10s, 75)")
        self.crop_end.setPlaceholderText("End (optional)")
        layout.addWidget(self._build_option_section("", self.crop_checkbox, [self.crop_start, self.crop_end]))

        # Normalize section
        self.normalize_checkbox = QCheckBox("Apply Normalize")
        self.normalize_preset_dropdown = QComboBox()

        for key, label in AudioNormalizePresets.PRESET_LABELS.items():
            self.normalize_preset_dropdown.addItem(label, userData=key)
            index = self.normalize_preset_dropdown.count() - 1

            preset = AudioNormalizePresets.PRESETS.get(key)
            if preset:
                tooltip = f"Loudness: {preset['I']} LUFS\nTrue Peak: {preset['TP']} dB\nLRA: {preset['LRA']} LU"
                self.normalize_preset_dropdown.setItemData(index, tooltip, role=Qt.ToolTipRole)

        layout.addWidget(self._build_option_section("", self.normalize_checkbox, [self.normalize_preset_dropdown]))

        # Convert section
        self.convert_checkbox = QCheckBox("Apply Convert")
        self.convert_format = QComboBox()
        self.convert_bitrate = QLineEdit()
        self.convert_channels = QLineEdit()
        self.convert_bitrate.setPlaceholderText("Bitrate (e.g., 192k)")
        self.convert_channels.setPlaceholderText("Channels (1 or 2)")

        for fmt in AudioFormatPresets.FORMATS:
            self.convert_format.addItem(fmt.upper(), fmt)

        layout.addWidget(self._build_option_section("", self.convert_checkbox, [self.convert_format, self.convert_bitrate, self.convert_channels]))

        for combo in (self.normalize_preset_dropdown, self.convert_format):
            combo.wheelEvent = lambda event, s=scroll: s.wheelEvent(event)

        # Process button + loader
        self.process_button = QPushButton("Process Selected Actions")
        self.process_button.setFixedHeight(36)
        self.process_button.clicked.connect(self.process_all)

        self.loader = QProgressBar()
        self.loader.setRange(0, 0)
        self.loader.setFixedHeight(24)
        self.loader.setVisible(False)

        self.stack_layout = QStackedLayout()
        self.stack_layout.addWidget(self.process_button)
        self.stack_layout.addWidget(self.loader)
        layout.addLayout(self.stack_layout)

        # Add scroll area to the main layout
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)

    def _build_file_groupbox(self) -> QGroupBox:
        box = QGroupBox("")
        layout = QVBoxLayout(box)
        layout.setSpacing(10)
        layout.addLayout(self._file_selector_row("Input File:", is_input=True))
        layout.addLayout(self._file_selector_row("Output File:", is_input=False))
        return box

    def _file_selector_row(self, label: str, is_input: bool) -> QHBoxLayout:
        row = QHBoxLayout()
        field = QLineEdit()
        field.setPlaceholderText("Drag or browse for audio file..." if is_input else "Set output path...")
        button = QPushButton("Browse")

        def browse():
            if is_input:
                path, _ = QFileDialog.getOpenFileName(self, "Select Input Audio", "", "Audio Files (*.mp3 *.wav *.flac *.m4a *.aac *.opus)")
                if path:
                    field.setText(path)
                    self.input_path = path
                    input_name = Path(path).stem
                    default_output = str(Path(path).with_name(f"{input_name}_converted.mp3"))
                    self.output_path = default_output
                    self.output_field.setText(default_output)
            else:
                path, _ = QFileDialog.getSaveFileName(self, "Save Output Audio", "", "Audio Files (*.mp3 *.flac *.aac *.wav *.ogg)")
                if path:
                    field.setText(path)
                    self.output_path = path

        button.clicked.connect(browse)
        row.addWidget(QLabel(label))
        row.addWidget(field)
        row.addWidget(button)

        if is_input:
            self.input_field = field
        else:
            self.output_field = field

        return row

    def _build_option_section(self, title: str, checkbox: QCheckBox, inputs: list) -> QGroupBox:
        group = QGroupBox(title)
        layout = QVBoxLayout(group)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(6)
        layout.addWidget(checkbox)
        for widget in inputs:
            layout.addWidget(widget)
        return group

    def _show_loader(self):
        self.process_button.setEnabled(False)
        self.loader.setVisible(True)
        self.stack_layout.setCurrentWidget(self.loader)

    def _hide_loader(self):
        self.loader.setVisible(False)
        self.process_button.setEnabled(True)
        self.stack_layout.setCurrentWidget(self.process_button)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith((".mp3", ".wav", ".flac", ".m4a", ".aac", ".opus", ".webm")):
                self.input_path = path
                self.input_field.setText(path)
                input_name = Path(path).stem
                default_output = str(Path(path).with_name(f"{input_name}_converted.mp3"))
                self.output_path = default_output
                self.output_field.setText(default_output)
                break

    def process_all(self):
        if not self.input_path or not self.output_path:
            QMessageBox.warning(self, "Missing Paths", "Please set both input and output paths.")
            return

        if not (
                self.crop_checkbox.isChecked() or
                self.normalize_checkbox.isChecked() or
                self.convert_checkbox.isChecked()
        ):
            QMessageBox.information(
                self,
                "No Actions Selected",
                "Please select at least one processing option (Crop, Normalize, or Convert)."
            )
            return

        crop_start = crop_end = None
        if self.crop_checkbox.isChecked():
            try:
                crop_start = parse_time_input(self.crop_start.text() or "0")
                crop_end = parse_time_input(self.crop_end.text()) if self.crop_end.text() else None
            except ValueError:
                QMessageBox.warning(
                    self,
                    "Invalid Input",
                    "Start/End time is invalid.\nExamples: 90, 1:30, 2m10s, 1h 2m"
                )
                return

        normalize_filter = None
        if self.normalize_checkbox.isChecked():
            key = self.normalize_preset_dropdown.currentData()
            normalize_filter = AudioNormalizePresets.get_preset_filter(key)
            if not normalize_filter:
                QMessageBox.warning(self, "Invalid Preset", "Please select a valid normalization preset.")
                return

        codec = "libmp3lame"
        bitrate = "192k"
        channels = 2

        if self.convert_checkbox.isChecked():
            fmt = self.convert_format.currentData()
            path_obj = Path(self.output_path)
            if path_obj.suffix.lower() != f".{fmt}":
                self.output_path = str(path_obj.with_suffix(f".{fmt}"))
                self.output_field.setText(self.output_path)

            codec = AudioFormatPresets.CODEC_MAP.get(fmt, "libmp3lame")
            bitrate = self.convert_bitrate.text().strip() or "192k"
            if not bitrate.endswith("k"):
                bitrate += "k"

            try:
                channels_input = self.convert_channels.text().strip()
                channels = int(channels_input) if channels_input else 2
                if channels not in (1, 2):
                    raise ValueError
            except ValueError:
                QMessageBox.warning(self, "Invalid Channels", "Channels must be 1 or 2.")
                return

        else:
            # Ensure the default output ends with .mp3 if convert is not checked
            path_obj = Path(self.output_path)
            if path_obj.suffix.lower() != ".mp3":
                self.output_path = str(path_obj.with_suffix(".mp3"))
                self.output_field.setText(self.output_path)

        # Confirm overwriting if a file already exists
        if Path(self.output_path).exists():
            reply = QMessageBox.question(
                self,
                "File Exists",
                f"The file:\n\n{self.output_path}\n\nalready exists. Overwrite it?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        self._show_loader()
        self.process_worker = UnifiedProcessWorker(
            input_path=self.input_path,
            output_path=self.output_path,
            crop_start=crop_start,
            crop_end=crop_end,
            normalize_filter=normalize_filter,
            codec=codec,
            bitrate=bitrate,
            channels=channels
        )
        self.process_worker.finished.connect(lambda success, _: (
            self._hide_loader(),
            QMessageBox.information(
                self,
                "Done",
                "Audio processing complete." if success else "Audio processing failed."
            )
        ))
        self.process_worker.start()