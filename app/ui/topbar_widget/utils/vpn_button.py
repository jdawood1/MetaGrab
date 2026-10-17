import webbrowser

import requests
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget

from app.core import settings


class VPNAlertWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("VPNAlertWidget")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.button = QPushButton()
        self.button.setObjectName("VPNStatusButton")
        self.button.setProperty("status", "unknown")
        self.button.setCursor(Qt.PointingHandCursor)
        self.button.setFixedHeight(28)

        self.button.clicked.connect(self.open_protonvpn_link)
        layout.addWidget(self.button)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self.update_status)
        self._timer.start(5000)

        self.update_status()

        self.setStyleSheet("""
            QPushButton#VPNStatusButton[status="active"] {
                color: #00b7ff; /* Blue */
            }

            QPushButton#VPNStatusButton[status="inactive"] {
                color: #ff5c5c; /* Red */
            }
        """)

    def update_status(self):
        home_ip = settings.load_user_settings().get("home_ip", "").strip()

        if not home_ip:
            self.button.setText("⚠️ VPN Check Disabled")
            self.button.setToolTip(
                "VPN status cannot be determined.\nPlease set your Home IP in the IP Monitor."
            )
            self.button.setProperty("status", "inactive")
        else:
            public_ip = self._get_public_ip()
            if not public_ip:
                self.button.setText("🌐 Checking IP...")
                self.button.setToolTip(
                    "Unable to fetch public IP. Please check your internet connection."
                )
                self.button.setProperty("status", "inactive")
            else:
                is_active = public_ip != home_ip
                self.button.setText("🔒 VPN is Active" if is_active else "🔓 VPN Not Detected")
                self.button.setToolTip(f"Public IP: {public_ip}\nHome IP: {home_ip}")
                self.button.setProperty("status", "active" if is_active else "inactive")

        self.button.style().unpolish(self.button)
        self.button.style().polish(self.button)

    def _get_public_ip(self) -> str:
        try:
            response = requests.get("https://api.ipify.org", timeout=5)
            return response.text.strip()
        except Exception as e:
            print(f"[VPNAlert] Failed to fetch public IP: {e}")
            return ""

    def open_protonvpn_link(self):
        webbrowser.open("https://protonvpn.com/free-vpn")
