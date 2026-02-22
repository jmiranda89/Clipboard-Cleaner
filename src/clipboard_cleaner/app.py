"""Tkinter UI for the clipboard cleaner app."""

from __future__ import annotations

import time
import tkinter as tk
from tkinter import ttk

from .cleaning import CleanClipboardContent, clean_clipboard_content, clean_text

POLL_MS = 500
RTF_TYPES = ("public.rtf", "RTF", "text/rtf")


class ClipboardCleanerApp(tk.Tk):
    def __init__(self, auto_mode: bool = False):
        super().__init__()
        self.title("Clipboard Cleaner")
        self.geometry("860x560")
        self.minsize(700, 420)

        self.last_clipboard_text: str | None = None
        self.last_clipboard_rtf: str | None = None
        self.last_loaded_content = CleanClipboardContent(plain_text="")
        self.auto_mode = tk.BooleanVar(value=auto_mode)
        self.keep_bold_italic_mode = tk.BooleanVar(value=False)

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
        ttk.Checkbutton(
            controls,
            text="Keep bold/italic (Word RTF)",
            variable=self.keep_bold_italic_mode,
        ).pack(side="left")

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

    def _get_clipboard_rtf(self) -> str:
        for rtf_type in RTF_TYPES:
            try:
                content = self.clipboard_get(type=rtf_type)
            except tk.TclError:
                continue
            if content:
                return content
        return ""

    def _set_clipboard_content(self, text: str, rtf: str | None = None) -> None:
        self.clipboard_clear()
        self.clipboard_append(text)
        if rtf:
            for rtf_type in RTF_TYPES:
                try:
                    self.clipboard_append(rtf, type=rtf_type)
                    break
                except tk.TclError:
                    continue
        try:
            self.update_idletasks()
        except Exception:
            pass

    def _render_content(self, content: CleanClipboardContent) -> None:
        self.text_editor.delete("1.0", "end")
        if not content.styled_runs:
            self.text_editor.insert("1.0", content.plain_text)
            return

        self.text_editor.tag_configure("bold", font=("TkDefaultFont", 10, "bold"))
        self.text_editor.tag_configure("italic", font=("TkDefaultFont", 10, "italic"))
        self.text_editor.tag_configure("bold_italic", font=("TkDefaultFont", 10, "bold italic"))

        index = "1.0"
        for run in content.styled_runs:
            self.text_editor.insert(index, run.text)
            end = self.text_editor.index(f"{index}+{len(run.text)}c")
            if run.bold and run.italic:
                self.text_editor.tag_add("bold_italic", index, end)
            elif run.bold:
                self.text_editor.tag_add("bold", index, end)
            elif run.italic:
                self.text_editor.tag_add("italic", index, end)
            index = end

    def read_clipboard(self) -> None:
        raw_text = self._get_clipboard_text()
        raw_rtf = self._get_clipboard_rtf()
        content = clean_clipboard_content(
            text=raw_text,
            rtf=raw_rtf,
            keep_bold_italic=self.keep_bold_italic_mode.get(),
        )
        self.last_loaded_content = content
        self._render_content(content)
        if content.rtf:
            self._set_status(
                f"Loaded {len(content.plain_text)} characters (bold/italic preserved for Word)."
            )
        else:
            self._set_status(f"Loaded {len(content.plain_text)} characters from clipboard.")

    def copy_clean_text(self) -> None:
        current = self.text_editor.get("1.0", "end-1c")
        cleaned = clean_text(current)
        rtf = None
        if (
            self.keep_bold_italic_mode.get()
            and self.last_loaded_content.rtf
            and current == self.last_loaded_content.plain_text
        ):
            rtf = self.last_loaded_content.rtf
        self._set_clipboard_content(cleaned, rtf=rtf)
        if rtf:
            self._set_status("Copied clean text with Word-compatible bold/italic.")
        elif self.keep_bold_italic_mode.get():
            self._set_status("Copied clean plain text. (Bold/italic kept only when clipboard text is unchanged.)")
        else:
            self._set_status("Copied clean plain text to clipboard.")

    def clear_editor(self) -> None:
        self.text_editor.delete("1.0", "end")
        self._set_status("Cleared editor.")

    def _schedule_poll(self) -> None:
        self.after(POLL_MS, self._poll_clipboard)

    def _poll_clipboard(self) -> None:
        try:
            if self.auto_mode.get():
                raw_text = self._get_clipboard_text()
                raw_rtf = self._get_clipboard_rtf()
                if raw_text and (raw_text != self.last_clipboard_text or raw_rtf != self.last_clipboard_rtf):
                    content = clean_clipboard_content(
                        text=raw_text,
                        rtf=raw_rtf,
                        keep_bold_italic=self.keep_bold_italic_mode.get(),
                    )
                    self._set_clipboard_content(content.plain_text, rtf=content.rtf)
                    self.last_clipboard_text = content.plain_text
                    self.last_clipboard_rtf = content.rtf
                    self.last_loaded_content = content
                    self._render_content(content)
                    now = time.strftime("%H:%M:%S")
                    if content.rtf:
                        self._set_status(f"Auto-cleaned clipboard at {now} (kept bold/italic).")
                    else:
                        self._set_status(f"Auto-cleaned clipboard at {now}.")
            else:
                current = self._get_clipboard_text()
                if current:
                    self.last_clipboard_text = current
                self.last_clipboard_rtf = self._get_clipboard_rtf()
        finally:
            self._schedule_poll()


def run_gui(auto_mode: bool = False) -> None:
    app = ClipboardCleanerApp(auto_mode=auto_mode)
    app.mainloop()
