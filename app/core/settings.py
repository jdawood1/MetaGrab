import json
import tempfile
from pathlib import Path

from platformdirs import user_config_dir, user_data_dir, user_log_dir

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
for path in [ORIGINALS_DIR, LOG_DIR, CONFIG_DIR, TOR_DATA_DIR]:
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(f"[Settings] Folder unavailable: {path}: {exc}")

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
                data = json.load(f)
                return data if isinstance(data, dict) else {}
    except Exception as e:
        print(f"[Settings] Failed to load settings: {e}")
    return {}


def save_user_settings(data: dict):
    temporary = None
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w", dir=CONFIG_DIR, suffix=".tmp", delete=False
        ) as f:
            temporary = Path(f.name)
            json.dump(data, f, indent=2)
        temporary.replace(USER_SETTINGS_FILE)
        return True
    except OSError as exc:
        print(f"[Settings] Failed to save settings: {exc}")
        return False
    finally:
        if temporary and temporary.exists():
            temporary.unlink()


def set_exports_dir(directory):
    """Validate a user-selected folder and persist it before changing the destination."""
    global EXPORTS_DIR
    directory = Path(directory).expanduser().resolve()
    if not directory.is_dir():
        raise OSError("Choose an existing folder.")
    next(directory.iterdir(), None)
    with tempfile.TemporaryFile(dir=directory):
        pass
    data = load_user_settings()
    data["exports_dir"] = str(directory)
    if not save_user_settings(data):
        raise OSError("Could not save the download folder preference.")
    EXPORTS_DIR = directory
    return directory


_saved_exports = load_user_settings().get("exports_dir")
if isinstance(_saved_exports, str) and Path(_saved_exports).is_absolute():
    EXPORTS_DIR = Path(_saved_exports)
