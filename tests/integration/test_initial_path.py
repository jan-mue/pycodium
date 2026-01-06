"""Integration tests for the PyCodium initial path functionality.

These tests verify that the initial path feature works correctly when
the PYCODIUM_INITIAL_PATH environment variable is set. This simulates
what happens when the CLI is invoked with a path argument.
"""

from __future__ import annotations

import os
import stat
from typing import TYPE_CHECKING

import pytest
from playwright.sync_api import Page, expect
from reflex.testing import AppHarness

from pycodium.constants import INITIAL_PATH_ENV_VAR, PROJECT_ROOT_DIR

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path


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
def app_with_initial_path(test_folder: Path) -> Generator[AppHarness, None, None]:
    """Start the PyCodium Reflex app with an initial path set via environment variable.

    This sets the PYCODIUM_INITIAL_PATH environment variable to simulate
    what the Typer CLI does when invoked with a path argument.
    """
    original_env = os.environ.get(INITIAL_PATH_ENV_VAR)
    os.environ[INITIAL_PATH_ENV_VAR] = str(test_folder)

    try:
        with AppHarness.create(root=PROJECT_ROOT_DIR) as harness:
            yield harness
    finally:
        if original_env is not None:
            os.environ[INITIAL_PATH_ENV_VAR] = original_env
        elif INITIAL_PATH_ENV_VAR in os.environ:
            del os.environ[INITIAL_PATH_ENV_VAR]


@pytest.fixture
def cli_app_page(app_with_initial_path: AppHarness, page: Page) -> Page:
    """Navigate to the app's frontend URL and return the page."""
    assert app_with_initial_path.frontend_url is not None
    page.goto(app_with_initial_path.frontend_url)
    page.wait_for_load_state("networkidle")
    return page


def test_cli_opens_folder_from_path_argument(cli_app_page: Page, test_folder: Path) -> None:
    """Test that the CLI correctly passes the initial path to the Reflex backend.

    This verifies that when the CLI is invoked with a path argument,
    the environment variable is set and inherited by the backend subprocess,
    resulting in the file explorer showing the contents of that folder.
    """
    folder_name = test_folder.name
    folder_item = cli_app_page.locator(f".folder-item:has-text('{folder_name}')")
    expect(folder_item).to_be_visible(timeout=10000)


def test_initial_path_folder_is_expanded_by_default(cli_app_page: Page, test_folder: Path) -> None:
    """Test that the opened folder is expanded by default in the file tree."""
    folder_name = test_folder.name
    folder_item = cli_app_page.locator(f".folder-item:has-text('{folder_name}')")
    expect(folder_item).to_be_visible(timeout=10000)
    file_item = cli_app_page.locator(".file-item:has-text('file1.py')")
    expect(file_item).to_be_visible(timeout=5000)


def test_initial_path_shows_all_files_in_folder(cli_app_page: Page) -> None:
    """Test that all files in the opened folder are visible in the file explorer."""
    file1 = cli_app_page.locator(".file-item:has-text('file1.py')")
    file2 = cli_app_page.locator(".file-item:has-text('file2.txt')")

    expect(file1).to_be_visible(timeout=5000)
    expect(file2).to_be_visible(timeout=5000)


def test_initial_path_shows_subdirectories(cli_app_page: Page) -> None:
    """Test that subdirectories in the opened folder are visible."""
    subdir = cli_app_page.locator(".folder-item:has-text('subdir')")
    expect(subdir).to_be_visible(timeout=5000)


@pytest.fixture
def test_folder_with_inaccessible_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a test folder with a subdirectory that has no read permissions."""
    test_dir = tmp_path / "permission_test_project"
    test_dir.mkdir()
    (test_dir / "readable_file.py").write_text("print('hello')")

    # Create a subdirectory with no read permissions
    restricted_dir = test_dir / "restricted"
    restricted_dir.mkdir()
    (restricted_dir / "secret.txt").write_text("secret content")

    # Remove read permission from the directory
    restricted_dir.chmod(stat.S_IWUSR | stat.S_IXUSR)  # Write and execute only, no read

    yield test_dir

    # Restore permissions for cleanup
    restricted_dir.chmod(stat.S_IRWXU)


@pytest.fixture
def app_with_inaccessible_dir(
    test_folder_with_inaccessible_dir: Path,
) -> Generator[AppHarness, None, None]:
    """Start the PyCodium Reflex app with a folder containing an inaccessible subdirectory."""
    original_env = os.environ.get(INITIAL_PATH_ENV_VAR)
    os.environ[INITIAL_PATH_ENV_VAR] = str(test_folder_with_inaccessible_dir)

    try:
        with AppHarness.create(root=PROJECT_ROOT_DIR) as harness:
            yield harness
    finally:
        if original_env is not None:
            os.environ[INITIAL_PATH_ENV_VAR] = original_env
        elif INITIAL_PATH_ENV_VAR in os.environ:
            del os.environ[INITIAL_PATH_ENV_VAR]


@pytest.fixture
def inaccessible_dir_page(app_with_inaccessible_dir: AppHarness, page: Page) -> Page:
    """Navigate to the app's frontend URL and return the page."""
    assert app_with_inaccessible_dir.frontend_url is not None
    page.goto(app_with_inaccessible_dir.frontend_url)
    page.wait_for_load_state("networkidle")
    return page


def test_expanding_inaccessible_directory_shows_toast(inaccessible_dir_page: Page) -> None:
    """Test that expanding an inaccessible directory shows an error toast.

    This verifies that when a user tries to expand a directory they don't have
    permission to read, a toast notification is displayed informing them of the error.
    """
    # Wait for the file explorer to load
    restricted_folder = inaccessible_dir_page.locator(".folder-item:has-text('restricted')")
    expect(restricted_folder).to_be_visible(timeout=10000)

    # Click on the restricted folder to try to expand it
    restricted_folder.click()
    inaccessible_dir_page.wait_for_timeout(500)

    # Verify that a toast error is shown
    toast = inaccessible_dir_page.locator("[data-sonner-toast][data-type='error']")
    expect(toast).to_be_visible(timeout=5000)

    # Verify the toast message mentions the folder name
    toast_message = inaccessible_dir_page.locator("[data-sonner-toast][data-type='error']")
    expect(toast_message).to_contain_text("restricted")
