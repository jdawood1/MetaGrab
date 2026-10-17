from pathlib import Path

from mutagen.easymp4 import EasyMP4
from mutagen.flac import FLAC
from mutagen.id3 import ID3, TALB, TCON, TDRC, TIT2, TPE1, TRCK, ID3NoHeaderError
from mutagen.oggvorbis import OggVorbis


def set_metadata(file_path: Path, tags: dict) -> bool:
    if not file_path.exists() or not file_path.is_file():
        print("❌ File does not exist.")
        return False

    ext = file_path.suffix.lower()

    try:
        if ext == ".mp3":
            try:
                audio = ID3(file_path)
            except ID3NoHeaderError:
                audio = ID3()
            if "title" in tags:
                audio.add(TIT2(encoding=3, text=tags["title"]))
            if "artist" in tags:
                audio.add(TPE1(encoding=3, text=tags["artist"]))
            if "album" in tags:
                audio.add(TALB(encoding=3, text=tags["album"]))
            if "date" in tags:
                audio.add(TDRC(encoding=3, text=tags["date"]))
            if "tracknumber" in tags:
                audio.add(TRCK(encoding=3, text=tags["tracknumber"]))
            if "genre" in tags:
                audio.add(TCON(encoding=3, text=tags["genre"]))
            audio.save(file_path)
            print("✅ MP3 metadata updated.")

        elif ext in {".m4a", ".mp4"}:
            audio = EasyMP4(file_path)
            audio.update(tags)
            audio.save()
            print("✅ M4A/MP4 metadata updated.")

        elif ext == ".flac":
            audio = FLAC(file_path)
            audio.update(tags)
            audio.save()
            print("✅ FLAC metadata updated.")

        elif ext in {".ogg", ".oga"}:
            audio = OggVorbis(file_path)
            audio.update(tags)
            audio.save()
            print("✅ OGG metadata updated.")

        elif ext == ".webm":
            print("⚠️ WebM metadata writing is not supported by Mutagen. Use FFmpeg instead.")
            return False

        else:
            print("❌ Unsupported file type for metadata writing.")
            return False

        return True

    except Exception as e:
        print(f"❌ Error setting metadata: {e}")
        return False


# Example usage
if __name__ == "__main__":
    from pathlib import Path

    # Always reference file relative to the current script's location
    base_dir = Path(__file__).resolve().parent
    test_file = base_dir / "example.mp3"

    tags_to_write = {
        "title": "Test Song",
        "artist": "Test Artist",
        "album": "Test Album",
        "tracknumber": "1",
        "genre": "Test Genre",
        "date": "2025",
    }
    success = set_metadata(test_file, tags_to_write)
    if success:
        print("🎉 Metadata successfully written.")
