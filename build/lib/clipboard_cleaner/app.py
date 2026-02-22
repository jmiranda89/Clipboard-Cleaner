"""Tkinter UI for the clipboard cleaner app."""

from __future__ import annotations

import time
import tkinter as tk
from tkinter import ttk

from .cleaning import clean_text

POLL_MS = 500


class ClipboardCleanerApp(tk.Tk):
    def __init__(self, auto_mode: bool = False):
        super().__init__()
        self.title("Clipboard Cleaner")
        self.geometry("860x560")
        self.minsize(700, 420)

        self.last_clipboard_text: str | None = None
        self.auto_mode = tk.BooleanVar(value=auto_mode)

        self._build_ui()
        self._schedule_poll()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        controls = ttk.Frame(self, padding=12)
        controls.grid(row=0, column=0, sticky="ew")

        ttk.Button(controls, text="Read Clipboard", command=self.read_clipboard).pack(side="left")
        ttk.Button(controls, text="Copy Clean Text", command=self.copy_clean_text).pack(side="left", padx=8)
        ttk.Button(controls, text="Clear", command=self.clear_editor).pack(side="left")

        ttk.Checkbutton(
            controls,
            text="Auto-clean new clipboard text",
            variable=self.auto_mode,
        ).pack(side="left", padx=16)

        editor_frame = ttk.Frame(self, padding=(12, 0, 12, 12))
        editor_frame.grid(row=1, column=0, sticky="nsew")
        editor_frame.rowconfigure(0, weight=1)
        editor_frame.columnconfigure(0, weight=1)

        self.text_editor = tk.Text(editor_frame, wrap="word", undo=True)
        self.text_editor.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(editor_frame, orient="vertical", command=self.text_editor.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.text_editor.configure(yscrollcommand=scrollbar.set)

        status_bar = ttk.Frame(self, padding=(12, 0, 12, 12))
        status_bar.grid(row=2, column=0, sticky="ew")

        self.status_label = ttk.Label(status_bar, text="Ready.")
        self.status_label.pack(side="left")

        ttk.Button(status_bar, text="Quit", command=self.destroy).pack(side="right")

    def _set_status(self, message: str) -> None:
        self.status_label.configure(text=message)

    def _get_clipboard_text(self) -> str:
        try:
            return self.clipboard_get()
        except tk.TclError:
            return ""

    def _set_clipboard_text(self, text: str) -> None:
        self.clipboard_clear()
        self.clipboard_append(text)
        try:
            self.update_idletasks()
        except Exception:
            pass

    def read_clipboard(self) -> None:
        cleaned = clean_text(self._get_clipboard_text())
        self.text_editor.delete("1.0", "end")
        self.text_editor.insert("1.0", cleaned)
        self._set_status(f"Loaded {len(cleaned)} characters from clipboard.")

    def copy_clean_text(self) -> None:
        current = self.text_editor.get("1.0", "end-1c")
        cleaned = clean_text(current)
        self._set_clipboard_text(cleaned)
        self._set_status("Copied clean plain text to clipboard.")

    def clear_editor(self) -> None:
        self.text_editor.delete("1.0", "end")
        self._set_status("Cleared editor.")

    def _schedule_poll(self) -> None:
        self.after(POLL_MS, self._poll_clipboard)

    def _poll_clipboard(self) -> None:
        try:
            if self.auto_mode.get():
                raw = self._get_clipboard_text()
                if raw and raw != self.last_clipboard_text:
                    cleaned = clean_text(raw)
                    self._set_clipboard_text(cleaned)
                    self.last_clipboard_text = cleaned
                    self.text_editor.delete("1.0", "end")
                    self.text_editor.insert("1.0", cleaned)
                    now = time.strftime("%H:%M:%S")
                    self._set_status(f"Auto-cleaned clipboard at {now}.")
            else:
                current = self._get_clipboard_text()
                if current:
                    self.last_clipboard_text = current
        finally:
            self._schedule_poll()


def run_gui(auto_mode: bool = False) -> None:
    app = ClipboardCleanerApp(auto_mode=auto_mode)
    app.mainloop()
