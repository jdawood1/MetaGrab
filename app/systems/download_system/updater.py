"""Update the source-install downloader without changing the running Qt process."""

import json
import sys
import threading
from urllib.request import urlopen

from app.core import processes as subprocess

_UPDATE_LOCK = threading.Lock()
_CHECKED = False
_EXTRACTION_ERRORS = (
    "nsig extraction failed",
    "signature extraction failed",
    "the page needs to be reloaded",
    "unable to extract",
)


def is_extractor_failure(message):
    return any(marker in message.lower() for marker in _EXTRACTION_ERRORS)


def update_if_outdated():
    """Return (retry, explanation). Check once per app session; serialize updates."""
    global _CHECKED
    with _UPDATE_LOCK:
        if getattr(sys, "frozen", False):
            return False, "This bundled app needs an app update to update its downloader."
        if sys.prefix == sys.base_prefix:
            return False, "Automatic downloader updates require a virtual environment."
        if _CHECKED:
            return False, "Downloader update already checked this session."
        _CHECKED = True
        try:
            probe = subprocess.run(
                [sys.executable, "-m", "yt_dlp", "--version"],
                capture_output=True,
                text=True,
                timeout=20,
                check=True,
            )
            installed = probe.stdout.strip()
            with urlopen("https://pypi.org/pypi/yt-dlp/json", timeout=15) as response:
                latest = json.load(response)["info"]["version"]

            # yt-dlp stable versions are numeric date versions.
            def version(value):
                return tuple(int(part) for part in value.split("."))

            if version(installed) >= version(latest):
                return False, f"Downloader is current ({installed}); the failure needs another fix."
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "--isolated",
                    "install",
                    "--disable-pip-version-check",
                    "--no-input",
                    "--upgrade",
                    "--index-url",
                    "https://pypi.org/simple",
                    "yt-dlp[default]",
                ],
                capture_output=True,
                text=True,
                timeout=180,
            )
            if result.returncode:
                return (
                    False,
                    "Automatic downloader update failed. Check your network and installation.",
                )
            return True, f"Updated downloader from {installed} to {latest}; retrying once."
        except Exception as exc:
            return False, f"Could not check/update the downloader: {exc}"
