# app/styles/theme.py

from PySide6.QtWidgets import QApplication
from app.core.resource_path import resource_path

_current_theme = "dark"  # private module-level variable

def apply_theme(app: QApplication, theme: str = "dark") -> None:
    """
    Applies the QSS theme to the given application.
    """
    global _current_theme
    _current_theme = theme

    try:
        qss_path = resource_path(f"app/styles/{theme}.qss")
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print(f"[Theme] Warning: Theme '{theme}' not found. Skipping style application.")

def toggle_theme(app: QApplication) -> str:
    """
    Toggles between dark and light themes.
    """
    new_theme = "light" if _current_theme == "dark" else "dark"
    apply_theme(app, new_theme)
    return new_theme

def current_theme() -> str:
    """
    Returns the currently applied theme name.
    """
    return _current_theme
