from PySide6.QtWidgets import QTextEdit, QVBoxLayout, QWidget

from app.core.logger import logger


class ConsoleOutput(QWidget):
    """Live console output widget for status/log messages."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ConsoleOutput")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)

        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        self.output_area.setObjectName("OutputArea")

        logger.ui_logger.register_target("main", self.output_area)
        logger.console("Ready.")

        layout.addWidget(self.output_area)

    def append_text(self, text: str):
        """Append a new line of text to the console."""
        self.output_area.append(text)
