from clipboard_cleaner.cleaning import clean_text


def test_none_returns_empty_string():
    assert clean_text(None) == ""


def test_windows_and_old_mac_newlines_normalized():
    assert clean_text("a\r\nb\rc") == "a\nb\nc"


def test_non_breaking_spaces_replaced():
    assert clean_text("a\u00A0b") == "a b"


def test_tabs_and_spacing_preserved():
    assert clean_text("\titem  1\n\titem  2") == "\titem  1\n\titem  2"
