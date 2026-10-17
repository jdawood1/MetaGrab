from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.core.resource_path import resource_path
from app.ui.audio_editor.audio_combiner.file_drop_widget import FileDropWidget


def colored_icon(svg_path: str, color: QColor) -> QIcon:
    pixmap = QPixmap(svg_path)
    if pixmap.isNull():
        return QIcon()
    tinted = QPixmap(pixmap.size())
    tinted.fill(Qt.transparent)

    painter = QPainter(tinted)
    painter.setCompositionMode(QPainter.CompositionMode_Source)
    painter.drawPixmap(0, 0, pixmap)
    painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
    painter.fillRect(tinted.rect(), color)
    painter.end()

    return QIcon(tinted)


class FileDropContainer(QWidget):
    files_updated = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.drop_widgets = []
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(20)

        # Top bar with the Clear All button
        top_bar = QHBoxLayout()
        top_bar.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.clear_button = QToolButton()
        self.clear_button.setObjectName("ClearAllButton")

        # Use resource_path to load and tint the icon
        icon_path = resource_path("assets/icons/trash_can.svg")
        self.icon_path = icon_path  # Store for later use

        self.clear_button.setIcon(colored_icon(icon_path, QColor("white")))
        self.clear_button.setCursor(Qt.PointingHandCursor)
        self.clear_button.setToolTip("Clear All Files")

        # Hover events to change icon color
        def enter_event(_):
            self.clear_button.setIcon(colored_icon(icon_path, QColor("red")))

        def leave_event(_):
            self.clear_button.setIcon(colored_icon(icon_path, QColor("white")))

        self.clear_button.enterEvent = enter_event
        self.clear_button.leaveEvent = leave_event

        self.clear_button.clicked.connect(self.clear_all)
        top_bar.addWidget(self.clear_button)

        main_layout.addLayout(top_bar)

        # File row layout
        self.row_layout = QHBoxLayout()
        self.row_layout.setSpacing(12)
        main_layout.addLayout(self.row_layout)

        main_layout.addStretch()

        # Start with 3-drop widgets
        self.add_widget(force=True)
        self.add_widget(force=True)
        self.add_widget(force=True)

    def add_widget(self, force=False):
        if self.drop_widgets and not force:
            last = self.drop_widgets[-1]
            if not last.has_file():
                return

        widget = FileDropWidget()
        widget.file_changed_callback = lambda: self._on_widget_change(widget)
        self.drop_widgets.append(widget)
        self._rebuild_layout()
        self.files_updated.emit()

    def _rebuild_layout(self):
        while self.row_layout.count():
            item = self.row_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)

        for widget in self.drop_widgets:
            self.row_layout.addWidget(widget)

        add_button = QPushButton("+")
        add_button.setObjectName("AddFileButton")
        add_button.setFixedSize(40, 40)
        add_button.setCursor(Qt.PointingHandCursor)
        add_button.setToolTip("Add Another File")

        add_button.clicked.connect(lambda: self.add_widget(force=True))
        self.row_layout.addWidget(add_button)

    def _on_widget_change(self, widget: FileDropWidget):
        all_filled = all(w.has_file() for w in self.drop_widgets)
        if widget.has_file() and all_filled:
            self.add_widget()
        self.files_updated.emit()

    def clear_all(self):
        for widget in self.drop_widgets:
            widget.setParent(None)
        self.drop_widgets.clear()

        for _ in range(3):
            self.add_widget(force=True)

        self.files_updated.emit()

    def get_file_paths(self) -> list[str]:
        return [w.file_path for w in self.drop_widgets if w.has_file()]
