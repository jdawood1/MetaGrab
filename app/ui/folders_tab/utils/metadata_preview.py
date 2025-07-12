from pathlib import Path
from PySide6.QtWidgets import QWidget
import mutagen.id3
from mutagen.mp3 import MP3
from app.ui.dialog_box_builder import get_confirmation

def get_audio_metadata(file_path: Path, parent: QWidget) -> str:
    if not file_path.exists() or not file_path.is_file():
        return "File not found."

    try:
        audio = MP3(file_path, ID3=mutagen.id3.ID3)
        info_lines = [f"<b>Metadata for: {file_path.name}</b><br><br>"]

        # Common ID3 frames
        extended_tags = {
            "Title": "TIT2",
            "Artist": "TPE1",
            "Album": "TALB",
            "Album Artist": "TPE2",
            "Track": "TRCK",
            "Genre": "TCON",
            "Year": "TDRC",
            "Composer": "TCOM",
            "BPM": "TBPM",
            "Comment": "COMM",
        }

        for label, frame_id in extended_tags.items():
            if frame_id == "COMM":
                comment_frames = audio.tags.getall("COMM")
                for frame in comment_frames:
                    if frame.lang == "eng":
                        info_lines.append(f"<b>{label}:</b> {frame.text[0]}<br>")
                        break
            else:
                tag = audio.tags.get(frame_id)
                if tag:
                    info_lines.append(f"<b>{label}:</b> {tag.text[0]}<br>")

        # Custom "Explicit" (TXXX frame)
        for frame in audio.tags.getall("TXXX"):
            if frame.desc.lower() == "explicit":
                info_lines.append(f"<b>Explicit:</b> {frame.text[0]}<br>")
                break

        # Lyrics (USLT frame)
        lyrics_frame = next((frame for frame in audio.tags.values() if isinstance(frame, mutagen.id3.USLT)), None)
        if lyrics_frame:
            if get_confirmation(parent, "Lyrics Found", "This file contains embedded lyrics. Show them?"):
                info_lines.append("<br><b>Lyrics:</b><br>")
                safe_lyrics = lyrics_frame.text.strip().replace("\n", "<br>")
                info_lines.append(f"<i>{safe_lyrics}</i><br>")

        # Cover Art (APIC)
        has_cover = any(isinstance(tag, mutagen.id3.APIC) for tag in audio.tags.values())
        info_lines.append("<br><b>Cover Art:</b> " + ("Image embedded<br>" if has_cover else "Not present<br>"))

        return ''.join(info_lines)

    except Exception as e:
        return f"Error reading metadata: {e}"
