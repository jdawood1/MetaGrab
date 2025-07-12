import sys
import traceback
from datetime import datetime
from pathlib import Path
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices


class CrashHandler:
    """Captures uncaught exceptions and saves crash reports."""

    CRASH_DIR = Path.home() / ".metagrab_crashes"
    MAX_CRASH_FILES = 5

    @classmethod
    def install(cls):
        """Install global exception handler."""
        sys.excepthook = cls.handle_exception

    @classmethod
    def handle_exception(cls, exctype, value, tb):
        """Handle any uncaught exception."""
        crash_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        crash_file = cls.CRASH_DIR / f"crash_{crash_time}.txt"
        crash_report = "".join(traceback.format_exception(exctype, value, tb))

        print("\n[MetaGrab Crash] An unexpected error occurred.", file=sys.stderr)
        print("[MetaGrab Crash] Writing crash report to disk...", file=sys.stderr)
        print(crash_report, file=sys.stderr)

        try:
            cls.CRASH_DIR.mkdir(parents=True, exist_ok=True)
            with open(crash_file, "w", encoding="utf-8") as f:
                f.write(crash_report)
            print(f"[MetaGrab Crash] Crash report saved to: {crash_file}", file=sys.stderr)
            cls._cleanup_old_crash_logs()
        except Exception as e:
            print(f"[MetaGrab Crash] Failed to save crash report: {e}", file=sys.stderr)

        cls._show_crash_dialog(crash_file)
        sys.exit(1)

    @classmethod
    def _cleanup_old_crash_logs(cls):
        """Keep only the newest 5 crash files."""
        crash_files = sorted(cls.CRASH_DIR.glob("crash_*.txt"), key=lambda f: f.stat().st_mtime, reverse=True)
        for old_file in crash_files[cls.MAX_CRASH_FILES:]:
            try:
                old_file.unlink()
                print(f"[MetaGrab Crash] Deleted old crash log: {old_file.name}", file=sys.stderr)
            except Exception as e:
                print(f"[MetaGrab Crash] Failed to delete old crash log {old_file.name}: {e}", file=sys.stderr)

    @classmethod
    def _show_crash_dialog(cls, crash_file):
        """Display a crash report dialog window."""
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)

            crash_text = crash_file.read_text(encoding="utf-8") if crash_file.exists() else "Crash report unavailable."

            crash_window = QWidget()
            crash_window.setWindowTitle("MetaGrab - Crash Detected")
            crash_window.setWindowModality(Qt.ApplicationModal)
            crash_window.resize(600, 400)

            layout = QVBoxLayout(crash_window)

            label = QLabel("<b>Oops! MetaGrab has crashed.</b><br><br>A crash report has been saved.", crash_window)
            label.setAlignment(Qt.AlignCenter)
            layout.addWidget(label)

            crash_details = QTextEdit(crash_window)
            crash_details.setReadOnly(True)
            crash_details.setPlainText(crash_text)
            layout.addWidget(crash_details)

            copy_button = QPushButton("Copy Crash Log", crash_window)
            copy_button.clicked.connect(lambda: QApplication.clipboard().setText(crash_text))
            layout.addWidget(copy_button)

            open_folder_button = QPushButton("Open Crash Folder", crash_window)
            open_folder_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(cls.CRASH_DIR))))
            layout.addWidget(open_folder_button)

            ok_button = QPushButton("OK", crash_window)
            ok_button.clicked.connect(crash_window.close)
            layout.addWidget(ok_button)

            crash_window.show()
            app.exec()

        except Exception as e:
            print(f"[MetaGrab Crash] Failed to show crash dialog: {e}", file=sys.stderr)