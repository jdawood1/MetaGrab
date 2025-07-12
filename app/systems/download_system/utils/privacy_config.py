from app.systems.download_system.utils.header_spoofer import HeaderSpoofer
from app.core.logger import logger
from app.core import settings

def get_privacy_options():
    """
    Return yt_dlp options that enhance privacy:
    - Spoofed headers (user-agent, referer, etc.)
    - SOCKS proxy (e.g., via Tor if enabled)
    """
    headers = HeaderSpoofer().generate_headers()

    privacy_opts = {
        'http_headers': headers
    }

    if settings.TOR_ENABLED:
        logger.info("🛡️ Tor enabled: routing yt_dlp through SOCKS5h proxy.")
        privacy_opts['proxy'] = 'socks5h://127.0.0.1:9050'
    else:
        logger.debug("Tor not enabled: using spoofed headers only.")

    return privacy_opts