from PySide6.QtCore import Qt
from PySide6.QtGui import QMovie, QPixmap
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from app.core.logger import logger
from app.core.resource_path import AssetNotFoundError, resource_path

LOG_MEDIA_SPLASH = False


class MediaSplash(QWidget):
    def __init__(self, asset_path: str, comment: str = None, parent=None, autoplay=True, loop=True):
        super().__init__(parent)
        self.setWindowFlags(Qt.SplashScreen | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(6)

        self.label = QLabel(alignment=Qt.AlignCenter)
        self.layout.addWidget(self.label)

        self.comment_label = None
        self._pending_comment = comment
        self._default_comment_y_offset = -40  # relative to bottom

        self.movie = None

        try:
            full_path = resource_path(asset_path)
            if LOG_MEDIA_SPLASH:
                logger.debug(f"MediaSplash: Resolved asset path to {full_path}")
        except AssetNotFoundError as e:
            self.label.setText("⚠️ Media not found")
            logger.warning(f"MediaSplash: Asset not found: {e}")
            return

        if full_path.lower().endswith(".gif"):
            self.movie = QMovie(full_path)
            self.movie.setCacheMode(QMovie.CacheAll)
            self.label.setMovie(self.movie)
            if LOG_MEDIA_SPLASH:
                logger.info(f"MediaSplash: Playing GIF {full_path}")
            if autoplay:
                if LOG_MEDIA_SPLASH:
                    logger.debug("MediaSplash: Autoplay enabled for GIF")
                self.movie.start()
            if loop:
                if LOG_MEDIA_SPLASH:
                    logger.debug("MediaSplash: Looping enabled for GIF")
                self.movie.finished.connect(lambda: self.movie.start())

        elif full_path.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            pixmap = QPixmap(full_path)
            self.label.setPixmap(pixmap)
            if LOG_MEDIA_SPLASH:
                logger.info(f"MediaSplash: Displaying image {full_path}")

        else:
            self.label.setText("⚠️ Unsupported media type")
            logger.warning(f"MediaSplash: Unsupported media type for {full_path}")
            return

        if LOG_MEDIA_SPLASH:
            logger.success("MediaSplash initialized successfully.")

    def showEvent(self, event):
        super().showEvent(event)

        if self._pending_comment:
            # Dynamically center comment horizontally, offset from bottom
            dummy_label = QLabel(self._pending_comment)
            dummy_label.setFont(self.font())
            dummy_label.adjustSize()
            comment_width = dummy_label.width()
            comment_height = dummy_label.height()

            x = (self.width() - comment_width) // 2
            y = self.height() - comment_height + self._default_comment_y_offset

            self.set_comment(self._pending_comment, x=x, y=y)

    def center_on_parent(self):
        self.adjustSize()
        splash_geometry = self.frameGeometry()

        if self.parent():
            parent_geometry = self.parent().geometry()
        else:
            screen = self.screen().availableGeometry()
            parent_geometry = screen

        center_point = parent_geometry.center()
        splash_geometry.moveCenter(center_point)
        self.move(splash_geometry.topLeft())

    def set_fixed_size(self, width: int, height: int):
        self.setFixedSize(width, height)
        if self.movie:
            self.movie.setScaledSize(self.size())
        elif self.label.pixmap():
            scaled = self.label.pixmap().scaled(
                self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.label.setPixmap(scaled)

    def scale_to_parent(self, scale_factor: float = 0.5):
        if self.parent():
            pw = self.parent().width()
            ph = self.parent().height()
        else:
            screen = self.screen().availableGeometry()
            pw = screen.width()
            ph = screen.height()

        new_width = int(pw * scale_factor)
        new_height = int(ph * scale_factor)
        self.set_fixed_size(new_width, new_height)

    def set_comment(
        self,
        text: str,
        *,
        x: int = 0,
        y: int = 0,
        color: str = "white",
        font_size: int = 12,
        italic: bool = False,
        bold: bool = False,
        rich: bool = False,
    ):
        """Set or update the comment text with styling and absolute positioning."""
        if self.comment_label is None:
            self.comment_label = QLabel(self)
            self.comment_label.setTextFormat(Qt.RichText if rich else Qt.PlainText)

        font_style = []
        if italic:
            font_style.append("font-style: italic;")
        if bold:
            font_style.append("font-weight: bold;")

        self.comment_label.setStyleSheet(
            f"color: {color}; font-size: {font_size}px; {' '.join(font_style)}"
        )
        self.comment_label.setText(text)
        self.comment_label.adjustSize()
        self.comment_label.move(x, y)
        self.comment_label.show()
