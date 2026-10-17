"""Build MetaGrab with the isolated, locked macOS build environment."""

import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
BUILD_ENV = PROJECT_ROOT / ".venv-build"
BUILD_PYTHON = BUILD_ENV / "bin" / "python"
LOCK_FILE = PROJECT_ROOT / "requirements-build.lock"
SPEC_FILE = PROJECT_ROOT / "MetaGrab.spec"


def build_environment():
    # Do not inherit IDE helper paths, interpreter overrides, or an activated venv.
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("PYTHON", "PYCHARM", "PYDEVD", "JETBRAINS", "IDEA_"))
        and key not in {"VIRTUAL_ENV", "VIRTUAL_ENV_PROMPT", "__PYVENV_LAUNCHER__"}
    }
    environment.update(
        PYINSTALLER_CONFIG_DIR=str(PROJECT_ROOT / "build/cache"),
        PYTHONDONTWRITEBYTECODE="1",
        PYTHONNOUSERSITE="1",
    )
    return environment


def run(command):
    subprocess.run(command, cwd=PROJECT_ROOT, check=True, env=build_environment())


def setup_environment():
    if sys.version_info[:2] != (3, 11):
        raise RuntimeError("Use Python 3.11 to create this build environment.")
    if not LOCK_FILE.is_file():
        raise RuntimeError("Missing requirements-build.lock; restore it from Git.")
    if not BUILD_PYTHON.exists():
        run([sys.executable, "-m", "venv", str(BUILD_ENV)])
    run([str(BUILD_PYTHON), "-m", "pip", "install", "--requirement", str(LOCK_FILE)])


def check_environment():
    if not BUILD_PYTHON.is_file():
        raise RuntimeError("Build environment missing. Run: python3.11 build.py --setup")
    for name in (
        "MetaGrab.spec",
        "requirements-build.lock",
        "main.py",
        "assets/icon.icns",
        "app/styles/dark.qss",
        "app/styles/light.qss",
        "app/styles/style.qss",
        "app/systems/download_system/analysis.py",
        "app/systems/download_system/analysis_runner.py",
        "app/systems/download_system/selections.py",
    ):
        if not (PROJECT_ROOT / name).is_file():
            raise RuntimeError(f"Required build input missing: {name}")
    # Inspect the exact interpreter used for packaging, not a tool elsewhere on PATH.
    probe = """import importlib.metadata as m
import pathlib, sys
from packaging.requirements import Requirement
assert sys.version_info[:2] == (3, 11), "Build environment must use Python 3.11"
lines = []
for filename in sys.argv[1:]:
    lines.extend(pathlib.Path(filename).read_text().splitlines())
for line in lines:
    if not line.strip() or line.startswith("#"):
        continue
    req = Requirement(line)
    if req.marker and not req.marker.evaluate():
        continue
    installed = m.version(req.name)
    assert req.specifier.contains(installed), f"{req.name}: installed {installed}, expected {req.specifier}"
import PyInstaller, PIL, PySide6, yt_dlp, yt_dlp_ejs
print("Pinned build environment verified.")
"""
    run(
        [
            str(BUILD_PYTHON),
            "-B",
            "-c",
            probe,
            str(LOCK_FILE),
            str(PROJECT_ROOT / "requirements.txt"),
            str(PROJECT_ROOT / "requirements-build.txt"),
        ]
    )
    run([str(BUILD_PYTHON), "-m", "pip", "check"])


def build():
    run(
        [
            str(BUILD_PYTHON),
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--clean",
            "--distpath",
            str(PROJECT_ROOT / "dist"),
            "--workpath",
            str(PROJECT_ROOT / "build"),
            str(SPEC_FILE),
        ]
    )
    app = PROJECT_ROOT / "dist" / "MetaGrab.app"
    if not (app / "Contents/MacOS/MetaGrab").is_file():
        raise RuntimeError("Build finished without producing the expected app executable.")
    print(
        f"\nBuilt: {app}\nExternal tools remain external: FFmpeg/ffprobe, Deno, and optional Tor."
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--setup", action="store_true", help="Install the locked build environment only"
    )
    parser.add_argument(
        "--check", action="store_true", help="Verify inputs and build dependencies only"
    )
    args = parser.parse_args()
    try:
        if platform.system() != "Darwin":
            raise RuntimeError("The macOS app must be built on macOS.")
        if args.setup:
            setup_environment()
        check_environment()
        if not args.setup and not args.check:
            build()
    except (RuntimeError, subprocess.CalledProcessError, AssertionError) as exc:
        print(f"Build failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
