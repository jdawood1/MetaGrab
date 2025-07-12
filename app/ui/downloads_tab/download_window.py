from urllib.parse import urlparse, parse_qs

from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QListWidget, QProgressBar, QSizePolicy,
    QComboBox, QCheckBox, QMessageBox
)
from PySide6.QtCore import Qt, QTimer, QThreadPool, QVariantAnimation
from app.core import settings
from app.core.logger import logger
from app.systems.download_system.download_worker import DownloadWorker
from app.ui.downloads_tab.download_menu import DownloadContextMenu
from app.ui.downloads_tab.lufs_worker import LUFSWorker
from app.ui.downloads_tab.task_tracker import DownloadTaskTracker


def clean_youtube_url(url: str) -> str:
    try:
        parsed = urlparse(url)
        if "youtube.com" in parsed.netloc or "youtu.be" in parsed.netloc:
            query = parse_qs(parsed.query)
            video_id = query.get("v", [None])[0]
            if video_id:
                return f"https://{parsed.netloc}/watch?v={video_id}"
            elif parsed.netloc == "youtu.be" and parsed.path:
                return f"https://youtu.be{parsed.path}"
    except Exception as e:
        print(f"[YouTube Clean Error] Failed to clean URL: {url}\n{e}")
    return url


def _on_normalize_changed(state):
    settings.NORMALIZE_AUDIO = bool(state)

def _on_strip_metadata_changed(state):
    settings.STRIP_METADATA = bool(state)


class DownloadsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("DownloaderWindow")
        self.thread_pool = QThreadPool(self)
        self.active_worker = None
        self._setup_ui()
        self._connect_signals()

        self._analyze_anim = None
        self._analyze_base_style = ""

        self.task_tracker = DownloadTaskTracker("downloads", self.list_widget)
        self.context_menu = DownloadContextMenu(self.list_widget, self.task_tracker)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.context_menu.show)

    def _setup_ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 24, 24, 24)

        self.title = QLabel("Download Manager")
        self.title.setAlignment(Qt.AlignLeft)
        self.title.setObjectName("Title")
        layout.addWidget(self.title)

        input_row = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter a download URL... (tip: use incognito mode, no sign-in)")
        self.url_input.returnPressed.connect(self.handle_download_clicked)
        self.url_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.download_button = QPushButton("Download")
        self.download_button.setFixedWidth(100)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setObjectName("CancelButton")
        self.cancel_button.setFixedWidth(100)
        self.cancel_button.setEnabled(False)

        self.analyze_button = QPushButton("Analyze")
        self.analyze_button.setFixedSize(100, 32)
        self.analyze_button.clicked.connect(self.handle_analyze_clicked)
        input_row.addWidget(self.analyze_button)

        input_row.addWidget(self.url_input)
        input_row.addWidget(self.download_button)
        input_row.addWidget(self.cancel_button)
        layout.addLayout(input_row)

        self.format_dropdown = QComboBox()
        formats = [
            ("MP3", "Audio"),
            ("FLAC", "Audio"),
            ("MP4", "Video + Audio"),
            ("Audio Only", "Raw"),
            ("Video Only", "Raw"),
            ("MKV", "Video + Audio"),
            ("WEBM", "Video + Audio"),
            ("AVI", "Video + Audio"),
            ("MOV", "Video + Audio"),
            ("M4A", "Audio"),
            ("OPUS", "Audio"),
            ("AAC", "Audio"),
            ("WAV", "Audio"),
        ]

        for i, (label, type_) in enumerate(formats, start=1):
            self.format_dropdown.addItem(f"{i}. {label} - {type_}")

        self.format_dropdown.setCurrentIndex(0)
        layout.addWidget(self.format_dropdown)

        # Normalization & Metadata Strip Options
        options_row = QHBoxLayout()
        options_row.setSpacing(20)

        self.normalize_checkbox = QCheckBox("Normalize Audio (MP3 only)")
        self.normalize_checkbox.setChecked(settings.NORMALIZE_AUDIO)
        self.normalize_checkbox.stateChanged.connect(_on_normalize_changed)

        self.strip_metadata_checkbox = QCheckBox("Strip Metadata")
        self.strip_metadata_checkbox.setChecked(settings.STRIP_METADATA)
        self.strip_metadata_checkbox.stateChanged.connect(_on_strip_metadata_changed)

        self.clear_url_button = QPushButton("Clear")
        self.clear_url_button.clicked.connect(self.clear_url_input)
        input_row.addWidget(self.clear_url_button)

        options_row.addWidget(self.normalize_checkbox)
        options_row.addWidget(self.strip_metadata_checkbox)
        options_row.addStretch()

        layout.addLayout(options_row)

        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        layout.addWidget(self.progress)

        self.list_widget = QListWidget()
        self.list_widget.addItem("(No downloads yet)")
        layout.addWidget(self.list_widget)

        outer_layout.addWidget(container)

    def _connect_signals(self):
        self.download_button.clicked.connect(self.handle_download_clicked)
        self.cancel_button.clicked.connect(self.cancel_active_download)
        self.url_input.returnPressed.connect(self.handle_download_clicked)

    def _clear_placeholder(self):
        if self.list_widget.count() == 1 and self.list_widget.item(0).text() == "(No downloads yet)":
            self.list_widget.clear()

    def clear_url_input(self):
        self.url_input.clear()
        logger.info("URL input cleared.")

    def handle_download_clicked(self):
        url = self.url_input.text().strip()
        if not url:
            logger.warning("Download clicked with empty URL.")
            return

        cleaned_url = clean_youtube_url(url)
        format_index = self.format_dropdown.currentIndex()
        format_choice = str(format_index + 1)
        normalize = self.normalize_checkbox.isChecked()

        self._clear_placeholder()

        worker = DownloadWorker(cleaned_url, format_choice, normalize=normalize)
        task_key = self.task_tracker.register_task(cleaned_url, format_choice, worker)

        if not task_key:
            return  # Duplicate task, already registered

        self.active_worker = worker
        self.cancel_button.setEnabled(True)

        worker.status.connect(lambda _, msg: self.task_tracker.update_status(task_key, msg))
        worker.error.connect(lambda _, err: self.task_tracker.mark_failed(task_key))
        worker.finished.connect(lambda _: self.on_task_finished(task_key))
        worker.cancelled.connect(lambda _: self.handle_worker_cancelled(task_key))
        worker.progress.connect(self.update_progress)
        worker.start()

        self.url_input.clear()
        self.list_widget.scrollToBottom()

    def cancel_active_download(self):
        if self.active_worker:
            self.active_worker.stop()  # Signal emitted from within
            logger.info("Cancellation signal sent to worker.")
            self.cancel_button.setEnabled(False)
            self.progress.setValue(0)

    def handle_worker_cancelled(self, task_key):
        self.task_tracker.mark_cancelled(task_key)
        self.cancel_button.setEnabled(False)
        self.progress.setValue(0)
        self.active_worker = None

    def update_progress(self, data):
        try:
            percent = float(data.get('_percent_str', '0').replace('%', '').strip())
            self.progress.setValue(int(percent))
        except Exception:
            pass

    def on_task_finished(self, task_key):
        self.task_tracker.mark_complete(task_key)
        self.progress.setValue(0)
        self.cancel_button.setEnabled(False)
        self.active_worker = None

    def handle_analyze_clicked(self):
        url = self.url_input.text().strip()
        if not url:
            self.analyze_button.setText("Invalid URL")
            QTimer.singleShot(1500, self._reset_analyze_button)
            return

        self.analyze_button.setText("Analyzing...")
        self.analyze_button.setEnabled(False)
        self._start_analyze_animation()

        cleaned_url = clean_youtube_url(url)
        worker = LUFSWorker(cleaned_url)

        worker.signals.result.connect(self._on_lufs_result)
        worker.signals.error.connect(self._on_lufs_error)

        self.thread_pool.start(worker)

    def _on_lufs_result(self, text):
        self._reset_analyze_button()
        QMessageBox.information(self, "LUFS Result", text)

    def _on_lufs_error(self, error):
        QMessageBox.critical(self, "LUFS Error", error)
        self._reset_analyze_button()

    def _reset_analyze_button(self):
        self.analyze_button.setText("Analyze")
        self.analyze_button.setEnabled(True)
        self._stop_analyze_animation()

    def _start_analyze_animation(self):
        self._analyze_base_style = self.analyze_button.styleSheet()
        self._analyze_anim = QVariantAnimation(
            startValue=QColor(100, 100, 255),
            endValue=QColor(200, 200, 255),
            duration=800
        )
        self._analyze_anim.setLoopCount(-1)
        self._analyze_anim.valueChanged.connect(self._apply_analyze_animation)
        self._analyze_anim.start()

    def _apply_analyze_animation(self, color):
        rgba = f"rgba({color.red()}, {color.green()}, {color.blue()}, 100)"
        self.analyze_button.setStyleSheet(
            f"{self._analyze_base_style}; background-color: {rgba}; border-radius: 6px;"
        )

    def _stop_analyze_animation(self):
        if self._analyze_anim:
            self._analyze_anim.stop()
            self._analyze_anim = None
        self.analyze_button.setStyleSheet(self._analyze_base_style)