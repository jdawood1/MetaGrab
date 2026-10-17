import re
from typing import Optional


class AudioNormalizePresets:
    """Reusable constants for normalization presets."""

    PRESETS = {
        "Apple Podcast": {"I": -16, "TP": -1.5, "LRA": 9},
        "Streaming (Spotify)": {"I": -14, "TP": -2.0, "LRA": 10},
        "YouTube": {"I": -13, "TP": -1.5, "LRA": 11},
        "Broadcast Standard": {"I": -23, "TP": -2.0, "LRA": 7},
        "Audiobooks": {"I": -18, "TP": -3.0, "LRA": 8},
        "CD Mastering": {"I": -11, "TP": -0.1, "LRA": 7},
        "Max Loudness": {"I": -9, "TP": -0.1, "LRA": 6},
    }

    PRESET_LABELS = {
        "Apple Podcast": "Podcast-ready (Apple)",
        "Streaming (Spotify)": "Streaming Optimized (Spotify)",
        "YouTube": "Loudness Standard (YouTube)",
        "Broadcast Standard": "Broadcast Safe",
        "Audiobooks": "Narration / Audiobook",
        "CD Mastering": "CD / Studio Mastering",
        "Max Loudness": "Maximum Volume (Aggressive)",
    }

    @classmethod
    def get_preset_filter(cls, key: str) -> Optional[str]:
        preset = cls.PRESETS.get(key)
        if not preset:
            return None
        return f"loudnorm=I={preset['I']}:TP={preset['TP']}:LRA={preset['LRA']}:print_format=json"


class AudioFormatPresets:
    """Reusable constants for audio conversion formats and options."""

    LOSSY_FORMATS = {"mp3", "aac", "ogg", "m4a", "opus", "webm", "amr", "wma"}
    LOSSLESS_FORMATS = {"flac", "wav", "aiff", "alac"}
    FORMATS = [
        "mp3",
        "aac",
        "flac",
        "opus",
        "wav",
        "m4a",
        "ogg",
        "webm",
        "alac",
        "aiff",
        "amr",
        "wma",
    ]
    CODEC_MAP = {
        "mp3": "libmp3lame",
        "aac": "aac",
        "flac": "flac",
        "opus": "libopus",
        "m4a": "aac",
        "ogg": "libvorbis",
        "wav": "pcm_s16le",
        "webm": "libopus",
        "alac": "alac",
        "aiff": "pcm_s16be",
        "amr": "libopencore_amrnb",
        "wma": "wmav2",
    }


# ---------------------------------------------
# Helper for unified FFmpeg single-pass command
# ---------------------------------------------


def build_ffmpeg_command(
    input_path: str,
    output_path: str,
    crop_start: Optional[float] = None,
    crop_end: Optional[float] = None,
    normalize_filter: Optional[str] = None,
    codec: Optional[str] = "libmp3lame",
    bitrate: Optional[str] = "192k",
    sample_rate: Optional[int] = None,
    channels: Optional[int] = None,
) -> list[str]:
    """Build a unified FFmpeg command that applies crop, normalize, and conversion in one pass."""
    cmd = ["ffmpeg", "-y"]

    # Crop
    if crop_start is not None:
        cmd += ["-ss", str(crop_start)]
    if crop_end is not None:
        cmd += ["-to", str(crop_end)]

    cmd += ["-i", input_path]

    # Audio filters
    filters = []
    if normalize_filter:
        filters.append(normalize_filter)
    if filters:
        cmd += ["-af", ",".join(filters)]

    # Codec
    if codec:
        cmd += ["-c:a", codec]

    # Bitrate for lossy formats
    lossy_codecs = {"libmp3lame", "aac", "libvorbis", "libopus", "wmav2", "libopencore_amrnb"}
    if bitrate and codec in lossy_codecs:
        if not bitrate.endswith("k"):
            bitrate += "k"
        cmd += ["-b:a", bitrate]

    # Sample rate and channels
    if sample_rate:
        cmd += ["-ar", str(sample_rate)]
    if channels:
        cmd += ["-ac", str(channels)]

    cmd.append(output_path)
    return cmd


# ---------------------------------------------
# Parse human-readable time formats into seconds.
# ---------------------------------------------


def parse_time_input(time_str: str) -> float:
    """
    Parse human-readable time formats into seconds.

    Supported:
    - "1h 2m 3s"
    - "2m30.5s"
    - "90" (interpreted as 90 seconds)
    - "1:23" => 1m23s
    - "1:02:03.5" => 1h2m3.5s
    """
    if not time_str.strip():
        return 0.0

    time_str = time_str.strip().lower()

    # Match "1h 2m 3.5s" style
    match = re.match(r"^(?:(\d+)h)?\s*(?:(\d+)m)?\s*(?:(\d+(?:\.\d+)?)s?)?$", time_str)
    if match:
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = float(match.group(3) or 0)
        return hours * 3600 + minutes * 60 + seconds

    # Match colon-separated formats like "1:02:03.5"
    parts = time_str.split(":")
    try:
        parts = [float(p) for p in parts]
    except ValueError:
        raise ValueError(f"Invalid time format: {time_str!r}")

    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    elif len(parts) == 2:
        return parts[0] * 60 + parts[1]
    elif len(parts) == 1:
        return parts[0]
    else:
        raise ValueError(f"Invalid time format: {time_str!r}")
