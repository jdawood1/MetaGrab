# Version-controlled macOS onedir application bundle.
from pathlib import Path
import tomllib

from PyInstaller.utils.hooks import collect_all

root = Path(SPECPATH)
metadata = tomllib.loads((root / "pyproject.toml").read_text())["project"]
yt_data, yt_bins, yt_imports = collect_all("yt_dlp")
ejs_data, ejs_bins, ejs_imports = collect_all("yt_dlp_ejs")

a = Analysis(
    [str(root / "main.py")],
    pathex=[str(root)],
    binaries=yt_bins + ejs_bins,
    datas=[(str(root / "assets"), "assets"),
           (str(root / "app/styles/dark.qss"), "app/styles"),
           (str(root / "app/styles/light.qss"), "app/styles"),
           (str(root / "app/styles/style.qss"), "app/styles")] + yt_data + ejs_data,
    hiddenimports=yt_imports + ejs_imports + [
        "app.systems.download_system.analysis", "app.systems.download_system.analysis_runner",
        "app.systems.download_system.download_runner", "app.systems.download_system.selections",
    ],
    hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[], noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [], exclude_binaries=True, name="MetaGrab",
    debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
    console=False, argv_emulation=False, target_arch=None, codesign_identity=None,
    entitlements_file=None,
)
collection = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="MetaGrab")
app = BUNDLE(
    collection, name="MetaGrab.app", icon=str(root / "assets/icon.icns"),
    bundle_identifier="local.metagrab.app",
    info_plist={"CFBundleShortVersionString": metadata["version"],
                "CFBundleVersion": metadata["version"], "NSHighResolutionCapable": True},
)
