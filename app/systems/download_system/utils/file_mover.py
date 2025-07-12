from pathlib import Path
import shutil
from app.core import settings
from app.core.logger import logger
from app.systems.download_system.utils.postprocess_handler import process_file

# Common YouTube/native original formats
ORIGINAL_FORMATS = {'.webm', '.m4a', '.3gp', '.ts', '.mpd'}

def is_original_format(file_path: Path) -> bool:
    """Return True if a file is a known original/raw format."""
    ext = file_path.suffix.lower()
    return ext in ORIGINAL_FORMATS

def get_safe_destination(dest: Path) -> Path:
    """Append a number to the filename if a file with the same name exists."""
    if not dest.exists():
        return dest

    base = dest.stem
    ext = dest.suffix
    parent = dest.parent

    i = 1
    while True:
        candidate = parent / f"{base} ({i}){ext}"
        if not candidate.exists():
            return candidate
        i += 1

def move_downloaded_files(temp_dir: Path) -> dict:
    """
    Move files from yt_dlp sandbox:
    - Originals (native formats) → ORIGINALS_DIR
    - Others → EXPORTS_DIR (assumed converted)
    - Applies post-processing if enabled (strip metadata / normalize)

    Returns:
        dict: {source_file: {'dest': Path, 'type': 'original' | 'converted'}}
    """
    moved = {}

    logger.info(f"Scanning sandbox: {temp_dir}")
    for file in temp_dir.iterdir():
        if not file.is_file():
            continue

        if is_original_format(file):
            destination = get_safe_destination(settings.ORIGINALS_DIR / file.name)
            file_type = 'original'
        else:
            destination = get_safe_destination(settings.EXPORTS_DIR / file.name)
            file_type = 'converted'

        try:
            shutil.move(str(file), str(destination))
            logger.info(f"Moved → {file.name} → {destination} [{file_type}]")

            # Postprocess converted files only
            if file_type == 'converted':
                processed = process_file(destination)
                if processed and processed != destination:
                    # Replace the original with a processed version
                    destination.unlink()
                    processed.rename(destination)
                    logger.info(f"Replaced with processed file: {destination.name}")

            moved[file] = {'dest': destination, 'type': file_type}
        except Exception as e:
            logger.error(f"Failed to move {file.name} → {destination}: {e}")

    return moved