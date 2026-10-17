import unittest

from app.systems.download_system.anizone import add_player_subtitles
from app.systems.download_system.selections import apply_selections, media_choices


class SelectionTests(unittest.TestCase):
    def test_explicit_audio_has_no_wrong_language_fallback(self):
        options = apply_selections({"format": "bestvideo+bestaudio/best"}, audio="en")
        self.assertEqual(options["format"], "bestvideo+bestaudio[language=en]/best[language=en]")

    def test_exact_regional_track_has_no_fallback(self):
        options = apply_selections(
            {"format": "bestvideo+bestaudio/best"}, audio="id:hls-group_audio-Spanish__Spain_"
        )
        self.assertEqual(options["format"], "bestvideo+hls-group_audio-Spanish__Spain_")

    def test_audio_only_preserves_container_filter(self):
        options = apply_selections({"format": "bestaudio[ext=m4a]/bestaudio"}, audio="ja")
        self.assertEqual(
            options["format"], "bestaudio[language=ja][ext=m4a]/bestaudio[language=ja]"
        )

    def test_embedding_preserves_existing_processors(self):
        options = apply_selections(
            {"postprocessors": [{"key": "Example"}]}, caption="en-english", embed=True
        )
        self.assertEqual(options["merge_output_format"], "mkv")
        self.assertEqual(options["postprocessors"][-1]["key"], "FFmpegEmbedSubtitle")
        self.assertTrue(options["writesubtitles"])
        self.assertEqual(options["subtitleslangs"], ["en-english"])

    def test_sidecar_does_not_change_container(self):
        options = apply_selections({"merge_output_format": "mp4"}, caption="en")
        self.assertEqual(options["merge_output_format"], "mp4")
        self.assertNotIn("postprocessors", options)

    def test_player_captions_keep_variants_separate(self):
        subtitles = add_player_subtitles(
            {},
            {
                "subtitles": [
                    {"file": "https://cdn.example/en.srt", "language": "en", "title": "English"},
                    {
                        "file": "https://cdn.example/forced.srt",
                        "language": "en",
                        "title": "English (Forced)",
                    },
                    {"file": "file:///tmp/no.srt", "language": "en"},
                ]
            },
        )
        self.assertEqual(set(subtitles), {"en-english", "en-english-forced"})
        choices = media_choices({"subtitles": subtitles})
        self.assertEqual(len(choices["captions"]), 2)

    def test_rejects_selector_injection(self):
        with self.assertRaises(ValueError):
            apply_selections({}, audio="en]/best")
