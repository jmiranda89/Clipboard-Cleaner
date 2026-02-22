from clipboard_cleaner.cleaning import clean_clipboard_content, clean_text


def test_none_returns_empty_string():
    assert clean_text(None) == ""


def test_windows_and_old_mac_newlines_normalized():
    assert clean_text("a\r\nb\rc") == "a\nb\nc"


def test_non_breaking_spaces_replaced():
    assert clean_text("a\u00A0b") == "a b"


def test_tabs_and_spacing_preserved():
    assert clean_text("\titem  1\n\titem  2") == "\titem  1\n\titem  2"


def test_clean_clipboard_content_keeps_bold_italic_from_rtf():
    rtf = r"{\rtf1\ansi Normal \b bold\b0  and \i italic\i0 .}"
    content = clean_clipboard_content(
        text="Normal bold and italic.",
        rtf=rtf,
        keep_bold_italic=True,
    )

    assert content.plain_text == "Normal bold and italic."
    assert len(content.styled_runs) >= 3
    assert any(run.bold for run in content.styled_runs)
    assert any(run.italic for run in content.styled_runs)
    assert content.rtf is not None
    assert r"\b " in content.rtf
    assert r"\i " in content.rtf
    assert "fonttbl" in content.rtf
    assert "<html" not in content.rtf.lower()


def test_clean_clipboard_content_without_rtf_falls_back_to_plain_text():
    content = clean_clipboard_content(
        text="A\r\nB\u00A0C",
        rtf=None,
        keep_bold_italic=True,
    )
    assert content.plain_text == "A\nB C"
    assert content.styled_runs == ()
    assert content.rtf is None
