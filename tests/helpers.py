"""Helper utilities for integration and performance tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from playwright.sync_api import expect
from reflex.testing import AppHarness

from pycodium.constants import INITIAL_PATH_ENV_VAR, PROJECT_ROOT_DIR

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

    from playwright.sync_api import Locator, Page


def wait_for_folder(page: Page, folder_name: str, *, timeout: int = 10000) -> Locator:
    """Wait for a folder to be visible in the file explorer.

    Args:
        page: Playwright page instance.
        folder_name: The name of the folder to wait for.
        timeout: Maximum time to wait in milliseconds.

    Returns:
        Locator for the folder element.
    """
    folder_locator = page.locator(f".folder-item:has-text('{folder_name}')")
    expect(folder_locator).to_be_visible(timeout=timeout)
    return folder_locator


def wait_for_file(page: Page, filename: str, *, timeout: int = 10000) -> Locator:
    """Wait for a file to be visible in the file explorer.

    Args:
        page: Playwright page instance.
        filename: The name of the file to wait for.
        timeout: Maximum time to wait in milliseconds.

    Returns:
        Locator for the file element.
    """
    file_locator = page.locator(f".file-item:has-text('{filename}')")
    expect(file_locator).to_be_visible(timeout=timeout)
    return file_locator


def open_file(page: Page, filename: str, *, timeout: int = 10000) -> Locator:
    """Open a file in the editor by clicking on it in the file explorer.

    Args:
        page: Playwright page instance.
        filename: The name of the file to open.
        timeout: Maximum time to wait for elements in milliseconds.

    Returns:
        Locator for the editor tab that was opened.
    """
    file_locator = wait_for_file(page, filename, timeout=timeout)
    file_locator.click()

    # Wait for the tab to appear
    tab_locator = page.locator(f".editor-tab:has-text('{filename}')")
    expect(tab_locator).to_be_visible(timeout=timeout)
    return tab_locator


def wait_for_editor_content(page: Page, text: str, *, timeout: int = 5000) -> Locator:
    """Wait for specific text content to appear in the Monaco editor.

    Args:
        page: Playwright page instance.
        text: The text content to wait for.
        timeout: Maximum time to wait in milliseconds.

    Returns:
        Locator for the content element.
    """
    content_locator = page.locator(".monaco-editor").get_by_text(text)
    expect(content_locator).to_be_visible(timeout=timeout)
    return content_locator


def wait_for_editor_visible(page: Page, *, timeout: int = 5000) -> Locator:
    """Wait for the Monaco editor to be visible.

    Args:
        page: Playwright page instance.
        timeout: Maximum time to wait in milliseconds.

    Returns:
        Locator for the Monaco editor element.
    """
    editor_locator = page.locator(".monaco-editor")
    expect(editor_locator).to_be_visible(timeout=timeout)
    return editor_locator


def close_active_tab(page: Page, filename: str, *, timeout: int = 5000) -> None:
    """Close an editor tab by clicking its close button.

    Args:
        page: Playwright page instance.
        filename: The name of the file in the tab to close.
        timeout: Maximum time to wait in milliseconds.
    """
    tab = page.locator(f".editor-tab:has-text('{filename}')")
    expect(tab).to_be_visible(timeout=timeout)

    # Try to find and click the close button
    close_button = tab.locator("svg, [class*='close'], button:has-text('x'), button:has-text('✕')")
    if close_button.count() > 0:
        close_button.first.click()
    else:
        # Fall back to keyboard shortcut
        page.keyboard.press("Meta+w")

    expect(tab).not_to_be_visible(timeout=timeout)


def expand_folder(page: Page, folder_name: str, *, timeout: int = 10000) -> Locator:
    """Expand a folder in the file explorer by clicking on it.

    Args:
        page: Playwright page instance.
        folder_name: The name of the folder to expand.
        timeout: Maximum time to wait in milliseconds.

    Returns:
        Locator for the folder element.
    """
    folder_locator = wait_for_folder(page, folder_name, timeout=timeout)
    folder_locator.click()
    return folder_locator


def assert_app_functional(page: Page) -> None:
    """Assert that the app is still functional by checking key UI elements.

    Args:
        page: Playwright page instance.
    """
    activity_bar = page.locator('[class*="bg-pycodium-activity-bar"]')
    expect(activity_bar).to_be_visible()


def trigger_menu_action(page: Page, action: str) -> None:
    """Trigger a menu action via the window.__PYCODIUM_MENU__ function.

    This simulates menu actions that would be triggered by Tauri's native menus.

    Args:
        page: Playwright page instance.
        action: The menu action to trigger (e.g., "open_file", "save").
    """
    page.evaluate(f"window.__PYCODIUM_MENU__({{ action: '{action}' }})")


def create_app_harness_with_path(path: Path | str) -> Generator[AppHarness, None, None]:
    """Create an AppHarness with a specific initial path.

    Args:
        path: The initial path to set for the app.

    Yields:
        Running AppHarness instance.
    """
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setenv(INITIAL_PATH_ENV_VAR, str(path))
        with AppHarness.create(root=PROJECT_ROOT_DIR) as harness:
            yield harness


def navigate_to_app(harness: AppHarness, page: Page) -> Page:
    """Navigate a Playwright page to the app's frontend URL.

    Args:
        harness: The running AppHarness instance.
        page: Playwright page fixture.

    Returns:
        Playwright page navigated to the app's frontend URL.
    """
    assert harness.frontend_url is not None
    page.goto(harness.frontend_url)
    page.wait_for_load_state("networkidle")
    return page
