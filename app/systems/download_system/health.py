"""Preflight and repair missing download tools before contacting a media site."""

import os
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path
from urllib.parse import urlparse

_REPAIR_LOCK = threading.Lock()


def is_youtube(url):
    host = (urlparse(url).hostname or "").lower()
    return host == "youtu.be" or host == "youtube.com" or host.endswith(".youtube.com")


def find_tool(name):
    candidates = [shutil.which(name)]
    candidates += [str(Path(base) / name) for base in ("/opt/homebrew/bin", "/usr/local/bin")]
    if name == "deno":
        candidates.append(str(Path.home() / ".deno/bin/deno"))
    for candidate in candidates:
        if candidate and os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return None


def run_command(command, cancelled, timeout=600):
    """Drain installer output while allowing cancellation and enforcing a deadline."""
    env = {**os.environ, "HOMEBREW_NO_AUTO_UPDATE": "1", "NONINTERACTIVE": "1"}
    with subprocess.Popen(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
    ) as process:
        started = time.monotonic()
        while True:
            try:
                if cancelled():
                    raise RuntimeError("__CANCELLED__")
                if time.monotonic() - started > timeout:
                    raise RuntimeError(
                        "Tool repair timed out. Check your connection and try again."
                    )
                output, _ = process.communicate(timeout=0.2)
                if process.returncode:
                    raise RuntimeError("Tool repair failed:\n" + output[-2000:])
                return output
            except subprocess.TimeoutExpired:
                continue
            except BaseException:
                process.terminate()
                try:
                    process.communicate(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.communicate()
                raise


def usable_deno(path, cancelled):
    if not path:
        return False
    try:
        output = run_command([path, "--version"], cancelled, timeout=15)
    except (OSError, RuntimeError) as exc:
        if str(exc) == "__CANCELLED__":
            raise
        return False
    match = re.search(r"deno (\d+)\.(\d+)\.(\d+)", output)
    return bool(match and tuple(map(int, match.groups())) >= (2, 3, 0))


def ensure_download_tools(url, report, cancelled=lambda: False):
    """Repair via existing Homebrew/venv; return explicit yt-dlp tool paths."""
    while not _REPAIR_LOCK.acquire(timeout=0.2):
        if cancelled():
            raise RuntimeError("__CANCELLED__")
    try:
        if cancelled():
            raise RuntimeError("__CANCELLED__")
        report("Checking download tools...")
        youtube = is_youtube(url)
        missing = []
        if not find_tool("ffmpeg") or not find_tool("ffprobe"):
            missing.append("ffmpeg")
        deno = find_tool("deno") if youtube else None
        if youtube and not usable_deno(deno, cancelled):
            missing.append("deno")
        if missing:
            brew = find_tool("brew") if sys.platform == "darwin" else None
            if not brew:
                raise RuntimeError(
                    "Missing or outdated download tools: "
                    + ", ".join(missing)
                    + ". Automatic installation requires Homebrew on macOS. "
                    "Install Homebrew from https://brew.sh, then retry the download."
                )
            report("Installing required tools: " + ", ".join(missing) + "...")
            run_command([brew, "install", *missing], cancelled)
            # Prefer the Homebrew result over an older runtime elsewhere on PATH.
            deno = str(Path(brew).parent / "deno") if "deno" in missing else deno
            for tool in ("ffmpeg", "ffprobe"):
                if not find_tool(tool):
                    raise RuntimeError(f"{tool} is still unavailable after repair.")
            if youtube and not usable_deno(deno, cancelled):
                raise RuntimeError("Deno repair did not produce a supported runtime (2.3+).")
        if youtube and not getattr(sys, "frozen", False):
            probe = subprocess.run(
                [sys.executable, "-c", "import yt_dlp_ejs"],
                capture_output=True,
                timeout=15,
            )
            if probe.returncode:
                if sys.prefix == sys.base_prefix:
                    raise RuntimeError(
                        "YouTube support repair requires an active virtual environment."
                    )
                report("Installing YouTube support components...")
                run_command(
                    [
                        sys.executable,
                        "-m",
                        "pip",
                        "--isolated",
                        "install",
                        "--no-input",
                        "--disable-pip-version-check",
                        "--upgrade",
                        "--index-url",
                        "https://pypi.org/simple",
                        "yt-dlp[default]",
                    ],
                    cancelled,
                    timeout=180,
                )
                result = subprocess.run(
                    [sys.executable, "-c", "import yt_dlp_ejs"],
                    capture_output=True,
                    timeout=15,
                )
                if result.returncode:
                    raise RuntimeError(
                        "YouTube support components are still unavailable after repair."
                    )
        report("Download tools ready.")
        options = {"ffmpeg_location": str(Path(find_tool("ffmpeg")).parent)}
        if youtube:
            options["js_runtimes"] = {"deno": {"path": deno}}
        return options
    finally:
        _REPAIR_LOCK.release()
