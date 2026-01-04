"""Integration tests for the file watching functionality.

These tests verify that the editor content is automatically updated
when files are modified externally (outside the editor).
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pytest
from playwright.sync_api import Page, expect
from reflex.testing import AppHarness

from pycodium.constants import INITIAL_PATH_ENV_VAR, PROJECT_ROOT_DIR

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path


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
def app_with_multiple_files(test_folder_with_multiple_files: Path) -> Generator[AppHarness, None, None]:
    """Start the PyCodium Reflex app with a test folder containing multiple files."""
    original_env = os.environ.get(INITIAL_PATH_ENV_VAR)
    os.environ[INITIAL_PATH_ENV_VAR] = str(test_folder_with_multiple_files)

    try:
        with AppHarness.create(root=PROJECT_ROOT_DIR) as harness:
            yield harness
    finally:
        if original_env is not None:
            os.environ[INITIAL_PATH_ENV_VAR] = original_env
        elif INITIAL_PATH_ENV_VAR in os.environ:
            del os.environ[INITIAL_PATH_ENV_VAR]


@pytest.fixture
def multi_file_page(app_with_multiple_files: AppHarness, page: Page) -> Page:
    """Navigate to the app's frontend URL and return the page."""
    assert app_with_multiple_files.frontend_url is not None
    page.goto(app_with_multiple_files.frontend_url)
    page.wait_for_load_state("networkidle")
    return page


@pytest.fixture
def app_with_watchable_file(test_folder_with_file: Path) -> Generator[AppHarness, None, None]:
    """Start the PyCodium Reflex app with a test folder containing a watchable file."""
    original_env = os.environ.get(INITIAL_PATH_ENV_VAR)
    os.environ[INITIAL_PATH_ENV_VAR] = str(test_folder_with_file)

    try:
        with AppHarness.create(root=PROJECT_ROOT_DIR) as harness:
            yield harness
    finally:
        if original_env is not None:
            os.environ[INITIAL_PATH_ENV_VAR] = original_env
        elif INITIAL_PATH_ENV_VAR in os.environ:
            del os.environ[INITIAL_PATH_ENV_VAR]


@pytest.fixture
def file_watch_page(app_with_watchable_file: AppHarness, page: Page) -> Page:
    """Navigate to the app's frontend URL and return the page."""
    assert app_with_watchable_file.frontend_url is not None
    page.goto(app_with_watchable_file.frontend_url)
    page.wait_for_load_state("networkidle")
    return page


def test_editor_updates_when_file_modified_externally(file_watch_page: Page, test_folder_with_file: Path) -> None:
    """Test that the editor content updates when a file is modified externally.

    This test verifies the keep_active_tab_content_updated background task
    that watches for file changes and updates the editor content accordingly.
    """
    # Wait for the file explorer to show the file
    file_item = file_watch_page.locator(".file-item:has-text('watched_file.py')")
    expect(file_item).to_be_visible(timeout=10000)

    # Click on the file to open it in the editor
    file_item.click()
    file_watch_page.wait_for_timeout(1000)

    # Wait for the editor to load and verify original content is displayed
    # The Monaco editor renders content in a specific way, look for content in the editor area
    editor_area = file_watch_page.locator(".monaco-editor")
    expect(editor_area).to_be_visible(timeout=5000)

    # Verify the tab is open with the file name (use the specific editor-tab class)
    tab = file_watch_page.locator(".editor-tab:has-text('watched_file.py')")
    expect(tab).to_be_visible(timeout=5000)

    # Verify original content is in the editor (look inside monaco editor)
    original_content = file_watch_page.locator(".monaco-editor >> text=Original content")
    expect(original_content).to_be_visible(timeout=5000)

    # Modify the file externally
    watched_file = test_folder_with_file / "watched_file.py"
    watched_file.write_text("# Modified externally\nprint('updated!')")

    # Wait for the file watcher to detect the change and update the editor
    # The watchfiles library should detect changes within a reasonable time
    modified_content = file_watch_page.locator(".monaco-editor >> text=Modified externally")
    expect(modified_content).to_be_visible(timeout=10000)

    # Verify the old content is no longer visible
    old_content = file_watch_page.locator(".monaco-editor >> text=Original content")
    expect(old_content).not_to_be_visible()


def test_file_watcher_stops_when_tab_closed(file_watch_page: Page) -> None:
    """Test that file watching stops when the tab is closed.

    This verifies that the on_not_active event is properly set when closing a tab,
    which signals the file watcher to stop.
    """
    # Open the file
    file_item = file_watch_page.locator(".file-item:has-text('watched_file.py')")
    expect(file_item).to_be_visible(timeout=10000)
    file_item.click()
    file_watch_page.wait_for_timeout(1000)

    # Wait for the tab to appear (use the specific editor-tab class)
    tab = file_watch_page.locator(".editor-tab:has-text('watched_file.py')")
    expect(tab).to_be_visible(timeout=5000)

    # Close the tab by clicking the close button
    close_button = tab.locator("svg, [class*='close'], button:has-text('x'), button:has-text('✕')")
    if close_button.count() > 0:
        close_button.first.click()
    else:
        # If no close button found, use keyboard shortcut
        file_watch_page.keyboard.press("Meta+w")

    file_watch_page.wait_for_timeout(500)

    # Verify the tab is closed
    file_watch_page.wait_for_timeout(500)
    expect(tab).not_to_be_visible(timeout=5000)

    # The app should still be functional (no crashes from orphaned watchers)
    activity_bar = file_watch_page.locator('[class*="bg-pycodium-activity-bar"]')
    expect(activity_bar).to_be_visible()


def test_switching_tabs_updates_file_watcher(multi_file_page: Page, test_folder_with_multiple_files: Path) -> None:
    """Test that switching between tabs properly manages file watchers.

    When switching to a different tab, the previous tab's watcher should stop
    and a new watcher should start for the newly active tab.
    """
    second_file = test_folder_with_multiple_files / "second_file.py"

    # Open the first file
    first_file_item = multi_file_page.locator(".file-item:has-text('first_file.py')")
    expect(first_file_item).to_be_visible(timeout=10000)
    first_file_item.click()
    multi_file_page.wait_for_timeout(1000)

    # Wait for first file tab (use the specific editor-tab class)
    first_tab = multi_file_page.locator(".editor-tab:has-text('first_file.py')")
    expect(first_tab).to_be_visible(timeout=5000)

    # Open the second file
    second_file_item = multi_file_page.locator(".file-item:has-text('second_file.py')")
    expect(second_file_item).to_be_visible(timeout=5000)
    second_file_item.click()
    multi_file_page.wait_for_timeout(1000)

    # Wait for second file tab (use the specific editor-tab class)
    second_tab = multi_file_page.locator(".editor-tab:has-text('second_file.py')")
    expect(second_tab).to_be_visible(timeout=5000)

    # Verify second file content is visible (look inside monaco editor)
    second_content = multi_file_page.locator(".monaco-editor >> text=Second file content")
    expect(second_content).to_be_visible(timeout=5000)

    # Modify the second file externally
    second_file.write_text("# Second file modified!")

    # Wait for the change to be detected
    modified_content = multi_file_page.locator(".monaco-editor >> text=Second file modified!")
    expect(modified_content).to_be_visible(timeout=10000)

    # App should still be functional
    activity_bar = multi_file_page.locator('[class*="bg-pycodium-activity-bar"]')
    expect(activity_bar).to_be_visible()
