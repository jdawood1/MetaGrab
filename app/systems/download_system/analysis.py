"""Source metadata and a bounded audio sample; independent of the Qt interface."""

import json
import tempfile
from pathlib import Path

from yt_dlp.utils import download_range_func

from app.core import processes as subprocess
from app.systems.download_system.anizone import create_downloader
from app.systems.download_system.selections import media_choices


def duration_text(value):
    if value is None:
        return "Unknown"
    seconds = int(value)
    return f"{seconds // 3600:02}:{seconds // 60 % 60:02}:{seconds % 60:02}"


def metadata_report(info):
    formats = info.get("formats") or [info]
    lines = [
        str(info.get("title") or "Untitled media"),
        f"Source: {info.get('webpage_url') or info.get('original_url') or 'Unknown'}",
        f"Extractor: {info.get('extractor') or 'Unknown'}",
        f"Duration: {duration_text(info.get('duration'))}",
        f"Uploader: {info.get('uploader') or info.get('channel') or 'Unknown'}",
        f"Live: {'Yes' if info.get('is_live') else 'No'}",
        "",
        "SOURCE FORMATS",
        "These are the site's available streams, not necessarily the original uploaded file.",
    ]
    languages = sorted({str(f["language"]) for f in formats if f.get("language")})
    lines.append("Audio/stream languages: " + (", ".join(languages) or "Not supplied"))
    subtitles = sorted(set(info.get("subtitles") or {}) | set(info.get("automatic_captions") or {}))
    lines.append("Subtitle languages: " + (", ".join(subtitles) or "Not supplied"))
    lines += [
        "",
        "ID | container | video codec / resolution / fps | audio codec / rate / channels / language | size",
    ]
    for f in formats:
        video = f.get("vcodec") or "unknown"
        audio = f.get("acodec") or "unknown"
        resolution = f.get("resolution") or (
            f"{f.get('width', '?')}x{f.get('height', '?')}" if f.get("height") else "—"
        )
        size = f.get("filesize") or f.get("filesize_approx")
        size_text = f"{size / 1024**2:.1f} MiB" if size else "Unknown"
        if size and not f.get("filesize"):
            size_text += " (estimated)"
        lines.append(
            f"{f.get('format_id', '?')} | {f.get('ext', '?')} ({f.get('protocol', '?')}) | "
            f"{video} / {resolution} / {f.get('fps') or '—'} | "
            f"{audio} / {f.get('asr') or '—'} Hz / {f.get('audio_channels') or '—'} ch / "
            f"{f.get('language') or f.get('format_note') or '—'} | {size_text}"
        )
    return "\n".join(lines)


def find_sample(info, downloader, directory):
    candidates = [info.get("filepath"), info.get("_filename")]
    candidates += [entry.get("filepath") for entry in info.get("requested_downloads") or []]
    candidates.append(downloader.prepare_filename(info))
    root = Path(directory).resolve()
    for name in candidates:
        if not name:
            continue
        path = Path(name).resolve()
        if path.is_relative_to(root) and path.is_file() and path.stat().st_size:
            return path
    raise RuntimeError("The downloader did not produce the reported sample file.")


def loudness_metrics(stderr):
    for start in reversed([i for i, char in enumerate(stderr) if char == "{"]):
        try:
            metrics, _ = json.JSONDecoder().raw_decode(stderr[start:])
        except ValueError:
            continue
        if isinstance(metrics, dict) and "input_i" in metrics:
            return metrics
    raise RuntimeError("FFmpeg returned no loudness measurements.")


def analyze_media(url, tool_options, privacy_options=None, return_details=False):
    base = {
        **(privacy_options or {}),
        **tool_options,
        "quiet": True,
        "noplaylist": True,
        "socket_timeout": 20,
        "retries": 1,
    }
    with create_downloader({**base, "skip_download": True}) as downloader:
        info = downloader.extract_info(url, download=False)
    if not info or info.get("_type") == "playlist":
        raise RuntimeError("Analyze requires a single playable media URL.")

    def finish(text):
        return {"report": text, "choices": media_choices(info)} if return_details else text

    report = metadata_report(info)
    if info.get("is_live"):
        return finish(report + "\n\nLOUDNESS\nSkipped for a live stream.")
    try:
        with tempfile.TemporaryDirectory(prefix="metagrab-analysis-") as directory:
            options = {
                **base,
                "format": "bestaudio/best",
                "outtmpl": str(Path(directory) / "sample.%(ext)s"),
                "download_ranges": download_range_func(None, [(0, 15)]),
                "external_downloader": "ffmpeg",
                "overwrites": True,
            }
            with create_downloader(options) as downloader:
                sample_info = downloader.extract_info(url, download=True)
                sample = find_sample(sample_info, downloader, directory)
            ffmpeg = str(Path(tool_options["ffmpeg_location"]) / "ffmpeg")
            result = subprocess.run(
                [
                    ffmpeg,
                    "-hide_banner",
                    "-nostdin",
                    "-i",
                    str(sample),
                    "-t",
                    "15",
                    "-map",
                    "0:a:0",
                    "-vn",
                    "-af",
                    "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json",
                    "-f",
                    "null",
                    "-",
                ],
                capture_output=True,
                text=True,
                timeout=45,
            )
            if result.returncode:
                raise RuntimeError(
                    "FFmpeg could not measure the sample's audio. " + result.stderr[-800:]
                )
            metrics = loudness_metrics(result.stderr)
            report += (
                "\n\nLOUDNESS — first up to 15 seconds (not a whole-program measurement)"
                f"\nSample source format: {sample_info.get('format_id', '?')} / {sample_info.get('ext', '?')}"
                f"\nIntegrated loudness: {metrics['input_i']} LUFS"
                f"\nTrue peak: {metrics.get('input_tp', 'Unknown')} dBTP"
                f"\nLoudness range: {metrics.get('input_lra', 'Unknown')} LU"
                "\nShort samples may not represent the rest of the program."
            )
    except Exception as exc:
        report += f"\n\nLOUDNESS\nUnavailable: {exc}\nSource metadata above is still available."
    return finish(report)
