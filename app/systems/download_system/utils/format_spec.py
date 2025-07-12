import shutil
import json
from app.systems.download_system.utils.privacy_config import get_privacy_options
from app.core.logger import logger

ENABLE_FORMAT_LOGGING = True

class FormatSpec:
    """Provides yt-dlp options based on format choice."""

    @staticmethod
    def check_ffmpeg() -> str:
        """Ensure ffmpeg is installed on the system."""
        ffmpeg_path = shutil.which("ffmpeg")
        if not ffmpeg_path:
            raise FileNotFoundError(
                "❌ 'ffmpeg' not found.\n"
                "Install it using Homebrew:\n"
                "  brew install ffmpeg"
            )
        return ffmpeg_path

    @staticmethod
    def get_options(choice: str, temp_sandbox_folder=None) -> dict:
        """Return yt-dlp options for a given format choice."""
        FormatSpec.check_ffmpeg()
        choice = str(choice or '1')

        # Privacy and sandbox config
        base_options = {
            'paths': {
                'home': str(temp_sandbox_folder),
            },
            'outtmpl': '%(title)s.%(ext)s',
            'keepvideo': True,
            **get_privacy_options(),
        }

        def log_and_return(opts):
            if ENABLE_FORMAT_LOGGING:
                logger.debug(f"[FormatSpec] yt-dlp options for choice {choice}:\n" + json.dumps(opts, indent=2))
            return opts

        if choice == '1':  # MP3
            return log_and_return({
                **base_options,
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })

        elif choice == '2':  # FLAC
            return log_and_return({
                **base_options,
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'flac',
                }],
            })

        elif choice == '3':  # MP4
            return log_and_return({
                **base_options,
                'format': 'bestvideo+bestaudio/best',
                'merge_output_format': 'mp4',
            })

        elif choice == '4':  # Audio only (raw)
            return log_and_return({
                **base_options,
                'format': 'bestaudio[ext=m4a]/bestaudio',
                'postprocessors': [],
                'merge_output_format': None,
            })

        elif choice == '5':  # Video only (raw)
            return log_and_return({
                **base_options,
                'format': 'bestvideo[ext=webm]/bestvideo',
                'postprocessors': [],
                'merge_output_format': None,
            })

        elif choice == '6':  # MKV
            return log_and_return({
                **base_options,
                'format': 'bestvideo+bestaudio/best',
                'merge_output_format': 'mkv',
            })

        elif choice == '7':  # WEBM
            return log_and_return({
                **base_options,
                'format': 'bestvideo[ext=webm]+bestaudio[ext=webm]/bestvideo+bestaudio',
                'merge_output_format': 'webm',
            })

        elif choice == '8':  # AVI
            return log_and_return({
                **base_options,
                'format': 'bestvideo+bestaudio/best',
                'merge_output_format': 'avi',
            })

        elif choice == '9':  # MOV
            return log_and_return({
                **base_options,
                'format': 'bestvideo+bestaudio/best',
                'merge_output_format': 'mov',
            })

        elif choice == '10':  # M4A
            return log_and_return({
                **base_options,
                'format': 'bestaudio[ext=m4a]/bestaudio',
                'postprocessors': [],
                'merge_output_format': None,
            })

        elif choice == '11':  # OPUS
            return log_and_return({
                **base_options,
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'opus',
                }],
            })

        elif choice == '12':  # AAC
            return log_and_return({
                **base_options,
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'aac',
                }],
            })

        elif choice == '13':  # WAV
            return log_and_return({
                **base_options,
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'wav',
                }],
            })

        raise ValueError(f"Unknown format choice: {choice}")