"""Isolated yt-dlp process: a retry always loads the newly installed version."""

import json
import os
import sys

from app.systems.download_system.anizone import create_downloader


def emit(kind, payload):
    print(json.dumps({"kind": kind, "payload": payload}), flush=True)


class DownloadLogger:
    def debug(self, message):
        pass

    def warning(self, message):
        emit("warning", message)

    def error(self, message):
        emit("error", message)


def main():
    os.environ["METAGRAB_HELPER"] = "1"
    request = json.loads(sys.stdin.readline())
    options = request["options"]

    def hook(data):
        payload = {
            key: data.get(key)
            for key in (
                "status",
                "_percent_str",
                "downloaded_bytes",
                "total_bytes",
                "total_bytes_estimate",
                "speed",
                "eta",
            )
        }
        payload["title"] = data.get("info_dict", {}).get("title")
        emit("progress", payload)

    options["progress_hooks"] = [hook]
    options["postprocessor_hooks"] = [
        lambda data: emit("processing", data.get("postprocessor") or "Processing")
    ]
    options["logger"] = DownloadLogger()
    try:
        with create_downloader(options) as downloader:
            result = downloader.download([request["url"]])
        if result:
            emit("error", "Downloader returned an unsuccessful result.")
            return 1
        return 0
    except Exception as exc:
        emit("error", str(exc))
        return 1


if __name__ == "__main__":
    sys.exit(main())
