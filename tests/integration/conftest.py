"""Conftest for integration tests.

Shared fixtures like `reflex_web_app`, `app_page`, and `runner` are inherited
from the central tests/conftest.py.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.conftest import create_app_harness_with_path, navigate_to_app

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

    from playwright.sync_api import Page
    from reflex.testing import AppHarness


@pytest.fixture
def test_folder(tmp_path: Path) -> Path:
    """Create a test folder with some files for the file explorer."""
    test_dir = tmp_path / "test_project"
    test_dir.mkdir()
    (test_dir / "file1.py").write_text("print('hello')")
    (test_dir / "file2.txt").write_text("some text")
    (test_dir / "subdir").mkdir()
    (test_dir / "subdir" / "nested.py").write_text("# nested")
    return test_dir


@pytest.fixture
def test_folder_with_file(tmp_path: Path) -> Path:
    """Create a test folder with a Python file for testing file watching."""
    test_dir = tmp_path / "watch_test_project"
    test_dir.mkdir()
    (test_dir / "watched_file.py").write_text("# Original content\nprint('hello')")
    return test_dir


@pytest.fixture
def test_folder_with_multiple_files(tmp_path: Path) -> Path:
    """Create a test folder with multiple Python files for testing tab switching."""
    test_dir = tmp_path / "multi_file_project"
    test_dir.mkdir()
    (test_dir / "first_file.py").write_text("# First file content")
    (test_dir / "second_file.py").write_text("# Second file content")
    return test_dir


@pytest.fixture
def app_with_initial_path(test_folder: Path) -> Generator[AppHarness, None, None]:
    """Start the app with an initial path set via environment variable."""
    yield from create_app_harness_with_path(test_folder)


@pytest.fixture
def cli_app_page(app_with_initial_path: AppHarness, page: Page) -> Page:
    """Navigate to the app's frontend URL and return the page."""
    return navigate_to_app(app_with_initial_path, page)


@pytest.fixture
def app_with_watchable_file(test_folder_with_file: Path) -> Generator[AppHarness, None, None]:
    """Start the app with a test folder containing a watchable file."""
    yield from create_app_harness_with_path(test_folder_with_file)


@pytest.fixture
def file_watch_page(app_with_watchable_file: AppHarness, page: Page) -> Page:
    """Navigate to the app's frontend URL and return the page."""
    return navigate_to_app(app_with_watchable_file, page)


@pytest.fixture
def app_with_multiple_files(test_folder_with_multiple_files: Path) -> Generator[AppHarness, None, None]:
    """Start the app with a test folder containing multiple files."""
    yield from create_app_harness_with_path(test_folder_with_multiple_files)


@pytest.fixture
def multi_file_page(app_with_multiple_files: AppHarness, page: Page) -> Page:
    """Navigate to the app's frontend URL and return the page."""
    return navigate_to_app(app_with_multiple_files, page)
