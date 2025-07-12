from PySide6.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLineEdit, QTextEdit, QSizePolicy
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextOption
from mutagen.easyid3 import EasyID3
import mutagen.id3


class MetadataFormWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        self.setObjectName("MetadataFormWidget")
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        form_wrapper = QWidget()

        self.form_layout = QFormLayout(form_wrapper)
        self.form_layout.setLabelAlignment(Qt.AlignRight)

        self.title_input = QLineEdit()
        self.artist_input = QLineEdit()
        self.album_input = QLineEdit()
        self.album_artist_input = QLineEdit()
        self.genre_input = QLineEdit()
        self.year_input = QLineEdit()
        self.track_input = QLineEdit()
        self.composer_input = QTextEdit()
        self.comment_input = QTextEdit()
        self.explicit_input = QTextEdit()
        self.bpm_input = QLineEdit()
        self.lyrics_input = QTextEdit()

        for widget in [
            self.title_input, self.artist_input, self.album_input,
            self.album_artist_input, self.genre_input, self.year_input,
            self.track_input, self.bpm_input,
            self.composer_input, self.comment_input,
            self.explicit_input, self.lyrics_input
        ]:
            widget.setMinimumWidth(350)

        # Adjust text fields for multiline input
        for textedit in [self.composer_input, self.comment_input, self.explicit_input, self.lyrics_input]:
            textedit.setWordWrapMode(QTextOption.WordWrap)
            textedit.setMinimumHeight(60)
            textedit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.lyrics_input.setMinimumHeight(120)

        # Placeholders
        self.title_input.setPlaceholderText("Full song title, e.g. 'Iron Man'")
        self.artist_input.setPlaceholderText("Primary performer, e.g. 'Black Sabbath'")
        self.album_input.setPlaceholderText("Album name, e.g. 'Paranoid'")
        self.album_artist_input.setPlaceholderText("Main credited artist for the album")
        self.genre_input.setPlaceholderText("Music style or category, e.g. 'Heavy Metal'")
        self.year_input.setPlaceholderText("Release year, e.g. '1970'")
        self.track_input.setPlaceholderText("Track position, e.g. '2' or '2/8'")
        self.composer_input.setPlaceholderText("Songwriters, e.g. 'Iommi, Butler, Osbourne, Ward'")
        self.comment_input.setPlaceholderText("Optional notes, e.g. 'Studio version, remastered'")
        self.explicit_input.setPlaceholderText("Flag if content is explicit: Yes / No")
        self.bpm_input.setPlaceholderText("Tempo in BPM (Beats Per Minute), e.g. '75'")
        self.lyrics_input.setPlaceholderText("Full unsynced lyrics (optional)")

        # Add form rows
        self.form_layout.addRow("Title:", self.title_input)
        self.form_layout.addRow("Artist:", self.artist_input)
        self.form_layout.addRow("Album:", self.album_input)
        self.form_layout.addRow("Album Artist:", self.album_artist_input)
        self.form_layout.addRow("Genre:", self.genre_input)
        self.form_layout.addRow("Year:", self.year_input)
        self.form_layout.addRow("Track #:", self.track_input)
        self.form_layout.addRow("Composer:", self.composer_input)
        self.form_layout.addRow("Comment:", self.comment_input)
        self.form_layout.addRow("Explicit:", self.explicit_input)
        self.form_layout.addRow("BPM:", self.bpm_input)
        self.form_layout.addRow("Lyrics:", self.lyrics_input)

        layout.addWidget(form_wrapper, alignment=Qt.AlignCenter)

    def get_metadata(self) -> dict:
        return {
            "title": self.title_input.text(),
            "artist": self.artist_input.text(),
            "album": self.album_input.text(),
            "album_artist": self.album_artist_input.text(),
            "genre": self.genre_input.text(),
            "year": self.year_input.text(),
            "track_number": self.track_input.text(),
            "composer": self.composer_input.toPlainText(),
            "comment": self.comment_input.toPlainText(),
            "explicit": self.explicit_input.toPlainText(),
            "bpm": self.bpm_input.text(),
            "lyrics": self.lyrics_input.toPlainText(),
        }

    def set_metadata(self, metadata: dict):
        self.title_input.setText(metadata.get("title", ""))
        self.artist_input.setText(metadata.get("artist", ""))
        self.album_input.setText(metadata.get("album", ""))
        self.album_artist_input.setText(metadata.get("album_artist", ""))
        self.genre_input.setText(metadata.get("genre", ""))
        self.year_input.setText(metadata.get("year", ""))
        self.track_input.setText(metadata.get("track_number", ""))
        self.composer_input.setPlainText(metadata.get("composer", ""))
        self.comment_input.setPlainText(metadata.get("comment", ""))
        self.explicit_input.setPlainText(metadata.get("explicit", ""))
        self.bpm_input.setText(metadata.get("bpm", ""))
        self.lyrics_input.setPlainText(metadata.get("lyrics", ""))

    def clear(self):
        for field in [
            self.title_input, self.artist_input, self.album_input,
            self.album_artist_input, self.genre_input, self.year_input,
            self.track_input, self.bpm_input
        ]:
            field.clear()

        for text_field in [
            self.composer_input, self.comment_input,
            self.explicit_input, self.lyrics_input
        ]:
            text_field.clear()

    def load_from_file(self, path: str) -> bool:
        """Reads metadata from an audio file and sets the form. Return success."""
        try:
            audio = EasyID3(path)
            metadata = {
                "title": audio.get("title", [""])[0],
                "artist": audio.get("artist", [""])[0],
                "album": audio.get("album", [""])[0],
                "album_artist": audio.get("albumartist", [""])[0],
                "genre": audio.get("genre", [""])[0],
                "year": audio.get("date", [""])[0],
                "track_number": audio.get("tracknumber", [""])[0],
                "composer": audio.get("composer", [""])[0],
                "bpm": audio.get("bpm", [""])[0] if "bpm" in audio else "",
                "explicit": "",  # fallback value
                "comment": "",
                "lyrics": ""
            }

            # Read additional ID3-only frames
            full_tags = mutagen.id3.ID3(path)

            # comm = next((f for f in full_tags.getall("COMM") if f.lang == "eng"), None)
            comm = next((f for f in full_tags.getall("COMM") if f.lang == "eng" and f.desc == ""), None)

            if comm:
                metadata["comment"] = comm.text[0]

            for frame in full_tags.getall("TXXX"):
                if frame.desc.lower() == "explicit":
                    metadata["explicit"] = frame.text[0]
                    break

            uslt = next((f for f in full_tags.getall("USLT") if f.lang == "eng"), None)
            if uslt:
                metadata["lyrics"] = uslt.text

            self.set_metadata(metadata)
            return True

        except mutagen.id3.ID3NoHeaderError:
            return False
        except Exception as e:
            print(f"MetadataFormWidget: Error loading metadata: {e}")
            return False