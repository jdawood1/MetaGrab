"""Run analysis in a fresh process so updated downloader packages are loaded."""

import json
import sys

from app.systems.download_system.analysis import analyze_media


def main():
    request = json.loads(sys.stdin.readline())
    try:
        report = analyze_media(
            request["url"], request["tools"], request.get("privacy"), return_details=True
        )
        print(json.dumps(report), flush=True)
        return 0
    except Exception as exc:
        print(json.dumps({"error": str(exc)}), flush=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
