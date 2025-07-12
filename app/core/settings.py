import json

from platformdirs import user_data_dir, user_log_dir, user_config_dir
from pathlib import Path

APP_NAME = "MetaGrab"
APP_VERSION = "v0.1.0"

# === Platform-aware base directories ===
CONFIG_DIR = Path(user_config_dir(APP_NAME))
DATA_DIR = Path(user_data_dir(APP_NAME))
LOG_DIR = Path(user_log_dir(APP_NAME))

# === App-specific subfolders ===
ORIGINALS_DIR = DATA_DIR / "Originals"
EXPORTS_DIR = Path.home() / "Downloads"  # User-facing folder

# === Tor-related paths and configuration ===
TOR_PORT = 9050
CONTROL_PORT = 9051

TOR_WORKING_DIR = DATA_DIR / "tor"
TOR_DATA_DIR = TOR_WORKING_DIR / "data"
TOR_RC_FILE = CONFIG_DIR / "torrc"
TOR_COOKIE_PATH = TOR_DATA_DIR / "control_auth_cookie"
TOR_BRIDGE_FILE = CONFIG_DIR / "tor_bridges.txt"
BRIDGE_GRABBER_SCRIPT = Path("app/systems/tor_system/bridge_clipboard.py")  # relative to root

# === Tor Bridge Grabber Configuration ===
TOR_BRIDGE_URL = "https://bridges.torproject.org/bridges?transport=obfs4"
TOR_BRIDGE_PATTERN = r"^obfs4\s.+"

# === Ensure all directories exist ===
for path in [ORIGINALS_DIR, EXPORTS_DIR, LOG_DIR, CONFIG_DIR, TOR_DATA_DIR]:
    path.mkdir(parents=True, exist_ok=True)

# === Feature toggles / flags ===
TOR_ENABLED = False
BRIDGE_ENABLED = False

NORMALIZE_AUDIO = False
STRIP_METADATA = False

CONSOLE_LOGGING_ENABLED = True

# === Persistent settings options ===
USER_SETTINGS_FILE = CONFIG_DIR / "user_settings.json"
def load_user_settings():
    try:
        if USER_SETTINGS_FILE.exists():
            with open(USER_SETTINGS_FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        print(f"[Settings] Failed to load settings: {e}")
    return {}

def save_user_settings(data: dict):
    try:
        with open(USER_SETTINGS_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[Settings] Failed to save settings: {e}")
