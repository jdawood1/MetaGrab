from app.ui.dependency_alert_builder import DependencyAlert


class Obfs4MissingAlert(DependencyAlert):
    def __init__(self, parent=None):
        super().__init__(
            object_name="Obfs4MissingAlert",
            check_binary="obfs4proxy",
            message="⚠️ Bridge mode requires the 'obfs4proxy' transport tool.\nInstall and restart.",
            install_steps=[
                {
                    "label": "1. Install Homebrew if not installed (Apple Silicon Macs):",
                    "command": '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"',
                    "height": 50
                },
                {
                    "label": "2. Then install obfs4proxy:",
                    "command": "brew install obfs4proxy"
                }
            ],
            button_text="🌐 View Tor Docs on obfs4proxy",
            help_url="https://2019.www.torproject.org/docs/pluggable-transports.html.en#obfs4proxy",
            parent=parent
        )