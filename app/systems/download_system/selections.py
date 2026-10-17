"""Build explicit source-language and caption download options."""

import re


def media_choices(info):
    audio = []
    for item in info.get("formats") or []:
        language = item.get("language")
        identifier = item.get("format_id")
        if language and identifier and item.get("vcodec") == "none":
            label = item.get("format_note") or identifier
            audio.append({"id": "id:" + identifier, "label": f"{language} — {label}"})
    subtitles = info.get("subtitles") or {}
    return {
        "audio": audio,
        "captions": [
            {"id": key, "label": f"{key} — {(tracks[0].get('name') or key) if tracks else key}"}
            for key, tracks in sorted(subtitles.items())
        ],
    }


def apply_selections(options, audio=None, caption=None, embed=False):
    options = dict(options)
    if audio:
        spec = options.get("format", "bestvideo+bestaudio/best")
        if audio.startswith("id:"):
            identifier = audio[3:]
            if not re.fullmatch(r"[\w.-]+", identifier):
                raise ValueError("Invalid audio track selection.")
            # Keep the exact regional track; do not silently fall back to another.
            spec = spec.split("/")[0]
            spec = re.sub(r"\bbestaudio\b(?:\[[^\]]+\])*", identifier, spec)
        else:
            if not re.fullmatch(r"[\w-]+", audio):
                raise ValueError("Invalid audio language selection.")
            spec = re.sub(r"\bbestaudio\b", f"bestaudio[language={audio}]", spec)
            spec = re.sub(r"\bbest\b", f"best[language={audio}]", spec)
        options["format"] = spec
    if caption:
        if not re.fullmatch(r"[\w-]+", caption):
            raise ValueError("Invalid caption selection.")
        options.update(
            writesubtitles=True, subtitleslangs=[caption], subtitlesformat="srt/vtt/best"
        )
        if embed:
            options["merge_output_format"] = "mkv"
            options["postprocessors"] = [
                *options.get("postprocessors", []),
                {"key": "FFmpegEmbedSubtitle"},
            ]
    return options
