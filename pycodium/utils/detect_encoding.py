"""Utilities for detecting the encoding of text files and decoding byte strings."""

import re
from codecs import BOM_UTF8, BOM_UTF16, BOM_UTF32

from charset_normalizer import detect

ENCODING_REGEX = re.compile(r"coding[:=]\s*([-\w_.]+)")
ENCODINGS = [
    "utf-8",
    "iso8859-1",
    "iso8859-15",
    "ascii",
    "koi8-r",
    "cp1251",
    "koi8-u",
    "iso8859-2",
    "iso8859-3",
    "iso8859-4",
    "iso8859-5",
    "iso8859-6",
    "iso8859-7",
    "iso8859-8",
    "iso8859-9",
    "iso8859-10",
    "iso8859-13",
    "iso8859-14",
    "latin-1",
    "utf-16",
]


def get_encoding(text: bytes, default_encoding: str | None = None) -> str | None:
    """Detect the encoding of a byte string."""
    for line in text.splitlines()[:2]:
        try:
            result = ENCODING_REGEX.search(str(line))
        except UnicodeDecodeError:  # noqa: PERF203
            # If the line cannot be decoded, skip it
            pass
        else:
            if result:
                encoding = result.group(1)
                if encoding in ENCODINGS:
                    return encoding

    if default_encoding is None:
        result = detect(text)
        return result["encoding"]

    return default_encoding


def decode(text: bytes, default_encoding: str | None = None) -> tuple[str, str]:
    """Decode a byte string to a string, guessing the encoding if necessary."""
    try:
        if text.startswith(BOM_UTF8):
            return str(text[len(BOM_UTF8) :], "utf-8"), "utf-8-bom"
        elif text.startswith(BOM_UTF16):
            return str(text[len(BOM_UTF16) :], "utf-16"), "utf-16"
        elif text.startswith(BOM_UTF32):
            return str(text[len(BOM_UTF32) :], "utf-32"), "utf-32"
        coding = get_encoding(text, default_encoding=default_encoding)
        if coding:
            return str(text, coding), coding
    except (UnicodeError, LookupError):
        pass
    try:
        return str(text, "utf-8"), "utf-8-guessed"
    except (UnicodeError, LookupError):
        pass
    return str(text, "latin-1"), "latin-1-guessed"
