import logging
import traceback
from PySide6.QtCore import QRunnable, Signal, QObject
from PySide6.QtWidgets import QApplication
from app.core import settings

# Global shutdown safety
active_tor_runnables = set()

class TorControlSignals(QObject):
    finished = Signal(bool, str)  # success, message


class TorControlRunnable(QRunnable):
    _latest_id = 0  # class-level counter to track the newest runnable

    def __init__(self, tor_manager, mode="start", exit_country=None, exit_label=None, bridge_enabled=None):
        super().__init__()
        self.tor_manager = tor_manager
        self.mode = mode  # "start", "stop", "switch", or "bridge"
        self.exit_country = exit_country
        self.exit_label = exit_label or "Auto"
        self.bridge_enabled = bridge_enabled
        self.signals = TorControlSignals()

        TorControlRunnable._latest_id += 1
        self._id = TorControlRunnable._latest_id  # instance ID

        active_tor_runnables.add(self)

    def run(self):
        try:
            if self.mode == "start":
                bridge_note = " + Bridge" if settings.BRIDGE_ENABLED else ""
                self._emit_safe(False, f"🟡 Connecting via {self.exit_label}{bridge_note}...")
                self.tor_manager.start(exit_country=self.exit_country)
                self._finalize_status()

            elif self.mode == "stop":
                self.tor_manager.stop()
                self._emit_safe(True, "Tor: OFF")

            elif self.mode == "switch":
                if not settings.TOR_ENABLED:
                    self._emit_safe(True, "Tor: OFF")
                    return
                bridge_note = " + Bridge" if settings.BRIDGE_ENABLED else ""
                self._emit_safe(False, f"🔆 Switching to {self.exit_label}{bridge_note}...")
                self.tor_manager.stop()
                self.tor_manager.start(exit_country=self.exit_country)
                self._finalize_status()

            elif self.mode == "bridge":
                if not settings.TOR_ENABLED:
                    self._emit_safe(True, "Tor: OFF")
                    return
                settings.BRIDGE_ENABLED = self.bridge_enabled
                state_label = "Enabling" if self.bridge_enabled else "Disabling"
                self._emit_safe(False, f"🌐 {state_label} Bridge Mode...")
                self.tor_manager.stop()
                self.tor_manager.start(exit_country=self.exit_country)
                self._finalize_status()

            else:
                raise ValueError(f"Invalid Tor control mode: {self.mode}")

        except Exception as e:
            logging.warning(f"Tor {self.mode} failed:\n" + traceback.format_exc())
            self._emit_safe(False, f"⚠️ Tor {self.mode} error: {str(e)}")

        finally:
            active_tor_runnables.discard(self)

    def _finalize_status(self):
        if self._id < TorControlRunnable._latest_id:
            return  # Skip if this runnable is outdated

        if not settings.TOR_ENABLED:
            self.tor_manager.stop()
            self._emit_safe(True, "Tor: OFF")
        else:
            bridge_note = " + Bridge" if settings.BRIDGE_ENABLED else ""
            self._emit_safe(True, f"🟢 Tor: ON ({self.exit_label}{bridge_note})")

    def _emit_safe(self, *args):
        """Safely emit signals if the app and QObject are still alive."""
        if QApplication.instance() is None:
            return
        try:
            self.signals.finished.emit(*args)
        except RuntimeError:
            # QObject deleted — app is shutting down
            pass