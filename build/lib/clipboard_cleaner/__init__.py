"""Clipboard Cleaner package."""

from .app import ClipboardCleanerApp, run_gui
from .cleaning import clean_text

__all__ = ["ClipboardCleanerApp", "run_gui", "clean_text"]
__version__ = "1.0.0"
