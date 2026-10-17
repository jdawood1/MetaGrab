from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.core.settings import APP_NAME, APP_VERSION
from app.ui.audio_editor.audio_editor_window import AudioEditorWindow
from app.ui.downloads_tab.download_window import DownloadsWindow
from app.ui.folders_tab.folder_window import FolderWindow
from app.ui.main_window.console_box import ConsoleOutput
from app.ui.main_window.sidebar_menu import SidebarMenu
from app.ui.main_window.video_tab_placeholder import VideoStudioPlaceholder
from app.ui.topbar_widget.topbar_widget import TopBarMenu


class MainWindow(QMainWindow):
    """The main window of MetaGrab."""

    def __init__(self, tor_manager, shutdown_manager=None):
        super().__init__()

        self.tor_manager = tor_manager
        self.shutdown_manager = shutdown_manager

        self.setWindowTitle(f"{APP_NAME} {APP_VERSION}")
        self.setMinimumSize(1280, 800)
        self.setMaximumSize(1280, 800)
        self.setObjectName("MainWindow")

        self.setup_ui()

    def setup_ui(self):
        # Central Widget
        main_widget = QWidget(self)
        self.setCentralWidget(main_widget)

        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Top Bar with TorManager passed in
        self.topbar = TopBarMenu(tor_manager=self.tor_manager)
        main_layout.addWidget(self.topbar)

        # Splitter for body + console
        main_splitter = QSplitter(Qt.Vertical)

        # Body section
        body_container = QWidget()
        body_layout = QHBoxLayout(body_container)
        body_layout.setContentsMargins(0, 0, 0, 0)

        self.sidebar = SidebarMenu()
        body_layout.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        body_layout.addWidget(self.stack)

        main_splitter.addWidget(body_container)

        # Console section
        self.console = ConsoleOutput()
        main_splitter.addWidget(self.console)
        main_splitter.setSizes([800, 300])

        # Add splitter to the main layout
        main_layout.addWidget(main_splitter)

        # Pages
        self.folder_page = FolderWindow()
        self.downloads_page = DownloadsWindow()
        self.audio_editor_page = AudioEditorWindow()
        self.video_studio_page = VideoStudioPlaceholder(self)

        self.stack.addWidget(self.folder_page)
        self.stack.addWidget(self.downloads_page)
        self.stack.addWidget(self.audio_editor_page)
        self.stack.addWidget(self.video_studio_page)

        # Navigation
        self.sidebar.browser_clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.sidebar.downloads_clicked.connect(lambda: self.stack.setCurrentIndex(1))
        self.sidebar.audio_editor_clicked.connect(lambda: self.stack.setCurrentIndex(2))
        self.sidebar.video_studio_clicked.connect(lambda: self.stack.setCurrentIndex(3))

    def closeEvent(self, event):
        if self.shutdown_manager and not self.shutdown_manager.complete:
            event.ignore()
            self.shutdown_manager.request(self)
        else:
            event.accept()
