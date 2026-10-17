import shutil
from pathlib import Path

from app.core import settings
from app.core.logger import logger
from app.systems.download_system.utils.postprocess_handler import process_file

# Common YouTube/native original formats
ORIGINAL_FORMATS = {".webm", ".m4a", ".3gp", ".ts", ".mpd"}


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
    failures = []
    exports_dir = settings.EXPORTS_DIR
    logger.info(f"Scanning sandbox: {temp_dir}")
    for file in temp_dir.iterdir():
        if not file.is_file():
            continue
        destination = None
        try:
            original = is_original_format(file)
            folder = settings.ORIGINALS_DIR if original else exports_dir
            folder.mkdir(parents=True, exist_ok=True)
            destination = get_safe_destination(folder / file.name)
            file_type = "original" if original else "converted"
            shutil.move(str(file), str(destination))
            if not original and file.suffix.lower() not in {".srt", ".vtt", ".ass", ".lrc"}:
                processed = process_file(destination)
                if processed and processed != destination:
                    processed.replace(destination)
            moved[file] = {"dest": destination, "type": file_type}
            logger.info(f"Moved → {file.name} → {destination} [{file_type}]")
        except Exception as exc:
            failures.append(f"{file.name}: {exc}")
            logger.error(f"Failed to export {file.name}: {exc}")
    if failures:
        raise RuntimeError(
            "Could not save all downloaded files. Choose an accessible download folder in Folders. "
            f"Some files may already be saved; remaining files are in {temp_dir}.\n"
            + "\n".join(failures)
        )
    return moved
