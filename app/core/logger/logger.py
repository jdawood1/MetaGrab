from datetime import datetime
from app.core.logger.ui_logger import UILogger
from app.core import settings
import threading

def _format_message(level, message):
    timestamp = datetime.now().strftime("[%H:%M:%S]")
    level_styles = {
        "error": "ERROR",
        "warning": "WARNING",
        "success": "SUCCESS",
        "info": "info",
        "debug": "debug",
        "console": "Console",
    }
    tag = level_styles.get(level.lower(), level.upper())
    return f"{timestamp} [{tag}] {message.strip()}"

class Logger:
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self.ui_logger = UILogger()
        self.console_enabled = settings.CONSOLE_LOGGING_ENABLED

    @classmethod
    def instance(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = Logger()
        return cls._instance

    def info(self, message):
        formatted = _format_message("info", message)
        self.ui_logger.log(formatted, level="info")
        if self.console_enabled:
            print(formatted)

    def warning(self, message):
        formatted = _format_message("warning", message)
        self.ui_logger.log(formatted, level="warning")
        if self.console_enabled:
            print(formatted)

    def error(self, message):
        formatted = _format_message("error", message)
        self.ui_logger.log(formatted, level="error")
        if self.console_enabled:
            print(formatted)

    def debug(self, message):
        formatted = _format_message("debug", message)
        self.ui_logger.log(formatted, level="debug")
        if self.console_enabled:
            print(formatted)

    def success(self, message):
        formatted = _format_message("success", message)
        self.ui_logger.log(formatted, level="success")
        if self.console_enabled:
            print(formatted)

    def console(self, message):
        formatted = _format_message("console", message)
        self.ui_logger.log(formatted, level="console")
        if self.console_enabled:
            print(formatted)

    def shutdown(self):
        self.ui_logger.shutdown()