from pathlib import Path
from PySide6.QtWidgets import QFrame, QTextBrowser
from PySide6.QtCore import Qt, QPoint, QThreadPool, QTimer

from app.ui.folders_tab.utils.folder_preview import summarize_folder
from app.ui.folders_tab.utils.lufs_preview import start_lufs_analysis

class PreviewBox(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.ToolTip)
        self.setObjectName("PreviewBox")
        self.setWindowFlags(Qt.ToolTip)
        self.setFrameShape(QFrame.StyledPanel)

        self.text_area = QTextBrowser(self)
        self.text_area.setObjectName("TextArea")
        self.text_area.setOpenExternalLinks(True)
        self.text_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text_area.resize(300, 0)

        self.thread_pool = QThreadPool.globalInstance()
        self.active_lufs_runner = None

        self.loading_timer = QTimer(self)
        self.loading_timer.setInterval(500)
        self.loading_timer.timeout.connect(self.update_loading_text)
        self.loading_base_text = ""
        self.loading_dot_count = 0

    def set_text(self, text: str):
        self.stop_text_loader()
        self.text_area.setHtml(f"<div style='text-align: left;'>{text}</div>")
        self._resize_to_content()

    def _resize_to_content(self):
        # Delay the resize slightly to ensure the layout is updated
        QTimer.singleShot(0, self._finalize_resize)

    def _finalize_resize(self):
        doc_height = self.text_area.document().size().height()
        max_height = 400
        height = min(int(doc_height) + 20, max_height)
        width = 300
        self.text_area.resize(width, height)
        self.resize(width, height)

    def show_text_loader(self, base_text="Analyzing"):
        self.loading_base_text = base_text
        self.loading_dot_count = 0
        self.text_area.setHtml(f"<div style='text-align: left; margin-top: 10px;'>{base_text}</div>")
        self._resize_to_content()
        self.loading_timer.start()

    def update_loading_text(self):
        self.loading_dot_count += 1
        dots = "." * self.loading_dot_count
        animated = f"{self.loading_base_text}{dots}"
        self.text_area.setHtml(f"<div style='text-align: left; margin-top: 10px;'>{animated}</div>")
        self._resize_to_content()

    def stop_text_loader(self):
        self.loading_timer.stop()
        self.loading_dot_count = 0

    def show_at(self, global_pos: QPoint):
        self.move(global_pos + QPoint(20, 20))
        self.show()

    def preview_path(self, path: Path):
        if self.active_lufs_runner:
            self.active_lufs_runner.terminate()
            self.active_lufs_runner = None

        if path.is_dir():
            self.set_text(summarize_folder(path))
        elif path.suffix.lower() in [".txt", ".srt"]:
            self._preview_text_file(path)
        elif path.suffix.lower() in [".mp3", ".m4a", ".flac", ".aac", ".wav", ".opus", ".webm"]:
            start_lufs_analysis(path, self, self.thread_pool)
        else:
            self.set_text("No preview available.")

    def _preview_text_file(self, path: Path):
        try:
            text = path.read_text(errors="ignore")[:1500]
            self.set_text(f"<pre>{text}</pre>")
        except Exception as e:
            self.set_text(f"Could not read file:<br><i>{e}</i>")