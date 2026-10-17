import sys

from PySide6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget

from app.styles.theme import apply_theme
from app.ui.topbar_widget.utils.obfs4proxy_alert import Obfs4MissingAlert
from app.ui.topbar_widget.utils.tor_missing_alert import TorMissingAlert


class TestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Alert Test")
        self.setMinimumSize(300, 150)

        layout = QVBoxLayout(self)

        self.obfs4_alert = Obfs4MissingAlert(None)
        self.tor_alert = TorMissingAlert(None)

        obfs4_btn = QPushButton("Show Obfs4 Alert")
        obfs4_btn.clicked.connect(lambda: self.show_alert(self.obfs4_alert, obfs4_btn))
        layout.addWidget(obfs4_btn)

        tor_btn = QPushButton("Show Tor Alert")
        tor_btn.clicked.connect(lambda: self.show_alert(self.tor_alert, tor_btn))
        layout.addWidget(tor_btn)

        self.setLayout(layout)

    def show_alert(self, alert_widget, parent_btn):
        global_pos = parent_btn.mapToGlobal(parent_btn.rect().bottomLeft())
        alert_widget.move(global_pos)
        alert_widget.show()
        alert_widget.raise_()
        alert_widget.activateWindow()


def main():
    app = QApplication(sys.argv)
    apply_theme(app)  # Optional, include if using theme.qss

    window = TestWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
