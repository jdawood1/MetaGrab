from PySide6.QtWidgets import QTabWidget, QVBoxLayout, QWidget

from app.ui.audio_editor.audio_combiner.combiner_tab import CombineAudioTab
from app.ui.audio_editor.editing_tools.editing_tools_tab import EditingToolsTab
from app.ui.audio_editor.meta_tags.metadata_tab import MetadataTab


class AudioEditorWindow(QWidget):
    """Window for editing audio: crop, normalize, convert, combine."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Audio Editor")
        self.setObjectName("AudioEditorWindow")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.tabs = QTabWidget()
        self.tabs.addTab(MetadataTab(), "Embed Metadata")
        self.tabs.addTab(EditingToolsTab(), "Editing Tools")
        self.tabs.addTab(CombineAudioTab(), "Combine Audio")
        layout.addWidget(self.tabs)
