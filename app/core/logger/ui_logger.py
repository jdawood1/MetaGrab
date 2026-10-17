import threading
import weakref

from PySide6.QtCore import QCoreApplication, QObject, Qt, Signal, Slot
from PySide6.QtGui import QColor, QTextCharFormat, QTextCursor
from shiboken6 import isValid


class LogBridge(QObject):
    message = Signal(str, str)

    def __init__(self, owner):
        super().__init__(QCoreApplication.instance())
        self.owner = owner
        self.message.connect(self.deliver, Qt.QueuedConnection)

    @Slot(str, str)
    def deliver(self, text, level):
        self.owner._deliver(text, level)


class UILogger:
    MAX_LINES = 2000

    def __init__(self):
        self.targets = {}
        self._lock = threading.Lock()
        self._bridge = None
        self._closed = False

    def register_target(self, name, widget):
        with self._lock:
            self._closed = False
            self.targets[name] = weakref.ref(widget)
            widget.document().setMaximumBlockCount(self.MAX_LINES)
            if self._bridge is None:
                self._bridge = LogBridge(self)

    def log(self, text, level="info"):
        with self._lock:
            bridge = self._bridge if not self._closed else None
        if bridge and text.strip():
            bridge.message.emit(text, level)

    def _deliver(self, text, level):
        with self._lock:
            reference = self.targets.get("main") if not self._closed else None
        widget = reference() if reference else None
        if widget is not None and isValid(widget):
            self._write_to_widget(widget, text, level)

    def _write_to_widget(self, widget, text, level):
        cursor = widget.textCursor()
        cursor.movePosition(QTextCursor.End)
        char_format = QTextCharFormat()
        color = self._get_color_for_level(level)
        if color:
            char_format.setForeground(color)
        char_format.setFontItalic(level == "console")
        cursor.setCharFormat(char_format)
        cursor.insertText(text + "\n")
        widget.setTextCursor(cursor)

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

    def debug(self, text):
        self.log(text, "debug")

    def info(self, text):
        self.log(text, "info")

    def warning(self, text):
        self.log(text, "warning")

    def error(self, text):
        self.log(text, "error")

    def success(self, text):
        self.log(text, "success")

    def console(self, text):
        self.log(text, "console")

    def shutdown(self):
        with self._lock:
            self._closed = True
            self.targets.clear()
