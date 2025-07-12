# MetaGrab

**MetaGrab** is a macOS-only desktop application built with Python and PyInstaller.

> ⚠️ _This project is not currently under active development._  
> The repository includes a working build script and bundled assets for macOS (tested on Apple Silicon / M1).

## 🚀 Build Instructions (macOS only)

1. Make sure you have the following installed:
   - Python 3.9+  
   - [`ffmpeg`](https://ffmpeg.org/download.html) in your system PATH  
   - Required packages in `requirements.txt`

2. Run the build script:

```bash
python build.py
```

The script will:

- Clean old build files
- Bundle assets and dependencies
- Build a `.app` with PyInstaller
- Copy the resulting app to your Desktop

## 📝 Notes

- Output is a macOS `.app` bundle.
- Icon and assets are located in the `assets/` directory.
- Script includes automatic installation of missing dependencies like Pillow and PyInstaller.
