# app/systems/tor_system/tor_controller.py

import os
import shutil
import socket
import subprocess
import threading
import time

from stem.control import Controller

from app.core import settings
from app.core.logger import logger

TOR_PATH = shutil.which("tor")


class TorBootstrapError(Exception):
    pass


class TorController:
    def __init__(self):
        self.tor_process = None
        self._cancel_bootstrap = False

    def cancel_bootstrap(self):
        self._cancel_bootstrap = True

    def is_tor_installed(self):
        return TOR_PATH is not None

    def ensure_directories(self):
        settings.TOR_WORKING_DIR.mkdir(parents=True, exist_ok=True)
        settings.TOR_DATA_DIR.mkdir(parents=True, exist_ok=True)
        settings.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        os.chmod(settings.TOR_DATA_DIR, 0o700)

    def write_torrc(self, exit_country: str = None):
        config = f"""
        SocksPort 127.0.0.1:{settings.TOR_PORT}
        ControlPort {settings.CONTROL_PORT}
        CookieAuthentication 1
        CookieAuthFile {settings.TOR_COOKIE_PATH}
        DataDirectory {settings.TOR_DATA_DIR}
        Log notice stdout
        """.strip()

        if exit_country:
            config += f"\nExitNodes {{{exit_country}}}\nStrictNodes 1"

        settings.TOR_RC_FILE.write_text(config)

    def is_port_open(self, port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            return s.connect_ex(("127.0.0.1", port)) == 0

    def is_tor_active(self):
        try:
            with Controller.from_port(port=settings.CONTROL_PORT) as controller:
                with open(settings.TOR_COOKIE_PATH, "rb") as f:
                    controller.authenticate(f.read())
                return controller.get_info("status/circuit-established") == "1"
        except Exception:
            return False

    def start(self, exit_country=None):
        from app.systems.tor_system import bridge_bootstrapper

        self._cancel_bootstrap = False

        if not self.is_tor_installed():
            raise FileNotFoundError("Tor binary not found. Please install Tor.")

        self.ensure_directories()

        if settings.BRIDGE_ENABLED:
            self.tor_process = bridge_bootstrapper.start_tor_with_bridges()
        else:
            self.write_torrc(exit_country=exit_country)
            self.tor_process = subprocess.Popen(
                [TOR_PATH, "-f", str(settings.TOR_RC_FILE)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )

        if self.tor_process.stdout:
            threading.Thread(
                target=self.stream_tor_output, args=(self.tor_process.stdout,), daemon=True
            ).start()

        if not self.wait_for_bootstrap():
            logger.error("Tor bootstrap failed. Terminating Tor process.")
            self.stop()
            raise TorBootstrapError("Tor could not start.")

    def wait_for_bootstrap(self, timeout=90):
        retry_interval = 4
        max_retries = timeout // retry_interval

        for attempt in range(max_retries):
            if self._cancel_bootstrap:
                logger.warning("Tor bootstrap cancelled by user.")
                return False

            if self.is_tor_active():
                return True

            logger.info(f"Waiting for Tor bootstrap... attempt {attempt + 1}/{max_retries}")
            time.sleep(retry_interval)

        logger.error("Tor bootstrap timeout or failure.")
        return False

    def stream_tor_output(self, pipe):
        for line in pipe:
            if any(level in line.lower() for level in ["warn", "error", "fail"]):
                logger.warning(f"[Tor] {line.strip()}")

    def stop(self):
        self._cancel_bootstrap = True
        if self.tor_process and self.tor_process.poll() is None:
            try:
                self.tor_process.terminate()
                self.tor_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.tor_process.kill()
            logger.info("TorController: Tor process terminated.")

    def is_running(self):
        return (
            self.tor_process is not None
            and self.tor_process.poll() is None
            and self.is_tor_active()
        )
