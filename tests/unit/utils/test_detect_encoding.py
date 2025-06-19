from pycodium.utils.detect_encoding import decode, get_encoding


def test_get_encoding_utf8() -> None:
    text = b"# coding: utf-8\nprint('hi')"
    assert get_encoding(text) == "utf-8"


def test_get_encoding_default() -> None:
    text = b"print('hi')"
    assert get_encoding(text, default_encoding="utf-8") == "utf-8"


def test_decode_utf8() -> None:
    text = b"hello"
    decoded, encoding = decode(text)
    assert decoded == "hello"
    assert encoding == "ascii"


def test_decode_utf16() -> None:
    text = b"\xff\xfeh\x00i\x00"
    decoded, encoding = decode(text)
    assert "hi" in decoded
    assert encoding.startswith("utf-16")
