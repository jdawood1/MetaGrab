import os

import mutagen.id3
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3


class MetadataEmbedder:
    def __init__(self, cover_image_path: str | None = None):
        self.cover_image_path = cover_image_path
        if cover_image_path:
            if not os.path.isfile(cover_image_path):
                raise FileNotFoundError(f"Cover image not found: {cover_image_path}")

    def embed_metadata(
        self,
        file_path: str,
        title: str = "",
        artist: str = "",
        album: str = "",
        album_artist: str = "",
        genre: str = "",
        year: str = "",
        track_number: str = "",
        composer: str = "",
        comment: str = "",
        explicit: str = "",
        bpm: str = "",
        lyrics: str = "",
    ) -> bool:
        try:
            if not os.path.isfile(file_path):
                print(f"File not found: {file_path}")
                return False

            # Ensure ID3 tag container exists
            try:
                audio = MP3(file_path, ID3=mutagen.id3.ID3)
                if audio.tags is None:
                    audio.add_tags()
            except mutagen.id3.error:
                pass

            # Standard EasyID3 tags
            audio = EasyID3(file_path)
            if title:
                audio["title"] = title
            if artist:
                audio["artist"] = artist
            if album:
                audio["album"] = album
            if genre:
                audio["genre"] = genre
            if year:
                audio["date"] = year
            if track_number:
                audio["tracknumber"] = track_number
            if composer:
                audio["composer"] = composer
            if bpm:
                audio["bpm"] = bpm
            audio.save()

            # Extended ID3 tags
            id3 = mutagen.id3.ID3(file_path)

            if album_artist:
                id3.add(mutagen.id3.TPE2(encoding=3, text=album_artist))

            # if comment:
            #     id3.add(mutagen.id3.COMM(encoding=3, lang="eng", desc="Comment", text=comment))
            if comment:
                id3.add(mutagen.id3.COMM(encoding=3, lang="eng", desc="", text=comment))

            if explicit:
                id3.add(mutagen.id3.TXXX(encoding=3, desc="explicit", text=explicit))

            if lyrics:
                id3.add(mutagen.id3.USLT(encoding=3, lang="eng", desc="", text=lyrics))

            if self.cover_image_path:
                with open(self.cover_image_path, "rb") as img:
                    id3.add(
                        mutagen.id3.APIC(
                            encoding=3, mime="image/jpeg", type=3, desc="Cover", data=img.read()
                        )
                    )

            id3.save(v2_version=3)
            print(f"Metadata embedded into: {file_path}")
            return True

        except Exception as e:
            print(f"Error embedding metadata: {e}")
            return False

    def process_batch(self, metadata_list: list[dict]) -> list[str]:
        failed = []
        for meta in metadata_list:
            try:
                embedder = MetadataEmbedder(meta.get("cover_image_path"))
                success = embedder.embed_metadata(
                    file_path=meta["file_path"],
                    title=meta.get("title", ""),
                    artist=meta.get("artist", ""),
                    album=meta.get("album", ""),
                    album_artist=meta.get("album_artist", ""),
                    genre=meta.get("genre", ""),
                    year=meta.get("year", ""),
                    track_number=meta.get("track_number", ""),
                    composer=meta.get("composer", ""),
                    comment=meta.get("comment", ""),
                    explicit=meta.get("explicit", ""),
                    bpm=meta.get("bpm", ""),
                    lyrics=meta.get("lyrics", ""),
                )
                if not success:
                    failed.append(meta["file_path"])
            except Exception:
                failed.append(meta["file_path"])
        return failed
