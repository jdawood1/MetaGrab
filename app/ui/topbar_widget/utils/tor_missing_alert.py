from app.ui.dependency_alert_builder import DependencyAlert


class TorMissingAlert(DependencyAlert):
    def __init__(self, parent=None):
        super().__init__(
            object_name="TorMissingAlert",
            check_binary="tor",
            message="⚠️ Tor is required to connect to the anonymity network.\nInstall and restart.",
            install_steps=[
                {
                    "label": "1. Install Homebrew if not installed (Apple Silicon Macs):",
                    "command": '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"',
                    "height": 50
                },
                {
                    "label": "2. Then install Tor:",
                    "command": "brew install tor"
                }
            ],
            button_text="🌐 View Tor Daemon Installation Guide",
            help_url="https://support.torproject.org/little-t-tor/install-little-t-tor/",
            parent=parent
        )