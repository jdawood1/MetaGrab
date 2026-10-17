# app/systems/tor_system/tor_manager.py
import atexit
import subprocess

from app.core import settings
from app.core.logger import logger
from app.systems.tor_system.tor_controller import TorController


class TorManager:
    def __init__(self):
        self.controller = TorController()
        self.running = False
        atexit.register(self.stop)

    def start(self, exit_country=None):
        if not settings.TOR_ENABLED:
            logger.debug("TorManager: TOR_ENABLED is False.")
            return

        logger.info(f"TorManager: Starting Tor system... (exit_country={exit_country or 'Auto'})")

        try:
            self.controller.start(exit_country=exit_country)
            self.running = True
            logger.info("TorManager: Tor system started.")
        except Exception as e:
            logger.error(f"TorManager: Failed to start Tor: {e}")
            self.running = False

    def stop(self):
        logger.info("TorManager: Stopping Tor system...")
        try:
            self.controller.cancel_bootstrap()
            self.controller.stop()
        except Exception as e:
            logger.warning(f"TorManager: Error during controller stop: {e}")

        try:
            subprocess.run(
                ["pkill", "-9", "tor"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            logger.info("TorManager: All Tor processes force-killed.")
        except subprocess.CalledProcessError:
            logger.info("TorManager: No Tor processes were running.")
        except Exception as e:
            logger.error(f"TorManager: Error during pkill: {e}")

        self.running = False
