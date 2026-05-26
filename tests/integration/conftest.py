"""Conftest for integration tests.

The `reflex_web_app` fixture is inherited from the central tests/conftest.py.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.helpers import navigate_to_app, navigate_to_app_with_path

if TYPE_CHECKING:
    from pathlib import Path

    from playwright.sync_api import Page
    from reflex.testing import AppHarness


@pytest.fixture
def app_page(reflex_web_app: AppHarness, page: Page) -> Page:
    """Navigate to the app's frontend URL and return the page."""
    return navigate_to_app(reflex_web_app, page)


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
def cli_app_page(reflex_web_app: AppHarness, page: Page, test_folder: Path, monkeypatch: pytest.MonkeyPatch) -> Page:
    """Navigate to the app with an initial path set via environment variable."""
    return navigate_to_app_with_path(reflex_web_app, page, test_folder, monkeypatch)


@pytest.fixture
def file_watch_page(
    reflex_web_app: AppHarness, page: Page, test_folder_with_file: Path, monkeypatch: pytest.MonkeyPatch
) -> Page:
    """Navigate to the app with a watchable file folder."""
    return navigate_to_app_with_path(reflex_web_app, page, test_folder_with_file, monkeypatch)


@pytest.fixture
def multi_file_page(
    reflex_web_app: AppHarness, page: Page, test_folder_with_multiple_files: Path, monkeypatch: pytest.MonkeyPatch
) -> Page:
    """Navigate to the app with a multiple files folder."""
    return navigate_to_app_with_path(reflex_web_app, page, test_folder_with_multiple_files, monkeypatch)
