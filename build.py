import subprocess
import shutil
import sys
import time
from pathlib import Path

APP_NAME = "MetaGrab"
ENTRY_SCRIPT = "main.py"
ICON_FILE = "assets/icon.icns"
ASSETS_DIR = "assets"
REQUIREMENTS_FILE = "requirements.txt"
BUILD_DIRS = ["build", "dist", f"{APP_NAME}.spec"]

PROJECT_ROOT = Path(__file__).resolve().parent

def clean():
    print("[*] Cleaning previous build artifacts...")
    for item in BUILD_DIRS:
        target = PROJECT_ROOT / item
        if target.exists():
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()

def read_hidden_imports(requirements_file):
    hidden_imports = []
    req_path = PROJECT_ROOT / requirements_file
    if req_path.exists():
        with open(req_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                package = line.split("~=")[0].strip()
                hidden_imports.append(f"--hidden-import={package}")
    return hidden_imports

def install(package):
    print(f"[*] Installing missing dependency: {package}")
    subprocess.run([sys.executable, "-m", "pip", "install", package], check=True)

def run_build(hidden_imports):
    print("[*] Preparing asset bundle...")
    asset_data_args = []

    # Add critical theme files manually
    asset_data_args += [
        "--add-data", "app/styles/dark.qss:app/styles",
        "--add-data", "app/styles/light.qss:app/styles",
    ]

    assets_dir = PROJECT_ROOT / ASSETS_DIR
    if assets_dir.exists():
        for file_path in assets_dir.rglob("*"):
            if file_path.is_file():
                relative_path = file_path.relative_to(PROJECT_ROOT)
                asset_data_args += [
                    "--add-data", f"{relative_path}:{relative_path.parent}"
                ]

    cmd = [
              sys.executable, "-m", "PyInstaller",
              "--noconfirm",
              "--windowed",
              f"--name={APP_NAME}",
              f"--icon={PROJECT_ROOT / ICON_FILE}",
          ] + asset_data_args + hidden_imports + [str(PROJECT_ROOT / ENTRY_SCRIPT)]


    print("[*] Running PyInstaller...")
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate()

    if process.returncode != 0:
        if "No module named 'PIL'" in stderr or "normalize_icon_type" in stderr:
            raise RuntimeError("MissingPillow")
        else:
            print(stdout)
            print(stderr)
            raise RuntimeError("BuildFailed")
    return stdout, stderr

def copy_app_to_desktop():
    desktop_path = Path.home() / "Desktop"
    dist_app_path = PROJECT_ROOT / "dist" / f"{APP_NAME}.app"

    if dist_app_path.exists():
        dest_path = desktop_path / f"{APP_NAME}.app"
        print(f"[*] Copying app to Desktop: {dest_path}")
        if dest_path.exists():
            shutil.rmtree(dest_path)
        shutil.copytree(dist_app_path, dest_path)
        print(f"[+] Done: App available on Desktop.")
    else:
        print("[!] .app not found — skipping copy.")

def ensure_ffmpeg():
    if not shutil.which("ffmpeg"):
        print("[!] ffmpeg not found. Please install it and ensure it’s on your PATH.")
        sys.exit(1)

def ensure_runtime_dirs():
    try:
        from app.core import settings
        for path in [settings.ORIGINALS_DIR, settings.EXPORTS_DIR, settings.LOG_DIR, settings.CONFIG_DIR]:
            path.mkdir(parents=True, exist_ok=True)
        print("[*] Verified runtime folders.")
    except Exception as e:
        print(f"[!] Could not verify runtime directories: {e}")
        sys.exit(1)

def build():
    print(f"[*] Starting build for: {APP_NAME}")
    hidden_imports = read_hidden_imports(REQUIREMENTS_FILE)

    try:
        run_build(hidden_imports)
    except RuntimeError as e:
        if str(e) == "MissingPillow":
            print("[!] Missing Pillow. Installing...")
            install("pillow")
            clean()
            print("[*] Retrying build...")
            time.sleep(1)
            run_build(hidden_imports)
        else:
            print("[!] Build failed unexpectedly.")
            sys.exit(1)

    print("[+] Build complete.")
    copy_app_to_desktop()

if __name__ == "__main__":
    print("[MetaGrab Builder]")

    if not shutil.which("pyinstaller"):
        print("[*] PyInstaller not found. Installing...")
        install("pyinstaller")

    ensure_ffmpeg()
    ensure_runtime_dirs()
    clean()
    build()