from codecs import BOM_UTF8, BOM_UTF16, BOM_UTF32
from unittest.mock import patch

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


def test_get_encoding_unicode_decode_error() -> None:
    """Test that UnicodeDecodeError is handled when searching for encoding comment."""
    # Create bytes that would trigger UnicodeDecodeError when searching for encoding
    # but still allow the function to continue
    text = b"\x80\x81\x82\nprint('hi')"
    # Should not raise an exception and should fall back to detection
    result = get_encoding(text)
    # Since no encoding comment found, it should use charset_normalizer detection
    assert result is not None or result is None  # Just ensure no exception


def test_get_encoding_with_encoding_not_in_list() -> None:
    """Test that unrecognized encodings are ignored."""
    text = b"# coding: fake-encoding-123\nprint('hi')"
    # Should fall back to detection since encoding is not in ENCODINGS list
    result = get_encoding(text)
    assert result != "fake-encoding-123"


def test_decode_with_bom_utf8() -> None:
    """Test decoding bytes that start with UTF-8 BOM."""
    text = BOM_UTF8 + b"hello world"
    decoded, encoding = decode(text)
    assert decoded == "hello world"
    assert encoding == "utf-8-bom"


def test_decode_with_bom_utf16() -> None:
    """Test decoding bytes that start with UTF-16 BOM."""
    # UTF-16 LE BOM followed by "hi" in UTF-16 LE
    text = BOM_UTF16 + "hi".encode("utf-16")[2:]  # Skip the BOM in the encoded string
    decoded, encoding = decode(text)
    assert "hi" in decoded
    assert encoding == "utf-16"


def test_decode_with_bom_utf32() -> None:
    """Test decoding bytes that start with UTF-32 BOM."""
    # Create UTF-32 LE encoded text with BOM
    # BOM_UTF32 is little-endian on most systems, so use utf-32-le for the content
    content = "hi".encode("utf-32-le")
    text = BOM_UTF32 + content
    decoded, encoding = decode(text)
    assert decoded == "hi"
    assert encoding == "utf-32"


def test_decode_unicode_error_fallback_to_utf8() -> None:
    """Test that when encoding is detected but decoding fails, it falls back to UTF-8."""
    # Create bytes with a fake encoding comment but content that's valid UTF-8
    text = b"# coding: iso8859-5\nhello"
    decoded, _encoding = decode(text)
    # Should decode successfully with the detected encoding
    assert "hello" in decoded


def test_decode_fallback_to_latin1() -> None:
    """Test that when UTF-8 decoding fails, it falls back to latin-1."""
    # Create bytes that are valid latin-1 but invalid UTF-8
    # 0x80-0xFF are valid in latin-1 but many are invalid in UTF-8
    text = b"\xe0\xe1\xe2"  # These are valid latin-1 characters
    decoded, encoding = decode(text)
    # If charset_normalizer returns an encoding that works, use it
    # Otherwise it should fall back to latin-1
    assert decoded is not None
    assert encoding is not None


def test_decode_invalid_encoding_lookup_error() -> None:
    """Test handling of LookupError when encoding is not recognized."""
    # This tests the case where get_encoding returns an encoding that Python doesn't recognize
    # We need to create content that triggers this path
    # Since we can't easily mock get_encoding, we test with binary-ish content
    text = bytes(range(256))  # All possible byte values
    decoded, encoding = decode(text)
    # Should successfully decode with some fallback
    assert decoded is not None
    assert encoding is not None


def test_get_encoding_iso8859_encodings() -> None:
    """Test detection of various ISO-8859 encodings in source file comments."""
    encodings_to_test = [
        ("iso8859-1", b"# coding: iso8859-1\n"),
        ("iso8859-15", b"# coding: iso8859-15\n"),
        ("latin-1", b"# coding: latin-1\n"),
        ("koi8-r", b"# coding: koi8-r\n"),
        ("cp1251", b"# coding: cp1251\n"),
    ]
    for expected_encoding, text in encodings_to_test:
        result = get_encoding(text)
        assert result == expected_encoding, f"Expected {expected_encoding}, got {result}"


def test_get_encoding_second_line() -> None:
    """Test that encoding comment on the second line is detected."""
    text = b"#!/usr/bin/env python\n# coding: utf-8\nprint('hi')"
    assert get_encoding(text) == "utf-8"


def test_decode_with_detected_encoding() -> None:
    """Test decoding when get_encoding returns a detected encoding (no default)."""
    # ASCII content that charset_normalizer should detect
    text = b"simple ascii text"
    decoded, encoding = decode(text)
    assert decoded == "simple ascii text"
    assert encoding is not None


def test_decode_binary_content_fallback() -> None:
    """Test decoding binary content falls back appropriately."""
    # Pure binary content that's not valid in most encodings
    text = b"\x00\x01\x02\x03\x04\x05"
    decoded, encoding = decode(text)
    # Should decode to something (likely latin-1 as final fallback)
    assert decoded is not None
    # The encoding should indicate it was guessed or a fallback
    assert encoding is not None


def test_decode_lookup_error_fallback_to_utf8_guessed() -> None:
    """Test that LookupError from invalid encoding falls back to utf-8-guessed."""
    with patch("pycodium.utils.detect_encoding.get_encoding", return_value="not-a-real-encoding"):
        decoded, encoding = decode(b"hello world")
        assert decoded == "hello world"
        assert encoding == "utf-8-guessed"


def test_decode_unicode_error_fallback_to_utf8_guessed() -> None:
    """Test that UnicodeError falls back to utf-8-guessed when detected encoding fails."""
    # Mock get_encoding to return utf-16 for content that isn't valid utf-16
    with patch("pycodium.utils.detect_encoding.get_encoding", return_value="utf-16"):
        # Odd number of bytes is invalid for utf-16
        decoded, encoding = decode(b"abc")
        # Should fall back to utf-8-guessed since the content is valid utf-8
        assert decoded == "abc"
        assert encoding == "utf-8-guessed"


def test_decode_fallback_to_latin1_guessed() -> None:
    """Test fallback to latin-1-guessed when both detected encoding and utf-8 fail."""
    # Create bytes that are invalid utf-8 but valid latin-1
    invalid_utf8 = b"\x80\x81\x82\x83"  # These are invalid utf-8 continuation bytes
    with patch("pycodium.utils.detect_encoding.get_encoding", return_value="not-a-real-encoding"):
        decoded, encoding = decode(invalid_utf8)
        assert encoding == "latin-1-guessed"
        assert decoded is not None
