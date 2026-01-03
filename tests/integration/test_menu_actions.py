"""Integration tests for menu actions triggered via JavaScript menu handler."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from playwright.sync_api import Page, expect

if TYPE_CHECKING:
    from reflex.testing import AppHarness


@pytest.fixture
def app_page_with_tauri_mock(reflex_web_app: AppHarness, page: Page) -> Page:
    """Navigate to the app with Tauri mocked for menu handler setup.

    This fixture injects a mock __TAURI__ object before the page loads,
    allowing the menu event handler to be initialized.

    Args:
        reflex_web_app: The running AppHarness instance.
        page: Playwright page fixture.

    Returns:
        Playwright page with Tauri mocked.
    """
    assert reflex_web_app.frontend_url is not None

    # Inject __TAURI__ mock before any scripts run
    page.add_init_script("""
        window.__TAURI__ = {
            core: { invoke: () => Promise.resolve() }
        };
    """)

    page.goto(reflex_web_app.frontend_url)
    page.wait_for_load_state("networkidle")
    return page


def _trigger_menu_action(page: Page, action: str) -> None:
    """Trigger a menu action via the window.__PYCODIUM_MENU__ function.

    Args:
        page: Playwright page.
        action: The menu action to trigger (e.g., "open_file", "save").
    """
    page.evaluate(f"window.__PYCODIUM_MENU__({{ action: '{action}' }})")


def test_pycodium_menu_function_setup(app_page_with_tauri_mock: Page) -> None:
    """Test that the menu handler is set up when Tauri is present."""
    result = app_page_with_tauri_mock.evaluate("typeof window.__PYCODIUM_MENU__")
    assert result == "function"


def test_menu_save_action_no_crash(app_page_with_tauri_mock: Page) -> None:
    """Test that save menu action doesn't crash with no open files."""
    _trigger_menu_action(app_page_with_tauri_mock, "save")
    app_page_with_tauri_mock.wait_for_timeout(300)

    # App should still be functional
    activity_bar = app_page_with_tauri_mock.locator('[class*="bg-pycodium-activity-bar"]')
    expect(activity_bar).to_be_visible()


def test_menu_save_as_action_no_crash(app_page_with_tauri_mock: Page) -> None:
    """Test that save_as menu action doesn't crash with no open files."""
    _trigger_menu_action(app_page_with_tauri_mock, "save_as")
    app_page_with_tauri_mock.wait_for_timeout(300)

    activity_bar = app_page_with_tauri_mock.locator('[class*="bg-pycodium-activity-bar"]')
    expect(activity_bar).to_be_visible()


def test_menu_close_tab_action_no_crash(app_page_with_tauri_mock: Page) -> None:
    """Test that close_tab menu action doesn't crash with no open tabs."""
    _trigger_menu_action(app_page_with_tauri_mock, "close_tab")
    app_page_with_tauri_mock.wait_for_timeout(300)

    activity_bar = app_page_with_tauri_mock.locator('[class*="bg-pycodium-activity-bar"]')
    expect(activity_bar).to_be_visible()


def test_menu_unknown_action_handled_gracefully(app_page_with_tauri_mock: Page) -> None:
    """Test that unknown menu action is handled without crashing."""
    # This should not throw an error
    result = app_page_with_tauri_mock.evaluate("""
        (async () => {
            try {
                await window.__PYCODIUM_MENU__({ action: 'unknown_action' });
                return 'success';
            } catch (e) {
                return 'error: ' + e.message;
            }
        })()
    """)
    assert result == "success"

    # App should still be functional
    activity_bar = app_page_with_tauri_mock.locator('[class*="bg-pycodium-activity-bar"]')
    expect(activity_bar).to_be_visible()
