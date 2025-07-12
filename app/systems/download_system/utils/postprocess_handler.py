import subprocess
from pathlib import Path
from app.core import settings
from app.core.logger import logger

def process_file(file_path: Path) -> Path | None:
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = file_path.suffix.lower()
    is_mp3 = ext == ".mp3"

    strip_meta = settings.STRIP_METADATA
    normalize = settings.NORMALIZE_AUDIO

    if not strip_meta and not (normalize and is_mp3):
        logger.debug(f"Skipping {file_path.name} — no processing needed")
        return None

    if normalize and not is_mp3:
        logger.warning(f"Normalization is only supported for MP3 files. Skipping normalization for: {file_path.name}")
        if not strip_meta:
            return None

    output_path = file_path.with_name(file_path.stem + "_processed" + file_path.suffix)

    cmd = ["ffmpeg", "-y", "-i", str(file_path)]

    if normalize and is_mp3:
        cmd += ["-af", "loudnorm=I=-9:TP=-0.1:LRA=5"]

    if strip_meta:
        cmd += ["-map_metadata", "-1"]

    if normalize and is_mp3:
        cmd += ["-c:a", "libmp3lame", "-b:a", "192k"]
    else:
        cmd += ["-c", "copy"]

    cmd.append(str(output_path))

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logger.info(f"File processed → {output_path.name}")
        return output_path
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ FFmpeg failed on {file_path.name}")
        raise