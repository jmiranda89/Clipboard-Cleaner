"""Text-cleaning utilities for clipboard content."""


def clean_text(text: str | None) -> str:
    """Return plain text while preserving structure and readable spacing."""
    if text is None:
        return ""

    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = normalized.replace("\u00A0", " ")
    return normalized
