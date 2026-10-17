from pathlib import Path

from PySide6.QtCore import Qt, QThreadPool, QTimer, QUrl
from PySide6.QtGui import QColor, QPainter
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSlider, QVBoxLayout, QWidget

from app.ui.audio_editor.audio_combiner.preview_build_worker import PreviewBuildWorker


class SeekBar(QSlider):
    def __init__(self, orientation=Qt.Horizontal, parent=None):
        super().__init__(orientation, parent)
        self.markers = []
        self.setStyleSheet("""
            QSlider::handle:horizontal {
                image: none;
                width: 0px;
            }
        """)

    def set_markers(self, positions_ms: list[int]):
        self.markers = positions_ms
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.markers or self.maximum() == 0:
            return
        painter = QPainter(self)
        bar_rect = self.rect()
        for pos in self.markers:
            x = int((pos / self.maximum()) * bar_rect.width())
            painter.setPen(QColor(255, 80, 80))
            painter.drawLine(x, bar_rect.height() // 4, x, bar_rect.height() * 3 // 4)
        painter.end()


class AudioPreviewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.thread_pool = QThreadPool.globalInstance()

        self.audio_output = QAudioOutput(self)
        self.media_player = QMediaPlayer(self)
        self.media_player.setAudioOutput(self.audio_output)

        self.preview_path = None
        self.duration = 0
        self._user_is_scrubbing = False

        # Fast-seek timers
        self.seek_direction = None
        self.seek_timer = QTimer(self)
        self.seek_timer.setInterval(200)
        self.seek_timer.timeout.connect(self._fast_seek_step)

        self.press_timer = QTimer(self)
        self.press_timer.setSingleShot(True)
        self.press_timer.setInterval(300)
        self.press_timer.timeout.connect(self._begin_fast_seek)

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(4)

        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        self.label = QLabel("No preview loaded")
        self.label.setStyleSheet("color: #ccc;")
        top_row.addWidget(self.label)

        self.skip_back_btn = QPushButton("⏮")
        self.skip_back_btn.setCursor(Qt.PointingHandCursor)
        self.skip_back_btn.setToolTip("Previous segment / Hold to rewind")
        top_row.addWidget(self.skip_back_btn)

        self.play_btn = QPushButton("Play")
        self.play_btn.setCursor(Qt.PointingHandCursor)
        self.play_btn.setEnabled(False)
        self.play_btn.clicked.connect(self.toggle_play_pause)
        top_row.addWidget(self.play_btn)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setCursor(Qt.PointingHandCursor)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_audio)
        top_row.addWidget(self.stop_btn)

        self.skip_forward_btn = QPushButton("⏭")
        self.skip_forward_btn.setCursor(Qt.PointingHandCursor)
        self.skip_forward_btn.setToolTip("Next segment / Hold to fast-forward")
        top_row.addWidget(self.skip_forward_btn)

        outer_layout.addLayout(top_row)

        slider_row = QHBoxLayout()
        slider_row.setSpacing(6)

        self.time_label = QLabel("00:00")
        self.time_label.setFixedWidth(40)
        self.time_label.setAlignment(Qt.AlignRight)
        slider_row.addWidget(self.time_label)

        self.seek_slider = SeekBar(Qt.Horizontal)
        self.seek_slider.setRange(0, 0)
        self.seek_slider.setEnabled(False)
        slider_row.addWidget(self.seek_slider)

        self.duration_label = QLabel("00:00")
        self.duration_label.setFixedWidth(40)
        slider_row.addWidget(self.duration_label)

        outer_layout.addLayout(slider_row)

    def _connect_signals(self):
        self.media_player.durationChanged.connect(self._on_duration_changed)
        self.media_player.positionChanged.connect(self._on_position_changed)
        self.seek_slider.sliderMoved.connect(self._on_slider_moved)
        self.seek_slider.sliderPressed.connect(self._on_slider_pressed)
        self.seek_slider.sliderReleased.connect(self._on_slider_released)
        self.media_player.playbackStateChanged.connect(self._update_button_text)

        self.skip_back_btn.pressed.connect(lambda: self._prepare_seek(-1))
        self.skip_forward_btn.pressed.connect(lambda: self._prepare_seek(1))
        self.skip_back_btn.released.connect(self._handle_seek_release)
        self.skip_forward_btn.released.connect(self._handle_seek_release)

    def _on_duration_changed(self, duration_ms):
        self.duration = duration_ms
        self.seek_slider.setRange(0, duration_ms)
        self.seek_slider.setEnabled(True)
        self.duration_label.setText(self._format_time(duration_ms))

    def _on_position_changed(self, position_ms):
        if not self._user_is_scrubbing:
            self.seek_slider.setValue(position_ms)
            self.time_label.setText(self._format_time(position_ms))

    def _on_slider_moved(self, value):
        self.time_label.setText(self._format_time(value))

    def _on_slider_pressed(self):
        self._user_is_scrubbing = True

    def _on_slider_released(self):
        self._user_is_scrubbing = False
        self.media_player.setPosition(self.seek_slider.value())

    def _format_time(self, ms: int) -> str:
        minutes, seconds = divmod(ms // 1000, 60)
        return f"{minutes:02}:{seconds:02}"

    def toggle_play_pause(self):
        if self.media_player.playbackState() == QMediaPlayer.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()

    def stop_audio(self):
        self.media_player.stop()

    def _update_button_text(self):
        self.play_btn.setText(
            "Pause" if self.media_player.playbackState() == QMediaPlayer.PlayingState else "Play"
        )

    def _prepare_seek(self, direction):
        self.seek_direction = direction
        self._was_fast_seek = False
        self.press_timer.start()

    def _begin_fast_seek(self):
        self._was_fast_seek = True
        self.seek_timer.start()

    def _handle_seek_release(self):
        self.press_timer.stop()
        if self.seek_timer.isActive():
            self.seek_timer.stop()
        elif not getattr(self, "_was_fast_seek", False):
            if self.seek_direction == -1:
                self._jump_to_previous_marker()
            elif self.seek_direction == 1:
                self._jump_to_next_marker()

    def _fast_seek_step(self):
        if self.seek_direction is None:
            return
        pos = self.media_player.position()
        step = 2000  # 2 seconds
        new_pos = max(0, min(self.duration, pos + step * self.seek_direction))
        self.media_player.setPosition(new_pos)

    def _jump_to_previous_marker(self):
        pos = self.media_player.position()
        prev = [m for m in self.seek_slider.markers if m < pos - 2000]
        if prev:
            self.media_player.setPosition(prev[-1])
        else:
            self.media_player.setPosition(0)

    def _jump_to_next_marker(self):
        pos = self.media_player.position()
        next_ = [m for m in self.seek_slider.markers if m > pos + 2000]
        if next_:
            self.media_player.setPosition(next_[0])
        else:
            self.media_player.setPosition(self.duration)

    def set_audio_file(self, file_path: str):
        self.media_player.stop()
        self.media_player.setSource(QUrl())
        self.seek_slider.setValue(0)
        self.duration_label.setText("00:00")
        self.time_label.setText("00:00")

        if not file_path or not Path(file_path).exists():
            self.label.setText("No preview loaded")
            self.preview_path = None
            self.seek_slider.setEnabled(False)
            self.seek_slider.set_markers([])
            self.play_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            return

        self.media_player.setSource(QUrl.fromLocalFile(file_path))
        self.label.setText(Path(file_path).name)
        self.preview_path = file_path
        self.play_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)

    def set_preview_files(self, file_paths: list[str], auto_play: bool = False):
        self.stop_audio()
        self.set_audio_file("")
        previous = getattr(self, "_preview_temp_dir", None)
        if previous:
            previous.cleanup()
            self._preview_temp_dir = None
        self.seek_slider.set_markers([])

        if not file_paths or len(file_paths) < 2:
            return

        self._auto_play_after_build = auto_play
        self._current_preview_worker = PreviewBuildWorker(file_paths)
        self._current_preview_worker.signals.finished.connect(
            lambda path, markers, job=self._current_preview_worker: self._on_preview_ready(
                path, markers, job
            )
        )
        QThreadPool.globalInstance().start(self._current_preview_worker)

    def _on_preview_ready(self, preview_path: str, markers: list[int], worker=None):
        if worker is not None and worker is not self._current_preview_worker:
            worker.temp_dir.cleanup()
            return
        if not preview_path or not Path(preview_path).exists():
            self.set_audio_file("")
            return

        previous = getattr(self, "_preview_temp_dir", None)
        self.media_player.stop()
        self.media_player.setSource(QUrl())
        if previous:
            previous.cleanup()
        self._preview_temp_dir = (worker or self._current_preview_worker).temp_dir
        self.set_audio_file(preview_path)
        self.seek_slider.set_markers(markers)
        if getattr(self, "_auto_play_after_build", False):
            self.media_player.play()

    def clear_preview(self):
        self.stop_audio()
        self.set_audio_file("")
        previous = getattr(self, "_preview_temp_dir", None)
        if previous:
            previous.cleanup()
            self._preview_temp_dir = None
        self.seek_slider.set_markers([])
