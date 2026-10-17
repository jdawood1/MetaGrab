# MetaGrab

**MetaGrab** is a macOS-only desktop application built with Python and PyInstaller.

> ⚠️ _This project is not currently under active development._  
> The repository includes a working build script and bundled assets for macOS (tested on Apple Silicon / M1).

## Build the local macOS app

Use Python 3.11 on the Mac/architecture you want to build for. Packaging has its
own `.venv-build` environment, separate from the application's `.venv`.

One-time setup (also use this after updating the committed lock file):

```bash
python3.11 build.py --setup
```

Check the environment and package the app:

```bash
python3.11 build.py --check
python3.11 build.py
```

The output is `dist/MetaGrab.app`. You can pass an absolute path to `build.py`
from another working directory. The script does not copy over a Desktop app,
install tools during an ordinary build, or delete the committed `MetaGrab.spec`.
Build output and cache stay in `build/` and `dist/`.

`MetaGrab.spec` defines the icon, assets, all three stylesheets, helper modules,
yt-dlp extractors, and YouTube challenge-script resources. `requirements-build.txt`
pins the packaging tools; `requirements-build.lock` pins the full resolved build
and application Python environment, including transitive dependencies. The lock
was resolved for macOS Apple Silicon with Python 3.11; it is not a universal or
cross-platform lock. Keep both files in Git. Re-resolve deliberately in a fresh
environment when changing dependencies and review the lock before committing.
The build checks installed versions against the lock and runs `pip check`.

External tools remain external: FFmpeg/ffprobe, Deno, and optional Tor tools.
Their versions and the system SDK/OS are not locked by this Python lock. The app
uses local/ad-hoc signing and is not notarized for distribution. Embedded yt-dlp
still requires an app rebuild to update. This setup makes Python build inputs
repeatable; it does not promise byte-for-byte identical app bundles.

## Notes

The app is a macOS `.app` bundle, built for the build interpreter's architecture.
Assets live in `assets/`. User data directories are created at runtime, not by
the build script. Verify the actual bundle from Finder before distributing it.

## Development checks

Use Python 3.10 or newer (as required by `pyproject.toml`).
Install the pinned development tool separately from the app dependencies:

```bash
python -m pip install -r requirements-dev.txt
ruff check .
ruff format --check .
```

To apply supported lint fixes and format Python files:

```bash
ruff check --fix .
ruff format .
```

Review fixes before committing. The checks also run on GitHub pushes and pull requests.
The lint workflow does not install or launch the GUI, FFmpeg, or Tor.
Qt stylesheets are outside the scope of these Python checks.

## Install and run from source (macOS)

From the repository folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python main.py
```

Install FFmpeg separately and make sure it is on your PATH. Tor features also
require the external Tor tools. Run the app from this folder so its assets resolve.

Runtime dependencies are maintained only in `requirements.txt`; `pyproject.toml`
reads that file automatically. `pip install -r requirements.txt` is also supported.
This change retains the existing dependency versions; it does not lock transitive
dependencies or upgrade the media downloader.

To install lint tools in the same environment:

```bash
python -m pip install -r requirements-dev.txt
```

## Automatic downloader repair

On recognizable extraction failures, source installs check PyPI for a newer stable
yt-dlp release, update `yt-dlp[default]` inside the active virtual environment,
and retry once in a fresh process. The update check runs at most once per app
session. Other failures show their error without triggering an update. Updates
require network access and may update yt-dlp's supporting Python packages.
Bundled `.app` builds require an application update instead.

After replacing this source folder, update the installed project metadata:

```bash
source .venv/bin/activate
python -m pip install --upgrade -e .
python main.py
```

YouTube support also needs a supported JavaScript runtime (Deno is recommended
and detected automatically when on PATH). FFmpeg and ffprobe remain external tools.
See https://github.com/yt-dlp/yt-dlp/wiki/EJS for setup instructions.

Run the updater regression tests with:

```bash
python -m unittest tests.test_downloader_updater
```

## Download tool health and repair

Before Download or Analyze, MetaGrab checks FFmpeg/ffprobe and, for YouTube,
Deno 2.3+ and the Python YouTube challenge scripts. When Homebrew is already
installed on macOS, missing FFmpeg or missing/outdated Deno is installed through
Homebrew automatically. These are shared tools, not private app copies. The
status list explains each repair step; a download starts only after rechecking.
Missing Python challenge scripts are installed with `yt-dlp[default]` in the
active virtual environment. Network access and writable install locations are
required. Homebrew itself is not installed automatically, and no administrator
password is requested by the app. Installation errors show a specific message.

Cancel stops the app's active installer command or download; already-installed
packages remain installed. A bundled app still needs a new app release to update
its embedded Python downloader and challenge scripts. External tools can be
repaired through Homebrew. Site restrictions, authentication requirements, and
network failures cannot always be repaired automatically.

Regression checks:

```bash
python -m unittest tests.test_downloader_updater tests.test_download_health
```

## AniZone episode support

Paste an AniZone episode URL (for example, `/anime/<series>/<episode>`) into
Download or Analyze. MetaGrab reads the Vidstack player's encoded source settings
and passes its HLS playlist to yt-dlp, retaining the episode page as the Referer.
Existing format selection, FFmpeg processing, and export behavior are reused.
Audio selection follows yt-dlp defaults; a language picker is not included.
Other sites continue using yt-dlp's standard extractors.

Verification: the supplied episode page and live HLS playlist exposed 29 formats
(3 video and 26 audio-only), and yt-dlp selected a video/audio pair. No full episode
was downloaded during verification. Site layout changes may require updating this
extractor. Missing player settings produce a specific error.

```bash
python -m unittest tests.test_downloader_updater tests.test_download_health tests.test_anizone
```

## Source and audio analyzer

Analyze opens a selectable, scrollable report containing the title, source URL,
extractor, duration/uploader when supplied, source stream containers and protocols,
video/audio codecs, resolutions, frame rates, audio rates/channels/languages,
subtitle languages, and file sizes when known (estimates are marked). Unavailable
metadata is shown as unknown. Source streams are not proof of the original upload
format, which most sites do not expose.

For non-live sources, Analyze requests only the first 15 seconds of a preferred
audio stream through FFmpeg and measures integrated LUFS, true peak, and loudness
range. Transport/keyframe boundaries may add a little data around the excerpt.
Measurements are sample-based, not whole-program values. Temporary sample files
are removed after analysis. MP4 audio is supported using the downloader's reported
file path rather than a filename-extension whitelist. Metadata remains visible if
sampling or loudness measurement fails. Source installations run analysis in a
fresh process with a four-minute timeout, so downloader updates are picked up.

## Audio language and captions

1. Paste an episode/video URL and click Analyze.
2. Close the report, then choose an Audio track and optional Captions track.
3. Choose Separate subtitle file or Embed captions (switches to MKV).
4. Click Download.

Audio defaults to the downloader's selection; captions default to None. Explicit
audio choices use an exact format ID, retaining regional variants. If that track
is no longer available, downloading fails rather than switching languages.
Editing the URL clears the discovered choices; analyze the new URL to repopulate.
Embedded captions force MKV for video/audio compatibility. Separate subtitle files
are exported beside downloads and are not sent through audio metadata processing.
AniZone's player-supplied subtitles, including forced/SDH/regional variants, now
appear in Analyze and the captions selector. One audio and one manual subtitle
track can be selected at a time. Automatic captions are not included in this picker.

## Download folder access

The Folders page opens even if Downloads cannot be read. It shows an access-needed
message and a Choose download folder button. Choose an existing readable, writable
folder; the destination is saved with your settings and used by later downloads.
You can also grant folder access in macOS Privacy & Security and click Refresh.
Failed exports report an error and retain remaining files in the logged temporary
sandbox rather than declaring the download complete. Original/raw files still use
the app's Originals folder. Changing the destination affects subsequent exports.
