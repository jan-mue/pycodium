"""Integration tests for the status bar component."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from playwright.sync_api import expect

from tests.helpers import (
    create_app_harness_with_path,
    navigate_to_app,
)

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

    from playwright.sync_api import Page
    from reflex.testing import AppHarness


@pytest.fixture(scope="module")
def status_bar_test_folder(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Create a test folder with Python files for testing.

    Using module scope to share the folder across all tests.
    """
    test_dir = tmp_path_factory.mktemp("status_bar_test")

    # Create a simple Python file
    main_py = test_dir / "main.py"
    main_py.write_text('"""Test file for status bar."""\n\nprint("Hello")\n')

    # Create a JSON file
    config_json = test_dir / "config.json"
    config_json.write_text('{"name": "test"}\n')

    return test_dir


@pytest.fixture(scope="module")
def app_with_test_folder(status_bar_test_folder: Path) -> Generator[AppHarness, None, None]:
    """Start the app with a test folder.

    Using module scope to share the app harness across all tests in this module.
    """
    yield from create_app_harness_with_path(status_bar_test_folder)


@pytest.fixture
def status_bar_page(app_with_test_folder: AppHarness, page: Page) -> Page:
    """Navigate to the app for status bar testing."""
    page = navigate_to_app(app_with_test_folder, page, timeout=90000)
    page.wait_for_timeout(3000)
    return page


class TestStatusBar:
    """Test suite for the status bar component."""

    def test_status_bar_is_visible(self, status_bar_page: Page) -> None:
        """Test that the status bar is visible at the bottom of the page."""
        status_bar = status_bar_page.locator("#status-bar")
        expect(status_bar).to_be_visible(timeout=5000)

    def test_interpreter_selector_is_visible(self, status_bar_page: Page) -> None:
        """Test that the interpreter selector is visible in the status bar."""
        interpreter_selector = status_bar_page.locator("#status-bar-interpreter")
        expect(interpreter_selector).to_be_visible(timeout=5000)

    def test_click_interpreter_opens_palette(self, status_bar_page: Page) -> None:
        """Test that clicking the interpreter section opens the interpreter palette."""
        interpreter_selector = status_bar_page.locator("#status-bar-interpreter")
        expect(interpreter_selector).to_be_visible(timeout=5000)

        # Click the interpreter selector
        interpreter_selector.click()
        status_bar_page.wait_for_timeout(1000)

        # Command palette should open in interpreter mode
        interpreter_list = status_bar_page.locator("#interpreter-list")
        expect(interpreter_list).to_be_visible(timeout=15000)

        # Input should have the interpreter selection placeholder
        input_field = status_bar_page.locator("#command-palette-input")
        expect(input_field).to_have_attribute("placeholder", "Select Python Interpreter", timeout=5000)


class TestStatusBarLanguage:
    """Test suite for the language display in the status bar."""

    def test_python_file_shows_python_language(self, status_bar_page: Page) -> None:
        """Test that opening a Python file shows 'Python' in the status bar."""
        # Open a Python file from the file explorer
        file_item = status_bar_page.locator(".file-item:has-text('main.py')")
        expect(file_item).to_be_visible(timeout=10000)
        file_item.click()
        status_bar_page.wait_for_timeout(1000)

        # Check language in status bar
        language_display = status_bar_page.locator("#status-bar-language")
        expect(language_display).to_be_visible(timeout=5000)
        expect(language_display).to_contain_text("Python", timeout=5000)


class TestStatusBarInterpreterSelection:
    """Test suite for interpreter selection flow from status bar."""

    def test_select_interpreter_from_status_bar(self, status_bar_page: Page) -> None:
        """Test selecting an interpreter from the status bar opens the palette."""
        # Click the interpreter selector in status bar
        interpreter_selector = status_bar_page.locator("#status-bar-interpreter")
        expect(interpreter_selector).to_be_visible(timeout=5000)
        interpreter_selector.click()

        # Wait for interpreter list
        interpreter_list = status_bar_page.locator("#interpreter-list")
        expect(interpreter_list).to_be_visible(timeout=15000)

        # Select an interpreter
        first_interpreter = interpreter_list.locator(".command-palette-item").first
        expect(first_interpreter).to_be_visible(timeout=5000)
        first_interpreter.click()
        status_bar_page.wait_for_timeout(2000)

        # Palette should close
        command_palette_overlay = status_bar_page.locator("#command-palette-overlay")
        expect(command_palette_overlay).not_to_be_visible(timeout=5000)

        # Status bar should now show the selected interpreter
        interpreter_selector = status_bar_page.locator("#status-bar-interpreter")
        expect(interpreter_selector).to_contain_text("Python", timeout=5000)
