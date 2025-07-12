# app/systems/download_system/utils/header_spoofer.py

import random

class HeaderSpoofer:
    """Generates randomized spoofed headers for privacy-focused downloading."""

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 15_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.2 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPad; CPU OS 13_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Linux; Android 10; SM-G970F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android 11; SM-G998U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0"
    ]

    REFERERS = [
        "https://www.google.com/",
        "https://www.bing.com/",
        "https://www.yahoo.com/",
        "https://www.duckduckgo.com/",
        "https://www.youtube.com/",
        "https://news.ycombinator.com/",
        "https://reddit.com/",
        "https://www.facebook.com/",
        "https://twitter.com/",
        "https://www.linkedin.com/"
    ]

    ACCEPT_LANGUAGES = [
        "en-US,en;q=0.9",
        "en-GB,en;q=0.8",
        "fr-FR,fr;q=0.9,en;q=0.7",
        "de-DE,de;q=0.9,en;q=0.8",
        "es-ES,es;q=0.9,en;q=0.7",
        "it-IT,it;q=0.9,en;q=0.8",
        "pt-BR,pt;q=0.9,en;q=0.8",
        "zh-CN,zh;q=0.9,en;q=0.7",
        "ja-JP,ja;q=0.9,en;q=0.7",
        "ru-RU,ru;q=0.9,en;q=0.7"
    ]

    SEC_CH_UA = [
        '"Not.A/Brand";v="8", "Chromium";v="114"',
        '"Google Chrome";v="110", "Chromium";v="110"',
        '"Microsoft Edge";v="109", "Chromium";v="109"',
        '"Opera";v="97", "Chromium";v="97"',
        '"Brave";v="112", "Chromium";v="112"',
        '"Vivaldi";v="108", "Chromium";v="108"',
        '"Safari";v="15", "WebKit";v="605"',
        '"Firefox";v="102", "Gecko";v="20100101"',
        '"Yandex";v="22", "Chromium";v="104"',
        '"Samsung Internet";v="18", "Chromium";v="103"'
    ]

    SEC_CH_UA_PLATFORM = [
        '"Windows"', '"macOS"', '"Linux"', '"Android"', '"iOS"',
        '"ChromeOS"', '"Ubuntu"', '"FreeBSD"', '"Debian"', '"Fedora"'
    ]

    def generate_headers(self):
        return {
            "User-Agent": random.choice(self.USER_AGENTS),
            "Referer": random.choice(self.REFERERS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": random.choice(self.ACCEPT_LANGUAGES),
            "DNT": "1",
            "Connection": "keep-alive",
            "Sec-CH-UA": random.choice(self.SEC_CH_UA),
            "Sec-CH-UA-Platform": random.choice(self.SEC_CH_UA_PLATFORM),
            "Sec-CH-UA-Mobile": random.choice(["?0", "?1"]),
        }