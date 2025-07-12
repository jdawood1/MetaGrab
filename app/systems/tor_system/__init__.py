from .tor_manager import TorManager
from .tor_controller import TorController

# Shared Tor controller instance (default = no bridges)
tor_controller = TorController()