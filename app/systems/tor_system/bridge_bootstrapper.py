# app/systems/tor_system/bridge_bootstrapper.py

import os
import shutil

from app.core import processes as subprocess
from app.core import settings
from app.core.logger import logger

TOR_PATH = shutil.which("tor")
OBFS4_PATH = shutil.which("obfs4proxy")


def build_bridge_config():
    if not settings.TOR_BRIDGE_FILE.exists():
        raise FileNotFoundError("Bridge file not found — cannot start in bridge mode.")

    bridges = settings.TOR_BRIDGE_FILE.read_text().strip().splitlines()
    bridges = [line.strip() for line in bridges if line.strip()]

    if not bridges:
        raise ValueError("Bridge mode is enabled, but no valid bridges were found.")

    if not OBFS4_PATH:
        raise FileNotFoundError("obfs4proxy not found — required for bridge mode.")

    base_config = f"""
    SocksPort 127.0.0.1:{settings.TOR_PORT}
    ControlPort {settings.CONTROL_PORT}
    CookieAuthentication 1
    CookieAuthFile {settings.TOR_COOKIE_PATH}
    DataDirectory {settings.TOR_DATA_DIR}
    Log notice stdout
    UseBridges 1
    ClientTransportPlugin obfs4 exec {OBFS4_PATH}
    """.strip()

    for line in bridges:
        base_config += f"\nBridge {line}"

    return base_config


def start_tor_with_bridges():
    if not TOR_PATH:
        raise FileNotFoundError("Tor binary not found. Please install Tor.")

    settings.TOR_WORKING_DIR.mkdir(parents=True, exist_ok=True)
    settings.TOR_DATA_DIR.mkdir(parents=True, exist_ok=True)
    settings.CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    os.chmod(settings.TOR_DATA_DIR, 0o700)
    settings.TOR_RC_FILE.write_text(build_bridge_config())

    logger.info("Starting Tor with bridge mode")
    return subprocess.Popen(
        [TOR_PATH, "-f", str(settings.TOR_RC_FILE)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
