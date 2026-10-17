import unittest

from yt_dlp.utils import ExtractorError

from app.systems.download_system.anizone import AniZoneIE, create_downloader, player_config


class AniZoneTests(unittest.TestCase):
    def test_encoded_player(self):
        page = r"""<div x-data="vidstackPlayer(JSON.parse('{\u0022src\u0022:\u0022https:\/\/cdn.example\/master.m3u8\u0022}'))"></div>"""
        self.assertEqual(player_config(page)["src"], "https://cdn.example/master.m3u8")

    def test_missing_player_has_clear_error(self):
        with self.assertRaisesRegex(ExtractorError, "player source was not found"):
            player_config('<iframe src="https://ads.example/"></iframe>')

    def test_non_web_source_is_rejected(self):
        page = """<div x-data="vidstackPlayer(JSON.parse('{&quot;src&quot;:&quot;file:///tmp/master.m3u8&quot;}'))"></div>"""
        with self.assertRaises(ExtractorError):
            player_config(page)

    def test_invalid_json_is_rejected(self):
        with self.assertRaises(ExtractorError):
            player_config("""<div x-data="vidstackPlayer(JSON.parse('invalid'))"></div>""")

    def test_url_scope(self):
        self.assertTrue(AniZoneIE.suitable("https://anizone.to/anime/vpdxs6e5/1"))
        self.assertFalse(AniZoneIE.suitable("https://anizone.to.example.org/anime/a/1"))
        self.assertFalse(AniZoneIE.suitable("https://youtube.com/watch?v=test"))

    def test_custom_extractor_precedes_generic(self):
        with create_downloader({"quiet": True}) as downloader:
            extractors = list(downloader._ies)
            self.assertLess(extractors.index("AniZone"), extractors.index("Generic"))
            self.assertIn("Youtube", extractors)
