"""Integration tests for the PyCodium initial path functionality."""

from __future__ import annotations

import stat
from typing import TYPE_CHECKING

import pytest
from playwright.sync_api import expect

from tests.conftest import create_app_harness_with_path, navigate_to_app
from tests.helpers import expand_folder, wait_for_file, wait_for_folder

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

    from playwright.sync_api import Page
    from reflex.testing import AppHarness


def test_cli_opens_folder_from_path_argument(cli_app_page: Page, test_folder: Path) -> None:
    """Test that the CLI correctly passes the initial path to the Reflex backend."""
    folder_name = test_folder.name
    wait_for_folder(cli_app_page, folder_name)


def test_initial_path_folder_is_expanded_by_default(cli_app_page: Page, test_folder: Path) -> None:
    """Test that the opened folder is expanded by default in the file tree."""
    folder_name = test_folder.name
    wait_for_folder(cli_app_page, folder_name)
    wait_for_file(cli_app_page, "file1.py")


def test_initial_path_shows_all_files_in_folder(cli_app_page: Page) -> None:
    """Test that all files in the opened folder are visible in the file explorer."""
    wait_for_file(cli_app_page, "file1.py")
    wait_for_file(cli_app_page, "file2.txt")


def test_initial_path_shows_subdirectories(cli_app_page: Page) -> None:
    """Test that subdirectories in the opened folder are visible."""
    wait_for_folder(cli_app_page, "subdir")


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
    """Start the app with a folder containing an inaccessible subdirectory."""
    yield from create_app_harness_with_path(test_folder_with_inaccessible_dir)


@pytest.fixture
def inaccessible_dir_page(app_with_inaccessible_dir: AppHarness, page: Page) -> Page:
    """Navigate to the app's frontend URL and return the page."""
    return navigate_to_app(app_with_inaccessible_dir, page)


def test_expanding_inaccessible_directory_shows_toast(inaccessible_dir_page: Page) -> None:
    """Test that expanding an inaccessible directory shows an error toast."""
    expand_folder(inaccessible_dir_page, "restricted")
    inaccessible_dir_page.wait_for_timeout(500)

    # Verify that a toast error is shown with the folder name
    toast = inaccessible_dir_page.locator("[data-sonner-toast][data-type='error']")
    expect(toast).to_be_visible(timeout=5000)
    expect(toast).to_contain_text("restricted")
