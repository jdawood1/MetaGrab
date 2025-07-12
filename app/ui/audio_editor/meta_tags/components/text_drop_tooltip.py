from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QToolButton, QDialog, QVBoxLayout, QTextEdit, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt


class MetadataHelpWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.help_button = QToolButton()
        self.help_button.setObjectName("MetadataHelpButton")
        self.help_button.setText("?")
        self.help_button.setCursor(Qt.PointingHandCursor)
        self.help_button.setToolTip("Click to view required .txt metadata format")
        self.help_button.clicked.connect(self.show_help_dialog)

        layout.addWidget(self.help_button, alignment=Qt.AlignTop | Qt.AlignLeft)

    def show_help_dialog(self):
        dialog = QDialog(self)
        dialog.setContentsMargins(0, 0, 0, 0)
        dialog.setWindowTitle("Metadata .txt Format")
        dialog.setMinimumWidth(560)
        dialog.setMinimumHeight(360)

        layout = QVBoxLayout(dialog)

        help_text = """
        <div style="color: #CCCCCC;">
            Format for metadata .txt file (case-insensitive):<br><br>
            <span style="color: yellow;">Title:</span> Iron Man<br>
            <span style="color: yellow;">Artist:</span> Black Sabbath<br>
            <span style="color: yellow;">Album:</span> Paranoid<br>
            <span style="color: yellow;">Album Artist:</span> Black Sabbath<br>
            <span style="color: yellow;">Genre:</span> Heavy Metal<br>
            <span style="color: yellow;">Year:</span> 1970<br>
            <span style="color: yellow;">Track:</span> 2/8<br>
            <span style="color: yellow;">Composer:</span> Iommi, Butler, Osbourne, Ward<br>
            <span style="color: yellow;">Comment:</span> Studio version, remastered<br>
            <span style="color: yellow;">Explicit:</span> No<br>
            <span style="color: yellow;">BPM:</span> 76<br>
            <span style="color: yellow;">Lyrics:</span> I - am - Iron - Man!<br><br>
    
            Has he lost his mind?<br>
            Can he see or is he blind?<br>
            Can he walk at all,<br>
            Or if he moves will he fall?<br><br>
    
            Is he alive or dead?<br>
            Has he thoughts within his head?<br>
            We'll just pass him there<br>
            Why should we even care?<br><br>
    
            He was turned to steel<br>
            In the great magnetic field<br>
            When he travelled time<br>
            For the future of mankind<br><br>
    
            Nobody wants him<br>
            He just stares at the world<br>
            Planning his vengeance<br>
            That he will soon unfold<br><br>
    
            Now the time is here<br>
            For Iron Man to spread fear<br>
            Vengeance from the grave<br>
            Kills the people he once saved<br><br>
    
            Nobody wants him<br>
            They just turn their heads<br>
            Nobody helps him<br>
            Now he has his revenge<br><br>
    
            Heavy bullets of lead<br>
            Fills his victims full of dread<br>
            Running as fast as they can<br>
            Iron Man lives again!
        </div>
        """

        help_label = QTextEdit()
        help_label.setReadOnly(True)
        help_label.setHtml(help_text)

        layout.addWidget(help_label)
        add_export_button_to_help_dialog(layout, parent=self)
        dialog.exec()


def add_export_button_to_help_dialog(dialog_layout, parent=None):
    export_button = QPushButton("Export Template to Desktop")
    export_button.setCursor(Qt.PointingHandCursor)

    def export_template():
        desktop_path = Path.home() / "Desktop"
        file_path = desktop_path / "metadata_template.txt"
        try:
            file_path.write_text("""\
Title:
Artist:
Album:
Album Artist:
Genre:
Year:
Track:
Composer:
Comment:
Explicit:
BPM:
Lyrics:
""")
            QMessageBox.information(parent, "Exported", f"Template saved to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(parent, "Error", f"Failed to export template:\n{e}")

    export_button.clicked.connect(export_template)
    dialog_layout.addWidget(export_button)