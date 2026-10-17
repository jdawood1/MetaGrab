import threading

from PySide6.QtGui import QColor, QTextCharFormat, QTextCursor


class UILogger:
    MAX_LINES = 2000

    def __init__(self):
        self.targets = {}
        self._lock = threading.Lock()

    def register_target(self, name, widget):
        with self._lock:
            self.targets[name] = widget

    def log(self, text: str, level: str = "info"):
        if not text.strip():
            return
        formatted_text = text

        with self._lock:
            widget = self.targets.get("main")

        if widget:
            self._write_to_widget(widget, formatted_text, level)

    def _write_to_widget(self, widget, text, level):
        if widget is None:
            return

        widget.moveCursor(QTextCursor.End)
        cursor = widget.textCursor()
        char_format = QTextCharFormat()

        color = self._get_color_for_level(level)
        if color:
            char_format.setForeground(color)
        if level == "console":
            char_format.setFontItalic(True)

        cursor.setCharFormat(char_format)
        cursor.insertText(text + "\n")
        cursor.setCharFormat(QTextCharFormat())
        widget.moveCursor(QTextCursor.End)
        self._truncate_widget(widget)

    def _get_color_for_level(self, level):
        if level == "warning":
            return QColor("orange")
        elif level == "error":
            return QColor("red")
        elif level == "console":
            return QColor("gray")
        elif level == "debug":
            return QColor("cyan")
        elif level == "info":
            return QColor("white")
        elif level == "success":
            return QColor("lightgreen")
        else:
            return None

    def _truncate_widget(self, widget):
        document = widget.document()
        if document.blockCount() > self.MAX_LINES:
            cursor = widget.textCursor()
            cursor.movePosition(cursor.Start)
            for _ in range(document.blockCount() - self.MAX_LINES):
                cursor.select(cursor.LineUnderCursor)
                cursor.removeSelectedText()
                cursor.deleteChar()

    def debug(self, text):
        self.log(text, level="debug")

    def info(self, text):
        self.log(text, level="info")

    def warning(self, text):
        self.log(text, level="warning")

    def error(self, text):
        self.log(text, level="error")

    def success(self, text):
        self.log(text, level="success")

    def console(self, text):
        self.log(text, level="console")

    def shutdown(self):
        """Clear all registered widgets to avoid access after deletion."""
        with self._lock:
            self.targets.clear()
