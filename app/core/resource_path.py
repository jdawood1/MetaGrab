import sys
from pathlib import Path


class AssetNotFoundError(Exception):
    """Custom exception for missing assets."""

    pass


# Determine the project root based on runtime context
if getattr(sys, "frozen", False):
    # When running as a frozen/packaged app (e.g., with PyInstaller)
    PROJECT_ROOT = Path(sys._MEIPASS)
else:
    # When running as a normal script, assume the project root is two levels up
    PROJECT_ROOT = Path(__file__).resolve().parents[2]


def resource_path(relative_path: str) -> str:
    """
    Get an absolute path to a resource relative to the project root.

    Args:
        relative_path (str): Path relative to the project root (e.g., 'assets/logo.png').

    Returns:
        str: Absolute path as a string.

    Raises:
        AssetNotFoundError: If the file does not exist.
    """
    full_path = PROJECT_ROOT / relative_path

    if not full_path.exists():
        raise AssetNotFoundError(f"Asset not found: {full_path}")

    return str(full_path)
