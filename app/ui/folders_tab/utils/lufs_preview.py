from app.ui.folders_tab.utils.lufs_runner import LufsRunner
from pathlib import Path

from app.core.logger import logger

def start_lufs_analysis(path: Path, preview_box, thread_pool):
    preview_box.show_text_loader("Analyzing")

    def handle_result(file_path: Path, lufs: dict):
        if file_path != path:
            return

        if "error" in lufs:
            logger.warning(f"LUFS analysis failed for {file_path.name}: {lufs['error']}")
        else:
            logger.info(f"LUFS Analysis for: {file_path.name}")
            logger.console("\n---\n" + "\n".join([
                f"{'Integrated':<13} : {lufs['input_i']} LUFS",
                f"{'True Peak':<12} : {lufs['input_tp']} dBTP",
                f"{'LRA':<10}       : {lufs['input_lra']} dB",
                f"{'Threshold':<12} : {lufs['input_thresh']} dB",
            ]))


        if preview_box.isVisible():
            preview_box.stop_text_loader()
            if "error" in lufs:
                preview_box.set_text(f"<i>{lufs['error']}</i>")
            else:
                preview_box.set_text(
                    f"<b>{path.name}</b><br><br>"
                    f"<b>Integrated:</b> {lufs['input_i']} LUFS<br>"
                    f"<b>True Peak:</b> {lufs['input_tp']} dBTP<br>"
                    f"<b>LRA:</b> {lufs['input_lra']} dB<br>"
                    f"<b>Threshold:</b> {lufs['input_thresh']} dB"
                )

    runner = LufsRunner(path)
    runner.signals.finished.connect(handle_result)
    preview_box.active_lufs_runner = runner
    thread_pool.start(runner)

