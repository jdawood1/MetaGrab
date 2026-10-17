# app/systems/tor_system/bridge_clipboard.py

import re
import webbrowser

import pyperclip
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from app.core import settings

BRIDGE_PATTERN = re.compile(settings.TOR_BRIDGE_PATTERN, re.MULTILINE)


class BridgeGrabber(QFrame):
    bridges_saved = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("BridgeGrabber")
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(self._dark_stylesheet())
        self.setWindowFlags(Qt.Popup)
        self.setFixedWidth(440)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)

        self.button = QPushButton("🌐 Open Tor Bridge Page")
        self.button.setObjectName("BridgeAction")
        self.button.clicked.connect(self.open_bridge_site)
        layout.addWidget(self.button)

        self.status = QLabel("", self)
        self.status.setStyleSheet("color: #999; font-size: 12px;")
        layout.addWidget(self.status)

        self.manual_input = QTextEdit(self)
        self.manual_input.setPlaceholderText("Paste bridges here...")
        self.manual_input.setStyleSheet(
            "background-color: #222; color: #f0f0f0; border: 1px solid #444;"
        )
        layout.addWidget(self.manual_input)

        self.append_checkbox = QCheckBox("Append to existing bridges")
        self.append_checkbox.setStyleSheet("color: #ccc; font-size: 13px;")
        layout.addWidget(self.append_checkbox)

        save_btn = QPushButton("Save Bridges")
        save_btn.setObjectName("BridgeAction")
        save_btn.clicked.connect(self.save_manual_bridges)
        layout.addWidget(save_btn)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_clipboard)

    def _dark_stylesheet(self):
        return """
        QFrame#BridgeGrabber {
            background-color: #1a1a1a;
            border: 1px solid #333;
            border-radius: 8px;
        }
        QPushButton#BridgeAction {
            background-color: transparent;
            color: #f0f0f0;
            font-size: 13px;
            padding: 6px 10px;
            border: 1px solid #333;
            border-radius: 10px;
        }
        QPushButton#BridgeAction:hover {
            background-color: #2b2b2b;
        }
        QPushButton#BridgeAction:pressed {
            background-color: #404040;
        }
        """

    def open_bridge_site(self):
        webbrowser.open(settings.TOR_BRIDGE_URL)
        self.button.setEnabled(False)
        self.status.setText("🕵️ Waiting for clipboard...")
        self.timer.start(1000)

    def check_clipboard(self):
        matches = BRIDGE_PATTERN.findall(pyperclip.paste())
        if matches:
            self.save_bridges(matches, append=False)
            self.status.setText(f"Saved {len(matches)} bridge(s).")
            self.timer.stop()
            self.hide()

    def save_manual_bridges(self):
        matches = BRIDGE_PATTERN.findall(self.manual_input.toPlainText())
        if not matches:
            QMessageBox.warning(self, "No Bridges Found", "No valid obfs4 bridges detected.")
            return

        self.save_bridges(matches, append=self.append_checkbox.isChecked())
        QMessageBox.information(self, "Bridges Saved", f"Saved {len(matches)} bridge(s).")
        self.manual_input.clear()
        self.bridges_saved.emit()
        self.hide()

    def save_bridges(self, bridges, append=False):
        settings.TOR_BRIDGE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(settings.TOR_BRIDGE_FILE, "a" if append else "w") as f:
            f.write("\n".join(bridges) + "\n")

    def focusOutEvent(self, event):
        self.hide()
        super().focusOutEvent(event)
