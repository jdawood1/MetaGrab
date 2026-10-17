"""AniZone's Vidstack player exposes its HLS source as encoded JSON."""

import json
import re
from html.parser import HTMLParser
from urllib.parse import urlparse

from yt_dlp import YoutubeDL
from yt_dlp.extractor.common import InfoExtractor
from yt_dlp.utils import ExtractorError, js_to_json


class PlayerParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.configs = []

    def handle_starttag(self, tag, attrs):
        value = dict(attrs).get("x-data", "")
        if "vidstackPlayer(" not in value:
            return
        match = re.search(r"JSON\.parse\(\s*('(?:\\.|[^'\\])*')\s*\)", value)
        if not match:
            return
        try:
            config = json.loads(json.loads(js_to_json(match.group(1))))
        except (ValueError, TypeError):
            return
        if isinstance(config, dict):
            self.configs.append(config)


def player_config(webpage):
    parser = PlayerParser()
    parser.feed(webpage)
    for config in parser.configs:
        source = config.get("src", "")
        if not isinstance(source, str):
            continue
        parsed = urlparse(source)
        if parsed.scheme in ("http", "https") and parsed.hostname and parsed.path.endswith(".m3u8"):
            return config
    raise ExtractorError(
        "AniZone's supported player source was not found. The page may have changed.",
        expected=True,
    )


def add_player_subtitles(subtitles, config):
    for track in config.get("subtitles") or []:
        source = track.get("file", "")
        parsed = urlparse(source)
        if parsed.scheme not in ("https", "http") or not parsed.hostname:
            continue
        language = track.get("language") or "und"
        # Distinguish variants/forced tracks instead of downloading them all.
        title = track.get("title") or language
        key = language + "-" + re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
        entry = {"url": source, "ext": track.get("format") or "srt", "name": title}
        subtitles.setdefault(key, []).append(entry)
    return subtitles


class AniZoneIE(InfoExtractor):
    IE_NAME = "anizone"
    _VALID_URL = (
        r"https?://(?:www\.)?anizone\.to/anime/(?P<series>[\w-]+)/(?P<id>[\w-]+)(?:[/?#]|$)"
    )

    def _real_extract(self, url):
        match = self._match_valid_url(url)
        video_id = match.group("series") + "-" + match.group("id")
        webpage = self._download_webpage(url, video_id)
        config = player_config(webpage)
        headers = {"Referer": url}
        formats, subtitles = self._extract_m3u8_formats_and_subtitles(
            config["src"],
            video_id,
            "mp4",
            m3u8_id="hls",
            headers=headers,
        )
        subtitles = add_player_subtitles(subtitles, config)
        return {
            "id": video_id,
            "title": self._html_search_meta(["og:title", "twitter:title"], webpage, default=None)
            or self._html_search_regex(
                r"<title[^>]*>(.*?)</title>", webpage, "title", default=video_id
            ),
            "formats": formats,
            "subtitles": subtitles,
            "http_headers": headers,
            "thumbnail": config.get("snapshot"),
        }


def create_downloader(options):
    downloader = YoutubeDL(options, auto_init=False)
    downloader.add_info_extractor(AniZoneIE())
    downloader.add_default_info_extractors()
    return downloader
