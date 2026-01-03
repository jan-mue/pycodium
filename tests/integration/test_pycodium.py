"""Integration tests for PyCodium using Playwright."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx
from playwright.sync_api import ConsoleMessage, Page, expect

if TYPE_CHECKING:
    from reflex.testing import AppHarness


def test_frontend_reachable(reflex_web_app: AppHarness) -> None:
    """Test that the frontend is reachable via HTTP."""
    assert reflex_web_app.frontend_url is not None
    response = httpx.get(reflex_web_app.frontend_url, timeout=60)
    assert response.status_code == 200


def test_app_loads_with_dark_theme(app_page: Page) -> None:
    """Test that the app loads with dark theme."""
    root_theme = app_page.locator('div[data-is-root-theme="true"]')
    expect(root_theme).to_be_visible()


def test_activity_bar_visible(app_page: Page) -> None:
    """Test that the activity bar is visible with icons."""
    activity_bar = app_page.locator('[class*="bg-pycodium-activity-bar"]')
    expect(activity_bar).to_be_visible()


def test_activity_bar_icons_have_tooltips(app_page: Page) -> None:
    """Test that activity bar icons have proper tooltips."""
    explorer_icon = app_page.locator('[title="Explorer"]')
    expect(explorer_icon).to_be_visible()

    search_icon = app_page.locator('[title="Search"]')
    expect(search_icon).to_be_visible()

    settings_icon = app_page.locator('[title="Settings"]')
    expect(settings_icon).to_be_visible()


def test_status_bar_visible(app_page: Page) -> None:
    """Test that the status bar is visible."""
    status_bar = app_page.locator('[class*="bg-pycodium-statusbar-bg"]')
    expect(status_bar).to_be_visible()


def test_sidebar_toggle(app_page: Page) -> None:
    """Test that clicking the explorer icon toggles the sidebar."""
    explorer_icon = app_page.locator('[title="Explorer"].w-12.h-12')
    sidebar = app_page.locator("div.bg-pycodium-sidebar-bg.overflow-auto")
    expect(sidebar).to_be_visible()

    explorer_icon.click()
    app_page.wait_for_timeout(500)
    expect(sidebar).not_to_be_visible()

    explorer_icon.click()
    app_page.wait_for_timeout(500)
    expect(sidebar).to_be_visible()


def test_switch_sidebar_tabs(app_page: Page) -> None:
    """Test switching between sidebar tabs."""
    explorer_icon = app_page.locator('[title="Explorer"]')
    search_icon = app_page.locator('[title="Search"]')

    search_icon.click()
    app_page.wait_for_timeout(500)

    search_content = app_page.get_by_text("Search functionality would be here")
    expect(search_content).to_be_visible()

    explorer_icon.click()
    app_page.wait_for_timeout(500)
    expect(search_content).not_to_be_visible()


def test_source_control_tab(app_page: Page) -> None:
    """Test the source control tab content."""
    source_control_icon = app_page.locator('[title="Source Control"]')
    source_control_icon.click()
    app_page.wait_for_timeout(500)

    source_control_content = app_page.get_by_text("Source control functionality would be here")
    expect(source_control_content).to_be_visible()


def test_debug_tab(app_page: Page) -> None:
    """Test the debug tab content."""
    debug_icon = app_page.locator('[title="Debug"]')
    debug_icon.click()
    app_page.wait_for_timeout(500)

    debug_content = app_page.get_by_text("Debugging tools would be here")
    expect(debug_content).to_be_visible()


def test_extensions_tab(app_page: Page) -> None:
    """Test the extensions tab content."""
    extensions_icon = app_page.locator('[title="Extensions"]')
    extensions_icon.click()
    app_page.wait_for_timeout(500)

    extensions_content = app_page.get_by_text("Extensions marketplace would be here")
    expect(extensions_content).to_be_visible()


def test_page_title(app_page: Page) -> None:
    """Test that the page has the correct title."""
    expect(app_page).to_have_title("PyCodium")


def test_no_console_errors(app_page: Page) -> None:
    """Test that there are no critical console errors on page load."""
    errors: list[str] = []

    def handle_console(msg: ConsoleMessage) -> None:
        if msg.type == "error":
            text = msg.text
            # Filter out expected errors (Tauri not available, React Fragment warning)
            is_expected_error = "__TAURI__" in text or "Failed to load resource" in text or "React.Fragment" in text
            if not is_expected_error:
                errors.append(text)

    app_page.on("console", handle_console)
    app_page.reload()
    app_page.wait_for_load_state("networkidle")
    app_page.wait_for_timeout(1000)

    assert len(errors) == 0, f"Console errors found: {errors}"
