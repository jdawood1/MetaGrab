from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)


def get_text(
    parent: QWidget, title: str, label: str, initial_text: str = "", width: int = 400
) -> str | None:
    """Text input dialog (e.g., for renaming)."""
    dialog = QDialog(parent)
    dialog.setWindowTitle(title)
    dialog.setFixedWidth(width)

    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(15)

    # Styled label
    label_widget = QLabel(f'<span style="font-weight: bold; font-size: 15px;">{label}</span>')
    label_widget.setTextFormat(Qt.RichText)
    layout.addWidget(label_widget)

    input_field = QLineEdit()
    input_field.setText(initial_text)
    input_field.setObjectName("DialogLineEdit")
    input_field.setFocus()

    text = input_field.text()
    dot_index = text.rfind(".")
    if dot_index > 0:
        input_field.setSelection(0, dot_index)
    else:
        input_field.selectAll()

    layout.addWidget(input_field)
    button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    layout.addWidget(button_box)

    button_box.accepted.connect(dialog.accept)
    button_box.rejected.connect(dialog.reject)

    if dialog.exec() == QDialog.Accepted:
        return input_field.text().strip()
    return None


def get_confirmation(parent: QWidget, title: str, message: str, default=QMessageBox.No) -> bool:
    """Yes/No confirmation dialog."""
    reply = QMessageBox.information(
        parent, title, message, QMessageBox.Yes | QMessageBox.No, default
    )
    return reply == QMessageBox.Yes


def confirm_overwrite(parent: QWidget, path: Path) -> bool:
    """Ask if a user wants to overwrite a file that already exists."""
    return get_confirmation(
        parent,
        "File Exists",
        f"The file '<b>{path.name}</b>' already exists.<br>Do you want to <span style='color:#FF3B30;'>overwrite</span> it?",
        default=QMessageBox.No,
    )


def confirm_delete(parent: QWidget, path: Path) -> bool:
    """Ask if the user wants to delete a file."""
    return get_confirmation(
        parent,
        "Confirm Delete",
        f"Are you sure you want to delete '<b>{path.name}</b>'?",
        default=QMessageBox.No,
    )


def show_info(parent: QWidget, title: str, message: str):
    """Informational message dialog."""
    QMessageBox.information(parent, title, message)
