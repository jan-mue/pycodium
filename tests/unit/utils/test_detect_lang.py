from pycodium.utils.detect_lang import detect_programming_language


def test_detect_programming_language_python() -> None:
    assert detect_programming_language("foo.py").lower() == "python"


def test_detect_programming_language_js() -> None:
    assert detect_programming_language("foo.js").lower() == "javascript"


def test_detect_programming_language_unknown() -> None:
    assert detect_programming_language("foo.unknown") == "undefined"
