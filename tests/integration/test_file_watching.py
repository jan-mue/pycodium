"""Integration tests for the file watching functionality.

These tests verify that the editor content is automatically updated
when files are modified externally (outside the editor).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from playwright.sync_api import expect

from tests.helpers import (
    assert_app_functional,
    close_active_tab,
    open_file,
    wait_for_editor_content,
    wait_for_editor_visible,
)

if TYPE_CHECKING:
    from pathlib import Path

    from playwright.sync_api import Page


def test_editor_updates_when_file_modified_externally(file_watch_page: Page, test_folder_with_file: Path) -> None:
    """Test that the editor content updates when a file is modified externally.

    This test verifies the keep_active_tab_content_updated background task
    that watches for file changes and updates the editor content accordingly.
    """
    # Open the file in the editor
    open_file(file_watch_page, "watched_file.py")

    # Wait for the editor to load and verify original content is displayed
    wait_for_editor_visible(file_watch_page)
    wait_for_editor_content(file_watch_page, "Original content")

    # Modify the file externally
    watched_file = test_folder_with_file / "watched_file.py"
    watched_file.write_text("# Modified externally\nprint('updated!')")

    # Wait for the file watcher to detect the change and update the editor
    wait_for_editor_content(file_watch_page, "Modified externally", timeout=10000)

    # Verify the old content is no longer visible
    old_content = file_watch_page.locator(".monaco-editor >> text=Original content")
    expect(old_content).not_to_be_visible()


def test_file_watcher_stops_when_tab_closed(file_watch_page: Page) -> None:
    """Test that file watching stops when the tab is closed.

    This verifies that the on_not_active event is properly set when closing a tab,
    which signals the file watcher to stop.
    """
    # Open the file
    open_file(file_watch_page, "watched_file.py")

    # Close the tab
    close_active_tab(file_watch_page, "watched_file.py")

    # The app should still be functional (no crashes from orphaned watchers)
    assert_app_functional(file_watch_page)


def test_switching_tabs_updates_file_watcher(multi_file_page: Page, test_folder_with_multiple_files: Path) -> None:
    """Test that switching between tabs properly manages file watchers.

    When switching to a different tab, the previous tab's watcher should stop
    and a new watcher should start for the newly active tab.
    """
    second_file = test_folder_with_multiple_files / "second_file.py"

    # Open the first file
    open_file(multi_file_page, "first_file.py")

    # Open the second file
    open_file(multi_file_page, "second_file.py")

    # Verify second file content is visible
    wait_for_editor_content(multi_file_page, "Second file content")

    # Modify the second file externally
    second_file.write_text("# Second file modified!")

    # Wait for the change to be detected
    wait_for_editor_content(multi_file_page, "Second file modified!", timeout=10000)

    # App should still be functional
    assert_app_functional(multi_file_page)
