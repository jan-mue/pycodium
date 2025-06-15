"""Utilities for detecting the programming language of a file."""

import logging
import time

from pygments.lexers import get_lexer_for_filename
from pygments.util import ClassNotFound

logger = logging.getLogger(__name__)


def detect_programming_language(filename: str) -> str:
    """Detect the programming language of a file based on its filename."""
    start_time = time.perf_counter()
    try:
        lexer = get_lexer_for_filename(filename)
        language = lexer.name
    except ClassNotFound:
        language = "undefined"
    logger.info(f"Detected language for '{filename}': {language} in {time.perf_counter() - start_time:.4f} seconds")
    return language
