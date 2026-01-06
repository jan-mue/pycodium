"""Conftest for integration tests.

Integration test fixtures are inherited from the central tests/conftest.py.
Shared fixtures like `reflex_web_app`, `app_page`, and `runner` are defined there.

This file contains integration-test-specific fixtures that aren't needed
in other test types.
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
    """Create a test folder with some files for the file explorer.

    This fixture creates a basic project structure useful for testing
    file explorer functionality.

    Args:
        tmp_path: Pytest temporary path fixture.

    Returns:
        Path to the test folder.
    """
    test_dir = tmp_path / "test_project"
    test_dir.mkdir()
    (test_dir / "file1.py").write_text("print('hello')")
    (test_dir / "file2.txt").write_text("some text")
    (test_dir / "subdir").mkdir()
    (test_dir / "subdir" / "nested.py").write_text("# nested")
    return test_dir


@pytest.fixture
def test_folder_with_file(tmp_path: Path) -> Path:
    """Create a test folder with a Python file for testing file watching.

    Args:
        tmp_path: Pytest temporary path fixture.

    Returns:
        Path to the test folder.
    """
    test_dir = tmp_path / "watch_test_project"
    test_dir.mkdir()
    (test_dir / "watched_file.py").write_text("# Original content\nprint('hello')")
    return test_dir


@pytest.fixture
def test_folder_with_multiple_files(tmp_path: Path) -> Path:
    """Create a test folder with multiple Python files for testing tab switching.

    Args:
        tmp_path: Pytest temporary path fixture.

    Returns:
        Path to the test folder.
    """
    test_dir = tmp_path / "multi_file_project"
    test_dir.mkdir()
    (test_dir / "first_file.py").write_text("# First file content")
    (test_dir / "second_file.py").write_text("# Second file content")
    return test_dir


@pytest.fixture
def app_with_initial_path(test_folder: Path) -> Generator[AppHarness, None, None]:
    """Start the PyCodium Reflex app with an initial path set via environment variable.

    This sets the PYCODIUM_INITIAL_PATH environment variable to simulate
    what the Typer CLI does when invoked with a path argument.

    Args:
        test_folder: Path to the test folder fixture.

    Yields:
        Running AppHarness instance.
    """
    yield from create_app_harness_with_path(test_folder)


@pytest.fixture
def cli_app_page(app_with_initial_path: AppHarness, page: Page) -> Page:
    """Navigate to the app's frontend URL and return the page.

    Args:
        app_with_initial_path: The running AppHarness instance with initial path.
        page: Playwright page fixture.

    Returns:
        Playwright page navigated to the app's frontend URL.
    """
    return navigate_to_app(app_with_initial_path, page)


@pytest.fixture
def app_with_watchable_file(test_folder_with_file: Path) -> Generator[AppHarness, None, None]:
    """Start the PyCodium Reflex app with a test folder containing a watchable file.

    Args:
        test_folder_with_file: Path to the test folder with a watchable file.

    Yields:
        Running AppHarness instance.
    """
    yield from create_app_harness_with_path(test_folder_with_file)


@pytest.fixture
def file_watch_page(app_with_watchable_file: AppHarness, page: Page) -> Page:
    """Navigate to the app's frontend URL and return the page.

    Args:
        app_with_watchable_file: The running AppHarness instance.
        page: Playwright page fixture.

    Returns:
        Playwright page navigated to the app's frontend URL.
    """
    return navigate_to_app(app_with_watchable_file, page)


@pytest.fixture
def app_with_multiple_files(test_folder_with_multiple_files: Path) -> Generator[AppHarness, None, None]:
    """Start the PyCodium Reflex app with a test folder containing multiple files.

    Args:
        test_folder_with_multiple_files: Path to the test folder with multiple files.

    Yields:
        Running AppHarness instance.
    """
    yield from create_app_harness_with_path(test_folder_with_multiple_files)


@pytest.fixture
def multi_file_page(app_with_multiple_files: AppHarness, page: Page) -> Page:
    """Navigate to the app's frontend URL and return the page.

    Args:
        app_with_multiple_files: The running AppHarness instance.
        page: Playwright page fixture.

    Returns:
        Playwright page navigated to the app's frontend URL.
    """
    return navigate_to_app(app_with_multiple_files, page)
