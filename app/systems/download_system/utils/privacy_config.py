from app.core import settings
from app.core.logger import logger


def get_privacy_options():
    """
    Return yt_dlp options that enhance privacy:
    - Extractor-managed default headers for compatibility
    - SOCKS proxy (e.g., via Tor if enabled)
    """
    privacy_opts = {}

    if settings.TOR_ENABLED:
        logger.info("🛡️ Tor enabled: routing yt_dlp through SOCKS5h proxy.")
        privacy_opts["proxy"] = "socks5h://127.0.0.1:9050"
    else:
        logger.debug("Tor not enabled: using downloader default headers.")

    return privacy_opts
