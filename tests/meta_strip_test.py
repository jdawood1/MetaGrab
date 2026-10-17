import subprocess
from pathlib import Path


def strip_metadata():
    # Always reference file relative to the current script's location
    base_dir = Path(__file__).resolve().parent
    input_path = base_dir / "example.mp3"
    output_path = base_dir / "example_nometa.mp3"

    if not input_path.exists():
        raise FileNotFoundError(f"Test MP3 not found at: {input_path}")

    command = [
        "ffmpeg",
        "-i",
        str(input_path),
        "-map_metadata",
        "-1",  # Remove all metadata
        "-c",
        "copy",  # Copy without re-encoding
        str(output_path),
        "-y",  # Overwrite output
    ]

    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"✅ Metadata stripped: {output_path}")
    except subprocess.CalledProcessError as e:
        print("❌ FFmpeg error:")
        print(e.stderr.decode())


if __name__ == "__main__":
    try:
        strip_metadata()
    except Exception as e:
        print(f"❌ Error: {e}")
