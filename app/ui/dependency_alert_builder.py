import shutil
import webbrowser
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QPushButton, QPlainTextEdit
)
from PySide6.QtCore import Qt


class DependencyAlert(QFrame):
    def __init__(self, *, object_name, check_binary, message, install_steps, button_text, help_url, parent=None):
        super().__init__(parent)
        self.setObjectName(object_name)
        self.setProperty("class", "DependencyAlert")
        self.check_binary = check_binary
        self.help_url = help_url

        self.setWindowFlags(Qt.Popup)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFixedWidth(460)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        label = QLabel(message)
        label.setWordWrap(True)
        layout.addWidget(label)

        for step in install_steps:
            layout.addWidget(QLabel(step["label"]))
            cmd_box = QPlainTextEdit()
            cmd_box.setPlainText(step["command"])
            cmd_box.setReadOnly(True)
            cmd_box.setFixedHeight(step.get("height", 40))
            layout.addWidget(cmd_box)

        docs_btn = QPushButton(button_text)
        docs_btn.clicked.connect(self._open_help_link)
        layout.addWidget(docs_btn)

    def _open_help_link(self):
        webbrowser.open(self.help_url)

    def check_and_show(self, button_widget=None) -> bool:
        if shutil.which(self.check_binary) is not None:
            return False

        if button_widget is not None:
            global_pos = button_widget.mapToGlobal(button_widget.rect().bottomLeft())
            self.move(global_pos)

        self.show()
        self.raise_()
        self.activateWindow()
        return True