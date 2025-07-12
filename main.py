import os
import sys
import traceback
import faulthandler
import signal

faulthandler.enable()

# Fix system PATH for subprocess tools
os.environ["PATH"] = "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:" + os.environ.get("PATH", "")

from PySide6.QtWidgets import QApplication
from app.ui.main_window.central_window import MainWindow
from app.ui.splash_builder import MediaSplash

# Core systems
from app.core.logger import logger
from app.core.crash_log import CrashHandler
from app.core.shutdown_mgr import ShutdownManager
from app.systems.tor_system.tor_manager import TorManager
from app.styles.theme import apply_theme

# Global
shutdown_manager = ShutdownManager()

# Handle Ctrl+C or kill signal
def _on_interrupt(sig, frame):
    logger.info("Main: Interrupt signal received. Initiating shutdown...")
    shutdown_manager.shutdown()
    sys.exit(0)

signal.signal(signal.SIGINT, _on_interrupt)

def main():
    CrashHandler.install()

    tor_manager = TorManager()

    # Register all shutdown tasks
    shutdown_manager.register_pre_task(shutdown_manager.wait_for_tor_runnables)
    shutdown_manager.register_pre_task(shutdown_manager.wait_for_downloads)
    shutdown_manager.register_pre_task(shutdown_manager.wait_for_audio_threads)
    shutdown_manager.register(logger.shutdown)
    shutdown_manager.register(tor_manager.stop)

    try:
        app = QApplication(sys.argv)
        apply_theme(app)

        splash = MediaSplash("assets/logo.png")
        splash.scale_to_parent(0.30)
        splash.center_on_parent()

        splash.set_comment(
            "🌀 Initializing modules...",
            x=30,
            y=250,
            font_size=14,
            italic=True,
            bold=True,
            color="#00ccff"
        )

        splash.show()

        window = MainWindow(tor_manager=tor_manager)

        splash.close()
        window.show()

        exit_code = app.exec()

    except Exception as e:
        logger.error("Exception caught in main loop:")
        logger.error(traceback.format_exc())

        exc_type, exc_value, exc_tb = sys.exc_info()
        CrashHandler.handle_exception(exc_type, exc_value, exc_tb)

        exit_code = 1

    finally:
        logger.info("Main: Performing final cleanup.")
        shutdown_manager.shutdown()

    sys.exit(exit_code)

if __name__ == "__main__":
    main()