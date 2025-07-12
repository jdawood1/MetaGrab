from pathlib import Path
from mutagen import File as MutagenFile
from collections import defaultdict

AUDIO_EXTENSIONS = {'.mp3', '.flac', '.wav', '.m4a', '.aac', '.ogg'}


def format_duration(seconds: float) -> str:
    minutes = int(seconds) // 60
    secs = int(seconds) % 60
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours} hr {mins} min {secs} sec"


def format_size(bytes_: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_ < 1024.0:
            return f"{bytes_:3.1f} {unit}"
        bytes_ /= 1024.0
    return f"{bytes_:3.1f} TB"


def summarize_folder(folder: Path, with_emojis: bool = True) -> str:
    if not folder.exists() or not folder.is_dir():
        return "Folder not found." if with_emojis else "Folder not found."

    total_seconds = 0
    total_files = 0
    total_size = 0
    total_bitrate = 0
    extension_counts = defaultdict(int)

    for file in folder.rglob("*"):
        if file.is_file() and file.suffix.lower() in AUDIO_EXTENSIONS:
            try:
                audio = MutagenFile(file)
                if audio and audio.info:
                    total_seconds += int(audio.info.length)
                    total_files += 1
                    total_size += file.stat().st_size
                    ext = file.suffix.lower()
                    extension_counts[ext] += 1
                    if hasattr(audio.info, "bitrate") and audio.info.bitrate:
                        total_bitrate += audio.info.bitrate
            except Exception:
                continue

    if total_files == 0:
        return "No audio files found." if with_emojis else "No audio files found."

    duration_text = format_duration(total_seconds)
    avg_duration_text = format_duration(total_seconds / total_files)
    avg_bitrate_kbps = int(total_bitrate / total_files / 1000) if total_bitrate else "—"
    size_text = format_size(total_size)
    file_word = "file" if total_files == 1 else "files"

    # Determine the most common format
    most_common_ext = max(extension_counts.items(), key=lambda x: x[1])[0][1:].upper()

    return f"""
        <div style="line-height: 1.6; text-align: left;">
            <b>Audio Folder Summary</b><br>
            <span><b>{total_files}</b> audio {file_word}</span><br>
            <span><b>Duration:</b> {duration_text}</span><br>
            <span><b>Size:</b> {size_text}</span><br>
            <span><b>Avg. Duration:</b> {avg_duration_text}</span><br>
            <span><b>Avg. Bitrate:</b> {avg_bitrate_kbps} kbps</span><br>
            <span><b>Format:</b> Mostly {most_common_ext}</span>
        </div>
    """