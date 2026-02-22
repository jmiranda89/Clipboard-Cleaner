"""Text-cleaning utilities for clipboard content."""

from __future__ import annotations

from dataclasses import dataclass

_IGNORABLE_DESTINATIONS = {
    "fonttbl",
    "colortbl",
    "stylesheet",
    "info",
    "pict",
    "object",
    "fldinst",
    "fldrslt",
    "header",
    "footer",
    "headerl",
    "headerr",
    "footerl",
    "footerr",
    "annotation",
    "datastore",
    "xmlnstbl",
    "listtable",
    "listoverridetable",
    "generator",
}


@dataclass(frozen=True)
class StyledRun:
    text: str
    bold: bool = False
    italic: bool = False


@dataclass(frozen=True)
class CleanClipboardContent:
    plain_text: str
    styled_runs: tuple[StyledRun, ...] = ()
    rtf: str | None = None


def clean_text(text: str | None) -> str:
    """Return plain text while preserving structure and readable spacing."""
    if text is None:
        return ""

    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = normalized.replace("\u00A0", " ")
    return normalized


def clean_clipboard_content(
    text: str | None,
    rtf: str | None,
    keep_bold_italic: bool = False,
) -> CleanClipboardContent:
    """Clean clipboard content, optionally preserving bold/italic via RTF."""
    plain_text = clean_text(text)
    if not keep_bold_italic or not rtf:
        return CleanClipboardContent(plain_text=plain_text)

    styled_runs = _parse_rtf_runs(rtf)
    if not styled_runs:
        return CleanClipboardContent(plain_text=plain_text)

    cleaned_runs = _clean_runs(styled_runs)
    if not cleaned_runs:
        return CleanClipboardContent(plain_text=plain_text)

    styled_plain_text = "".join(run.text for run in cleaned_runs)
    cleaned_plain = clean_text(styled_plain_text)
    if not cleaned_plain:
        return CleanClipboardContent(plain_text=plain_text)

    cleaned_styled_runs = _reapply_cleaning_to_runs(cleaned_runs)
    cleaned_rtf = _build_minimal_rtf(cleaned_styled_runs)
    return CleanClipboardContent(
        plain_text=cleaned_plain,
        styled_runs=tuple(cleaned_styled_runs),
        rtf=cleaned_rtf,
    )


def _parse_rtf_runs(rtf: str) -> list[StyledRun]:
    if not rtf.lstrip().startswith("{\\rtf"):
        return []

    stack = [{"bold": False, "italic": False, "ignorable": False, "uc": 1}]
    runs: list[StyledRun] = []
    i = 0
    length = len(rtf)
    pending_star = False
    skip_chars = 0

    def append_text(text: str) -> None:
        if not text:
            return
        state = stack[-1]
        if state["ignorable"]:
            return
        bold = bool(state["bold"])
        italic = bool(state["italic"])
        if runs and runs[-1].bold == bold and runs[-1].italic == italic:
            runs[-1] = StyledRun(text=runs[-1].text + text, bold=bold, italic=italic)
            return
        runs.append(StyledRun(text=text, bold=bold, italic=italic))

    while i < length:
        ch = rtf[i]
        if ch == "{":
            stack.append(dict(stack[-1]))
            pending_star = False
            i += 1
            continue
        if ch == "}":
            if len(stack) > 1:
                stack.pop()
            pending_star = False
            i += 1
            continue
        if ch != "\\":
            if skip_chars > 0:
                skip_chars -= 1
                i += 1
                continue
            append_text(ch)
            i += 1
            continue

        i += 1
        if i >= length:
            break

        control = rtf[i]
        if control in "{}\\":
            if skip_chars > 0:
                skip_chars -= 1
            else:
                append_text(control)
            i += 1
            continue
        if control == "*":
            pending_star = True
            i += 1
            continue
        if control == "'":
            if i + 2 < length:
                hex_part = rtf[i + 1 : i + 3]
                try:
                    char = bytes.fromhex(hex_part).decode("cp1252", errors="replace")
                    if skip_chars > 0:
                        skip_chars -= 1
                    else:
                        append_text(char)
                except ValueError:
                    pass
                i += 3
                continue
            i += 1
            continue
        if control in "~_-":
            if control == "~":
                append_text(" ")
            elif control == "_":
                append_text("-")
            i += 1
            continue
        if control == "\n" or control == "\r":
            i += 1
            continue

        if not control.isalpha():
            i += 1
            continue

        start = i
        while i < length and rtf[i].isalpha():
            i += 1
        word = rtf[start:i].lower()

        sign = 1
        if i < length and rtf[i] == "-":
            sign = -1
            i += 1

        number: int | None = None
        num_start = i
        while i < length and rtf[i].isdigit():
            i += 1
        if i > num_start:
            number = sign * int(rtf[num_start:i])

        if i < length and rtf[i] == " ":
            i += 1

        state = stack[-1]
        if pending_star:
            state["ignorable"] = True
            pending_star = False

        if word in _IGNORABLE_DESTINATIONS:
            state["ignorable"] = True
            continue
        if word == "b":
            state["bold"] = number != 0 if number is not None else True
            continue
        if word == "i":
            state["italic"] = number != 0 if number is not None else True
            continue
        if word == "plain":
            state["bold"] = False
            state["italic"] = False
            continue
        if word == "uc":
            state["uc"] = number if number is not None and number >= 0 else 1
            continue
        if word in {"par", "line"}:
            append_text("\n")
            continue
        if word == "tab":
            append_text("\t")
            continue
        if word == "u" and number is not None:
            if number < 0:
                number += 65536
            try:
                append_text(chr(number))
            except ValueError:
                append_text("\uFFFD")
            skip_chars = int(state["uc"])
            continue

    return runs


def _clean_runs(runs: list[StyledRun]) -> list[StyledRun]:
    cleaned: list[StyledRun] = []
    for run in runs:
        normalized = clean_text(run.text)
        if not normalized:
            continue
        if cleaned and cleaned[-1].bold == run.bold and cleaned[-1].italic == run.italic:
            last = cleaned[-1]
            cleaned[-1] = StyledRun(text=last.text + normalized, bold=last.bold, italic=last.italic)
            continue
        cleaned.append(StyledRun(text=normalized, bold=run.bold, italic=run.italic))
    return cleaned


def _reapply_cleaning_to_runs(runs: list[StyledRun]) -> list[StyledRun]:
    if not runs:
        return []

    cleaned_runs: list[StyledRun] = []
    for run in runs:
        text = run.text.replace("\r\n", "\n").replace("\r", "\n").replace("\u00A0", " ")
        if not text:
            continue
        if cleaned_runs and cleaned_runs[-1].bold == run.bold and cleaned_runs[-1].italic == run.italic:
            prev = cleaned_runs[-1]
            cleaned_runs[-1] = StyledRun(text=prev.text + text, bold=prev.bold, italic=prev.italic)
            continue
        cleaned_runs.append(StyledRun(text=text, bold=run.bold, italic=run.italic))
    return cleaned_runs


def _build_minimal_rtf(runs: list[StyledRun]) -> str:
    parts = [
        r"{\rtf1\ansi\deff0",
        r"{\fonttbl{\f0 Calibri;}}",
        r"\viewkind4\uc1\pard\f0\fs22 ",
    ]
    bold = False
    italic = False

    for run in runs:
        if run.bold != bold:
            parts.append(r"\b " if run.bold else r"\b0 ")
            bold = run.bold
        if run.italic != italic:
            parts.append(r"\i " if run.italic else r"\i0 ")
            italic = run.italic
        parts.append(_escape_rtf_text(run.text))

    if bold:
        parts.append(r"\b0 ")
    if italic:
        parts.append(r"\i0 ")
    parts.append("}")
    return "".join(parts)


def _escape_rtf_text(text: str) -> str:
    escaped: list[str] = []
    for ch in text:
        code = ord(ch)
        if ch == "\\":
            escaped.append(r"\\")
        elif ch == "{":
            escaped.append(r"\{")
        elif ch == "}":
            escaped.append(r"\}")
        elif ch == "\n":
            escaped.append(r"\par " + "\n")
        elif ch == "\t":
            escaped.append(r"\tab ")
        elif 32 <= code <= 126:
            escaped.append(ch)
        else:
            signed = code if code <= 32767 else code - 65536
            escaped.append(rf"\u{signed}?")
    return "".join(escaped)
