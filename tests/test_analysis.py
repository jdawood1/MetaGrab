import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from app.systems.download_system.analysis import (
    analyze_media,
    find_sample,
    loudness_metrics,
    metadata_report,
)


class AnalysisTests(unittest.TestCase):
    def test_mp4_audio_sample_is_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            sample = Path(directory) / "sample.mp4"
            sample.write_bytes(b"audio")
            downloader = Mock()
            downloader.prepare_filename.return_value = str(sample)
            self.assertEqual(
                find_sample(
                    {"requested_downloads": [{"filepath": str(sample)}]}, downloader, directory
                ),
                sample.resolve(),
            )

    def test_nonexistent_sample_is_not_guessed(self):
        with tempfile.TemporaryDirectory() as directory:
            downloader = Mock()
            downloader.prepare_filename.return_value = str(Path(directory) / "missing.mp4")
            with self.assertRaisesRegex(RuntimeError, "reported sample"):
                find_sample({}, downloader, directory)

    def test_report_handles_unknown_metadata(self):
        report = metadata_report(
            {
                "formats": [
                    {
                        "format_id": "audio",
                        "ext": "mp4",
                        "vcodec": "none",
                        "acodec": "aac",
                        "language": "ja",
                    }
                ]
            }
        )
        self.assertIn("Duration: Unknown", report)
        self.assertIn("ja", report)
        self.assertIn("not necessarily the original", report)

    def test_reads_ffmpeg_loudness_json(self):
        metrics = loudness_metrics(
            'noise\n[filter]\n{"input_i":"-18.2","input_tp":"-1.2","input_lra":"4.0"}\n'
        )
        self.assertEqual(metrics["input_i"], "-18.2")

    @patch("app.systems.download_system.analysis.create_downloader")
    def test_sample_failure_keeps_metadata(self, factory):
        downloader = factory.return_value.__enter__.return_value
        downloader.extract_info.side_effect = [
            {"title": "Episode", "formats": []},
            RuntimeError("403"),
        ]
        report = analyze_media("https://example.org/video", {"ffmpeg_location": "/tools"})
        self.assertIn("Episode", report)
        self.assertIn("Unavailable: 403", report)
        options = factory.call_args.args[0]
        self.assertEqual(options["external_downloader"], "ffmpeg")
        self.assertEqual(
            list(options["download_ranges"]({}, None)), [{"start_time": 0, "end_time": 15}]
        )

    @patch("app.systems.download_system.analysis.create_downloader")
    def test_live_stream_does_not_download_sample(self, factory):
        downloader = factory.return_value.__enter__.return_value
        downloader.extract_info.return_value = {"title": "Live", "is_live": True}
        self.assertIn("Skipped for a live stream", analyze_media("https://example.org/live", {}))
        self.assertEqual(factory.call_count, 1)
