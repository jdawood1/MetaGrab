import requests
from PySide6.QtCore import QObject, QRunnable, Signal, Slot

from app.core import processes


class IPFetchWorkerSignals(QObject):
    result = Signal(str)
    error = Signal(str)


class PublicIPFetcher(QRunnable):
    """Worker to fetch public IP in the background thread."""

    def __init__(self):
        super().__init__()
        self.signals = IPFetchWorkerSignals()

    @Slot()
    def run(self):
        if processes.closing.is_set():
            return
        try:
            response = requests.get("https://api.ipify.org", timeout=5)
            public_ip = response.text.strip()
            self.signals.result.emit(public_ip)
        except Exception as e:
            self.signals.error.emit(str(e))
