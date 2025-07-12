from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QCheckBox
from PySide6.QtCore import QTimer, Qt, QThreadPool
import socket

from app.core import settings
from app.ui.dialog_box_builder import get_confirmation
from app.ui.topbar_widget.utils.ip_fetcher import PublicIPFetcher
from app.core.resource_path import resource_path


class IPMonitorWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("IPMonitorWidget")

        self.local_ip = ""
        self.public_ip = ""
        self.home_ip = settings.load_user_settings().get("home_ip", "")
        self.show_ips = False  # Start hidden

        self.local_label = QLabel()
        self.public_label = QLabel()
        self.home_label = QLabel()

        # Hide labels initially
        self.local_label.setVisible(False)
        self.public_label.setVisible(False)
        self.home_label.setVisible(False)

        self.mask_checkbox = QCheckBox("Show IPs")
        self.mask_checkbox.setChecked(False)
        self.mask_checkbox.stateChanged.connect(self._toggle_masking)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(12)
        layout.addWidget(self.local_label)
        layout.addWidget(self.public_label)
        layout.addWidget(self.home_label)
        layout.addWidget(self.mask_checkbox)

        self.public_label.setCursor(Qt.PointingHandCursor)
        self.public_label.setToolTip("Click to set as Home IP")
        self.public_label.mousePressEvent = self._on_public_label_clicked

        self.thread_pool = QThreadPool.globalInstance()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_ips)
        self.timer.start(5000)

        self.update_ips()

    def _icon_label(self, icon_name: str, text: str) -> str:
        icon_path = resource_path(f"assets/icons/{icon_name}")
        return f'<img src="{icon_path}" width="20" height="20" style="margin-right:4px; vertical-align:top;"> {text}'

    def _toggle_masking(self, state):
        self.show_ips = bool(state)
        self.local_label.setVisible(self.show_ips)
        self.public_label.setVisible(self.show_ips)
        self.home_label.setVisible(self.show_ips and bool(self.home_ip))
        if self.show_ips:
            self._refresh_display()

    def update_ips(self):
        if not self.show_ips:
            return
        self._update_local_ip()
        self._update_public_ip()

    def _update_local_ip(self):
        try:
            hostname = socket.gethostname()
            self.local_ip = socket.gethostbyname(hostname)
        except Exception as e:
            self.local_ip = "Error"
            print(f"[IPMonitor] Failed to get local IP: {e}")
        self._refresh_display()

    def _update_public_ip(self):
        worker = PublicIPFetcher()
        worker.signals.result.connect(self._on_public_ip_result)
        worker.signals.error.connect(self._on_public_ip_error)
        self.thread_pool.start(worker)

    def _on_public_ip_result(self, ip: str):
        self.public_ip = ip
        self._refresh_display()

    def _on_public_ip_error(self, error: str):
        self.public_ip = "Error"
        print(f"[IPMonitor] Failed to get public IP: {error}")
        self._refresh_display()

    def _on_public_label_clicked(self, event):
        if not self.public_ip or self.public_ip in {"Checking...", "Error"}:
            return

        if get_confirmation(self, "Set Home IP", f"Do you want to set '{self.public_ip}' as your Home IP?"):
            settings_data = settings.load_user_settings()
            settings_data["home_ip"] = self.public_ip
            settings.save_user_settings(settings_data)

            self.home_ip = self.public_ip
            print(f"[IPMonitor] Home IP saved: {self.home_ip}")
            self._refresh_display()

    def _refresh_display(self):
        if not self.show_ips:
            return

        self.local_label.setText(self._icon_label("local_ip.svg", f"Local IP: {self.local_ip}"))
        self.public_label.setText(self._icon_label("public_ip.svg", f"Public IP: {self.public_ip}"))
        if self.home_ip:
            self.home_label.setText(self._icon_label("home_ip.svg", f"Home IP: {self.home_ip}"))