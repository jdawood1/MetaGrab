from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QWidget, QLabel, QHBoxLayout, QVBoxLayout,
    QPushButton, QCheckBox, QComboBox, QFrame
)
from PySide6.QtCore import QThreadPool, QPoint, QSize

from app.core import settings
from app.core.resource_path import resource_path
from app.ui.topbar_widget.utils.ip_monitor import IPMonitorWidget
from app.ui.topbar_widget.utils.vpn_button import VPNAlertWidget
from app.ui.topbar_widget.utils.tor_switches import TorControlRunnable
from app.ui.topbar_widget.utils.obfs4proxy_alert import Obfs4MissingAlert
from app.ui.topbar_widget.utils.tor_missing_alert import TorMissingAlert
from app.systems.tor_system.bridge_clipboard import BridgeGrabber


class TopBarMenu(QWidget):
    """Top bar displaying system status and Tor toggle."""

    def __init__(self, tor_manager, parent=None):
        super().__init__(parent)
        self.setObjectName("TopBarMenu")

        self.tor_manager = tor_manager
        self.thread_pool = QThreadPool.globalInstance()
        self._last_status_message = ""
        self._tor_enabled = settings.TOR_ENABLED
        self.bridge_window = None
        self.obfs4_alert = Obfs4MissingAlert(self)
        self.tor_alert = TorMissingAlert(self)

        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ========== Top Bar Layout ==========
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(15, 4, 15, 4)
        top_layout.setSpacing(16)

        self.logo_label = QLabel("MetaGrab", self)
        self.logo_label.setObjectName("LogoLabel")

        self.ip_monitor = IPMonitorWidget(self)

        self.tor_status_label = QLabel("Tor: OFF", self)
        self.tor_checkbox = QCheckBox("Enable Tor", self)
        self.tor_checkbox.setChecked(self._tor_enabled)
        self.tor_checkbox.stateChanged.connect(self.toggle_tor)

        icon_path = resource_path("assets/icons/filters-icon.svg")
        self.settings_button = QPushButton("", self)
        self.settings_button.setIcon(QIcon(icon_path))
        self.settings_button.setIconSize(QSize(25, 25))
        self.settings_button.setFixedSize(36, 36)
        self.settings_button.setToolTip("Toggle Settings")
        self.settings_button.clicked.connect(self._toggle_settings_view)

        self.vpn_button = VPNAlertWidget(self)

        top_layout.addWidget(self.logo_label)
        top_layout.addStretch()
        top_layout.addWidget(self.ip_monitor)
        top_layout.addWidget(self.tor_status_label)
        top_layout.addWidget(self.tor_checkbox)

        if self.tor_alert.check_and_show():
            self.tor_checkbox.setEnabled(False)
            self.tor_checkbox.setToolTip("Tor is not installed. Please install it to enable this option.")
            self.tor_info_button = QPushButton("⚠️")
            self.tor_info_button.setStyleSheet("QPushButton { background: transparent; }")
            self.tor_info_button.setToolTip("Click to view Tor installation instructions.")
            self.tor_info_button.clicked.connect(lambda: self._tor_info_button_clicked())
            top_layout.addWidget(self.tor_info_button)

        top_layout.addWidget(self.vpn_button)
        top_layout.addWidget(self.settings_button)

        main_layout.addLayout(top_layout)

        # ========== Detail Container ==========
        self.detail_container = QFrame(self)
        self.detail_container.setObjectName("DetailContainer")

        container_layout = QVBoxLayout(self.detail_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        self.detail_frame = QFrame(self.detail_container)
        self.detail_frame.setVisible(False)

        detail_layout = QVBoxLayout(self.detail_frame)
        detail_layout.setContentsMargins(20, 8, 20, 8)
        detail_layout.setSpacing(8)

        # ========== Exit Controls Group ==========
        exit_controls_layout = QHBoxLayout()
        exit_controls_layout.setSpacing(12)

        self.exit_country_selector = QComboBox()
        self.exit_country_selector.setToolTip("Select preferred exit node country")
        self.exit_country_selector.addItem("Auto", "")
        self._populate_country_selector()
        self.exit_country_selector.currentIndexChanged.connect(self._on_exit_node_changed)

        self.get_bridges_button = QPushButton("Manage Bridges")
        self.get_bridges_button.setObjectName("BridgeButton")
        self.get_bridges_button.setToolTip("Fetch or manually paste Tor bridges")
        self.get_bridges_button.clicked.connect(self._show_bridge_grabber)

        self.bridge_mode_checkbox = QCheckBox("Use Bridge Mode")
        self.bridge_mode_checkbox.setChecked(settings.BRIDGE_ENABLED)
        self.bridge_mode_checkbox.stateChanged.connect(self._on_bridge_mode_toggled)

        if self.obfs4_alert.check_and_show():
            self.bridge_mode_checkbox.setEnabled(False)
            self.bridge_mode_checkbox.setToolTip("obfs4proxy not detected — required for Bridge Mode.")

        exit_controls_layout.addWidget(QLabel("🌐 Exit Location:"))
        exit_controls_layout.addWidget(self.exit_country_selector)
        exit_controls_layout.addWidget(self.get_bridges_button)
        exit_controls_layout.addWidget(self.bridge_mode_checkbox)
        exit_controls_layout.addStretch()

        detail_layout.addLayout(exit_controls_layout)

        container_layout.addWidget(self.detail_frame)
        main_layout.addWidget(self.detail_container)

    def _populate_country_selector(self):
        countries = {
            # Existing countries
            "🇺🇸 United States": "us", "🇩🇪 Germany": "de", "🇳🇱 Netherlands": "nl",
            "🇨🇦 Canada": "ca", "🇬🇧 United Kingdom": "gb", "🇫🇷 France": "fr",
            "🇸🇪 Sweden": "se", "🇨🇭 Switzerland": "ch", "🇳🇴 Norway": "no",
            "🇫🇮 Finland": "fi", "🇯🇵 Japan": "jp", "🇪🇸 Spain": "es",
            "🇮🇹 Italy": "it", "🇧🇪 Belgium": "be", "🇦🇺 Australia": "au",
            "🇩🇰 Denmark": "dk", "🇵🇱 Poland": "pl", "🇧🇷 Brazil": "br",
            "🇮🇳 India": "in", "🇸🇬 Singapore": "sg", "🇷🇺 Russia": "ru",
            "🇦🇶 Antarctica": "aq",

            # Newly added countries
            "🇦🇹 Austria": "at", "🇮🇪 Ireland": "ie", "🇵🇹 Portugal": "pt", "🇬🇷 Greece": "gr",
            "🇨🇿 Czech Republic": "cz", "🇭🇺 Hungary": "hu", "🇺🇦 Ukraine": "ua", "🇷🇴 Romania": "ro",
            "🇲🇽 Mexico": "mx", "🇦🇷 Argentina": "ar", "🇨🇱 Chile": "cl", "🇨🇴 Colombia": "co",
            "🇰🇷 South Korea": "kr", "🇹🇭 Thailand": "th", "🇮🇩 Indonesia": "id", "🇹🇷 Turkey": "tr",
            "🇮🇱 Israel": "il", "🇿🇦 South Africa": "za", "🇳🇿 New Zealand": "nz", "🇮🇸 Iceland": "is"
        }

        for label, code in countries.items():
            self.exit_country_selector.addItem(label, code)

    # ========== TOR CONTROL ==========

    def toggle_tor(self, state):
        current_state = bool(state)
        if current_state == self._tor_enabled:
            return

        self._tor_enabled = current_state
        settings.TOR_ENABLED = current_state

        if current_state:
            self._start_tor_async()
        else:
            self._stop_tor_async()

    def _tor_info_button_clicked(self):
        # Re-run the same alert logic
        if self.tor_alert.check_and_show(self.tor_checkbox):
            self.tor_checkbox.setChecked(False)

    def _on_exit_node_changed(self):
        index = self.exit_country_selector.currentIndex()
        exit_country = self.exit_country_selector.itemData(index)
        exit_label = self.exit_country_selector.itemText(index)

        runnable = TorControlRunnable(
            self.tor_manager,
            mode="switch",
            exit_country=exit_country,
            exit_label=exit_label
        )
        runnable.signals.finished.connect(self._on_tor_signal)
        self.thread_pool.start(runnable)

    def _start_tor_async(self, exit_country=None):
        index = self.exit_country_selector.currentIndex()
        exit_country = self.exit_country_selector.itemData(index)
        exit_label = self.exit_country_selector.itemText(index)

        runnable = TorControlRunnable(
            self.tor_manager,
            mode="start",
            exit_country=exit_country,
            exit_label=exit_label
        )
        runnable.signals.finished.connect(self._on_tor_signal)
        self.thread_pool.start(runnable)

    def _stop_tor_async(self):
        runnable = TorControlRunnable(self.tor_manager, mode="stop")
        runnable.signals.finished.connect(self._on_tor_signal)
        self.thread_pool.start(runnable)

    def _on_tor_signal(self, success: bool, message: str):
        self.tor_status_label.setText(message)

    # ========== UI ACTIONS ==========

    def _toggle_settings_view(self):
        self.detail_frame.setVisible(not self.detail_frame.isVisible())

    def _show_bridge_grabber(self):
        if self.obfs4_alert.check_and_show(self.get_bridges_button):
            return

        if not hasattr(self, "bridge_window") or self.bridge_window is None:
            self.bridge_window = BridgeGrabber(self)

        global_pos = self.get_bridges_button.mapToGlobal(QPoint(0, self.get_bridges_button.height()))
        self.bridge_window.move(global_pos)
        self.bridge_window.show()
        self.bridge_window.raise_()
        self.bridge_window.activateWindow()

    def _on_bridge_mode_toggled(self, state):
        settings.BRIDGE_ENABLED = bool(state)
        index = self.exit_country_selector.currentIndex()
        exit_country = self.exit_country_selector.itemData(index)
        exit_label = self.exit_country_selector.itemText(index)

        runnable = TorControlRunnable(
            self.tor_manager,
            mode="bridge",
            exit_country=exit_country,
            exit_label=exit_label,
            bridge_enabled=bool(state)
        )
        runnable.signals.finished.connect(self._on_tor_signal)
        self.thread_pool.start(runnable)