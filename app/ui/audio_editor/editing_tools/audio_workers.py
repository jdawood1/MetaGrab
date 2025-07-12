import re
import json
import subprocess
from typing import Optional, Callable

from app.core.logger import logger
from app.ui.audio_editor.editing_tools.audio_presets import build_ffmpeg_command, AudioFormatPresets, \
    AudioNormalizePresets
from app.ui.audio_editor.editing_tools.base_ffmpeg_worker import BaseFFmpegWorker

ENABLE_FORMAT_LOGGING = False
active_audio_threads = set()

class UnifiedProcessWorker(BaseFFmpegWorker):
    def __init__(self, input_path: str, output_path: str,
                 crop_start: Optional[float] = None, crop_end: Optional[float] = None,
                 normalize_filter: Optional[str] = None, codec: Optional[str] = "libmp3lame",
                 bitrate: Optional[str] = "192k", sample_rate: Optional[int] = 48000,
                 channels: Optional[int] = 2):
        self.input_path = input_path
        self.output_path = output_path
        self.crop_start = crop_start
        self.crop_end = crop_end
        self.normalize_filter = normalize_filter
        self.codec = codec
        self.bitrate = bitrate
        self.sample_rate = sample_rate
        self.channels = channels
        self._two_pass_required = normalize_filter and "print_format=json" in normalize_filter

        super().__init__([], output_path, enable_logging=ENABLE_FORMAT_LOGGING)
        active_audio_threads.add(self)

    def run(self):
        try:
            if self._two_pass_required:
                cmd = build_two_pass_normalize_command(
                    input_path=self.input_path,
                    output_path=self.output_path,
                    normalize_filter=self.normalize_filter,
                    crop_start=self.crop_start,
                    crop_end=self.crop_end,
                    codec=self.codec,
                    bitrate=self.bitrate,
                    sample_rate=self.sample_rate,
                    channels=self.channels,
                    logging=ENABLE_FORMAT_LOGGING,
                    cancel_flag=self.cancelled
                )
                if not cmd:
                    logger.info("[UnifiedProcessWorker] Two-pass normalization was cancelled or failed.")
                    return  # Don’t call super().run() if first pass was cancelled

                self.cmd = cmd
            else:
                self.cmd = build_ffmpeg_command(
                    input_path=self.input_path,
                    output_path=self.output_path,
                    crop_start=self.crop_start,
                    crop_end=self.crop_end,
                    normalize_filter=self.normalize_filter,
                    codec=self.codec,
                    bitrate=self.bitrate,
                    sample_rate=self.sample_rate,
                    channels=self.channels
                )

            ext = self.output_path.lower().split(".")[-1]
            if ext in AudioFormatPresets.LOSSLESS_FORMATS:
                self.cmd += ["-map_metadata", "-1", "-vn"]

            super().run()
        finally:
            active_audio_threads.discard(self)


class CropWorker(BaseFFmpegWorker):
    def __init__(self, input_path: str, output_path: str, start_sec: float, end_sec: float):
        cmd = build_ffmpeg_command(
            input_path=input_path,
            output_path=output_path,
            crop_start=start_sec,
            crop_end=end_sec
        )
        super().__init__(cmd, output_path, enable_logging=ENABLE_FORMAT_LOGGING)
        active_audio_threads.add(self)

    def run(self):
        try:
            super().run()
        finally:
            active_audio_threads.discard(self)


class NormalizeWorker(BaseFFmpegWorker):
    def __init__(self, input_path: str, output_path: str, filter_string: str):
        self.input_path = input_path
        self.output_path = output_path
        self.filter_string = filter_string
        self._two_pass_required = "print_format=json" in filter_string

        super().__init__([], output_path, enable_logging=ENABLE_FORMAT_LOGGING)
        active_audio_threads.add(self)

    def run(self):
        try:
            if self._two_pass_required:
                cmd = build_two_pass_normalize_command(
                    input_path=self.input_path,
                    output_path=self.output_path,
                    normalize_filter=self.filter_string,
                    logging=ENABLE_FORMAT_LOGGING,
                    cancel_flag=self.cancelled
                )
                if not cmd:
                    logger.info("[NormalizeWorker] Two-pass normalization was cancelled or failed.")
                    return

                self.cmd = cmd
            else:
                self.cmd = build_ffmpeg_command(
                    input_path=self.input_path,
                    output_path=self.output_path,
                    normalize_filter=self.filter_string
                )

            super().run()
        finally:
            active_audio_threads.discard(self)


class ConvertWorker(BaseFFmpegWorker):
    def __init__(self, input_path: str, output_path: str,
                 codec: Optional[str] = "libmp3lame", bitrate: str = "192k",
                 sample_rate: Optional[int] = 48000, channels: Optional[int] = 2):
        cmd = build_ffmpeg_command(
            input_path=input_path,
            output_path=output_path,
            codec=codec,
            bitrate=bitrate,
            sample_rate=sample_rate,
            channels=channels
        )
        ext = output_path.lower().split(".")[-1]
        if ext in AudioFormatPresets.LOSSLESS_FORMATS:
            cmd += ["-map_metadata", "-1", "-vn"]

        super().__init__(cmd, output_path, enable_logging=ENABLE_FORMAT_LOGGING)
        active_audio_threads.add(self)

    def run(self):
        try:
            super().run()
        finally:
            active_audio_threads.discard(self)


# Probe Utility
def probe_audio(path: str) -> dict:
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", path],
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except Exception as e:
        if ENABLE_FORMAT_LOGGING:
            print(f"[ffprobe] Failed: {e}")
        return {}

# Two Pass Utility
def build_two_pass_normalize_command(
        input_path: str,
        output_path: str,
        normalize_filter: str,
        crop_start: Optional[float] = None,
        crop_end: Optional[float] = None,
        codec: Optional[str] = "libmp3lame",
        bitrate: Optional[str] = "192k",
        sample_rate: Optional[int] = 48000,
        channels: Optional[int] = 2,
        logging: bool = False,
        cancel_flag: Optional[Callable[[], bool]] = None
) -> Optional[list[str]]:
    first_cmd = ["ffmpeg"]
    if crop_start is not None:
        first_cmd += ["-ss", str(crop_start)]
    if crop_end is not None:
        first_cmd += ["-to", str(crop_end)]
    first_cmd += ["-i", input_path, "-af", normalize_filter, "-f", "null", "-"]

    try:
        proc = subprocess.Popen(
            first_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stderr_lines = []
        while True:
            if cancel_flag and cancel_flag():
                proc.terminate()
                try:
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    proc.kill()
                return None

            line = proc.stderr.readline()
            if not line and proc.poll() is not None:
                break
            if line:
                stderr_lines.append(line)

        stderr = ''.join(stderr_lines)

        if proc.returncode != 0:
            raise RuntimeError("FFmpeg returned non-zero exit code in pass 1")

        match = re.search(r'\{[\s\S]+?\}', stderr)
        if not match:
            raise ValueError("Could not extract loudnorm JSON output.")
        data = json.loads(match.group(0))

        preset_key = next(
            (k for k, v in AudioNormalizePresets.PRESETS.items()
             if f"I={v['I']}" in normalize_filter and
             f"TP={v['TP']}" in normalize_filter and
             f"LRA={v['LRA']}" in normalize_filter),
            None
        )
        if not preset_key:
            raise ValueError("No matching preset found.")

        preset = AudioNormalizePresets.PRESETS[preset_key]

        second_pass_filter = (
            f"loudnorm=I={preset['I']}:TP={preset['TP']}:LRA={preset['LRA']}:"
            f"measured_I={data['input_i']}:"
            f"measured_TP={data['input_tp']}:"
            f"measured_LRA={data['input_lra']}:"
            f"measured_thresh={data['input_thresh']}:"
            f"offset={data['target_offset']}:"
            f"linear=true:print_format=summary"
        )

        return build_ffmpeg_command(
            input_path=input_path,
            output_path=output_path,
            crop_start=crop_start,
            crop_end=crop_end,
            normalize_filter=second_pass_filter,
            codec=codec,
            bitrate=bitrate,
            sample_rate=sample_rate,
            channels=channels
        )

    except Exception as e:
        if logging:
            print(f"[TwoPass] Error: {e}")
        return None
