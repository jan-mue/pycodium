"""Integration tests for Command Palette functionality using Playwright.

These tests verify that the command palette opens, displays commands,
handles keyboard navigation, and executes commands correctly.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from playwright.sync_api import expect

from tests.helpers import navigate_to_app_with_path

if TYPE_CHECKING:
    from pathlib import Path

    from playwright.sync_api import Page
    from reflex.testing import AppHarness


@pytest.fixture(scope="module")
def command_palette_test_folder(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Create a test folder with Python files for testing.

    Using module scope to share the folder across all tests.
    """
    test_dir = tmp_path_factory.mktemp("cmd_palette_test")

    main_py = test_dir / "main.py"
    main_py.write_text('"""Test file for command palette."""\n\nprint("Hello, World!")\n')

    return test_dir


@pytest.fixture
def command_palette_page(
    reflex_web_app: AppHarness, page: Page, command_palette_test_folder: Path, monkeypatch: pytest.MonkeyPatch
) -> Page:
    """Navigate to the app for command palette testing."""
    page = navigate_to_app_with_path(reflex_web_app, page, command_palette_test_folder, monkeypatch)
    page.wait_for_timeout(3000)
    return page


class TestCommandPaletteOpen:
    """Tests for opening and closing the command palette."""

    def test_command_palette_opens_with_keyboard_shortcut(self, command_palette_page: Page) -> None:
        """Test that Cmd+Shift+P opens the command palette."""
        command_palette = command_palette_page.locator("#command-palette-container")
        expect(command_palette).not_to_be_visible(timeout=2000)

        command_palette_page.keyboard.press("Meta+Shift+p")
        command_palette_page.wait_for_timeout(500)

        expect(command_palette).to_be_visible(timeout=5000)

        input_field = command_palette_page.locator("#command-palette-input")
        expect(input_field).to_be_visible(timeout=2000)

    def test_command_palette_closes_with_escape(self, command_palette_page: Page) -> None:
        """Test that Escape closes the command palette."""
        command_palette_page.keyboard.press("Meta+Shift+p")
        command_palette_page.wait_for_timeout(500)

        command_palette = command_palette_page.locator("#command-palette-container")
        expect(command_palette).to_be_visible(timeout=5000)

        command_palette_page.keyboard.press("Escape")
        command_palette_page.wait_for_timeout(300)

        expect(command_palette).not_to_be_visible(timeout=2000)

    def test_command_palette_closes_on_overlay_click(self, command_palette_page: Page) -> None:
        """Test that clicking the overlay closes the command palette."""
        command_palette_page.keyboard.press("Meta+Shift+p")
        command_palette_page.wait_for_timeout(500)

        command_palette = command_palette_page.locator("#command-palette-container")
        expect(command_palette).to_be_visible(timeout=5000)

        overlay = command_palette_page.locator("#command-palette-overlay")
        overlay.click(position={"x": 50, "y": 650})
        command_palette_page.wait_for_timeout(300)

        expect(command_palette).not_to_be_visible(timeout=2000)


class TestCommandPaletteSearch:
    """Tests for command palette search functionality."""

    def test_commands_are_displayed(self, command_palette_page: Page) -> None:
        """Test that commands are displayed in the command palette."""
        command_palette_page.keyboard.press("Meta+Shift+p")
        command_palette_page.wait_for_timeout(500)

        command_list = command_palette_page.locator("#command-palette-list")
        expect(command_list).to_be_visible(timeout=5000)

        save_command = command_palette_page.locator("#command-save")
        expect(save_command).to_be_visible(timeout=2000)

    def test_search_filters_commands(self, command_palette_page: Page) -> None:
        """Test that typing filters the command list."""
        command_palette_page.keyboard.press("Meta+Shift+p")
        command_palette_page.wait_for_timeout(500)

        input_field = command_palette_page.locator("#command-palette-input")
        expect(input_field).to_be_visible(timeout=2000)

        input_field.fill("Python")
        command_palette_page.wait_for_timeout(300)

        python_command = command_palette_page.locator("#command-select-python")
        expect(python_command).to_be_visible(timeout=2000)

        save_command = command_palette_page.locator("#command-save")
        expect(save_command).not_to_be_visible(timeout=1000)

    def test_no_results_message_shown(self, command_palette_page: Page) -> None:
        """Test that 'No commands found' is shown when search has no results."""
        command_palette_page.keyboard.press("Meta+Shift+p")
        command_palette_page.wait_for_timeout(500)

        input_field = command_palette_page.locator("#command-palette-input")
        input_field.fill("xyznonexistent")
        command_palette_page.wait_for_timeout(300)

        no_results = command_palette_page.get_by_text("No commands found")
        expect(no_results).to_be_visible(timeout=2000)


class TestCommandPaletteNavigation:
    """Tests for keyboard navigation in the command palette."""

    def test_arrow_keys_navigate_commands(self, command_palette_page: Page) -> None:
        """Test that arrow keys navigate through commands."""
        command_palette_page.keyboard.press("Meta+Shift+p")
        command_palette_page.wait_for_timeout(500)

        first_command = command_palette_page.locator(".command-palette-item.bg-pycodium-highlight").first
        expect(first_command).to_be_visible(timeout=2000)

        command_palette_page.keyboard.press("ArrowDown")
        command_palette_page.wait_for_timeout(200)

        highlighted = command_palette_page.locator(".command-palette-item.bg-pycodium-highlight")
        expect(highlighted).to_be_visible(timeout=2000)


class TestCommandPaletteExecution:
    """Tests for command execution from the command palette."""

    def test_toggle_sidebar_command(self, command_palette_page: Page) -> None:
        """Test that the Toggle Sidebar command works."""
        command_palette_page.keyboard.press("Meta+Shift+p")
        command_palette_page.wait_for_timeout(500)

        input_field = command_palette_page.locator("#command-palette-input")
        input_field.fill("Toggle Sidebar")
        command_palette_page.wait_for_timeout(300)

        toggle_command = command_palette_page.locator("#command-toggle-sidebar")
        expect(toggle_command).to_be_visible(timeout=2000)
        toggle_command.click()
        command_palette_page.wait_for_timeout(500)

        command_palette = command_palette_page.locator("#command-palette-container")
        expect(command_palette).not_to_be_visible(timeout=2000)

    def test_enter_key_executes_command(self, command_palette_page: Page) -> None:
        """Test that pressing Enter executes the selected command."""
        command_palette_page.keyboard.press("Meta+Shift+p")
        command_palette_page.wait_for_timeout(500)

        input_field = command_palette_page.locator("#command-palette-input")
        input_field.fill("Toggle Sidebar")
        command_palette_page.wait_for_timeout(300)

        command_palette_page.keyboard.press("Enter")
        command_palette_page.wait_for_timeout(500)

        command_palette = command_palette_page.locator("#command-palette-container")
        expect(command_palette).not_to_be_visible(timeout=2000)


class TestPythonInterpreterSelection:
    """Tests for Python interpreter selection mode."""

    def test_select_interpreter_command_shows_interpreters(self, command_palette_page: Page) -> None:
        """Test that selecting Python interpreter shows interpreter list."""
        command_palette_page.keyboard.press("Meta+Shift+p")
        command_palette_page.wait_for_timeout(500)

        input_field = command_palette_page.locator("#command-palette-input")
        input_field.fill("Python: Select")
        command_palette_page.wait_for_timeout(500)

        python_command = command_palette_page.locator("#command-select-python")
        expect(python_command).to_be_visible(timeout=5000)
        python_command.click()

        interpreter_list = command_palette_page.locator("#interpreter-list")
        expect(interpreter_list).to_be_visible(timeout=15000)

        input_field = command_palette_page.locator("#command-palette-input")
        expect(input_field).to_have_attribute("placeholder", "Select Python Interpreter", timeout=5000)

    def test_interpreter_list_shows_python_versions(self, command_palette_page: Page) -> None:
        """Test that interpreter list shows Python version information."""
        command_palette_page.keyboard.press("Meta+Shift+p")
        command_palette_page.wait_for_timeout(500)

        input_field = command_palette_page.locator("#command-palette-input")
        expect(input_field).to_be_visible(timeout=5000)

        input_field.clear()
        input_field.fill("Python: Select")
        command_palette_page.wait_for_timeout(500)

        python_command = command_palette_page.locator("#command-select-python")
        expect(python_command).to_be_visible(timeout=5000)
        python_command.click()
        command_palette_page.wait_for_timeout(1500)

        interpreter_list = command_palette_page.locator("#interpreter-list")
        expect(interpreter_list).to_be_visible(timeout=10000)

        python_version = command_palette_page.get_by_text("Python 3", exact=False)
        expect(python_version.first).to_be_visible(timeout=5000)

    def test_select_interpreter_with_enter_key(self, command_palette_page: Page) -> None:
        """Regression test: selecting interpreter with Enter key should work without errors.

        This test verifies the fix for the async generator error:
        "object async_generator can't be used in 'await' expression"
        """
        command_palette_page.keyboard.press("Meta+Shift+p")
        command_palette_page.wait_for_timeout(500)

        input_field = command_palette_page.locator("#command-palette-input")
        input_field.fill("Python: Select")
        command_palette_page.wait_for_timeout(500)

        python_command = command_palette_page.locator("#command-select-python")
        expect(python_command).to_be_visible(timeout=5000)
        python_command.click()

        interpreter_list = command_palette_page.locator("#interpreter-list")
        expect(interpreter_list).to_be_visible(timeout=15000)

        command_palette_page.keyboard.press("Enter")
        command_palette_page.wait_for_timeout(2000)

        command_palette_overlay = command_palette_page.locator("#command-palette-overlay")
        expect(command_palette_overlay).not_to_be_visible(timeout=5000)

    def test_select_interpreter_by_clicking(self, command_palette_page: Page) -> None:
        """Test that clicking on an interpreter in the list selects it."""
        command_palette_page.keyboard.press("Meta+Shift+p")
        command_palette_page.wait_for_timeout(500)

        input_field = command_palette_page.locator("#command-palette-input")
        input_field.fill("Python: Select")
        command_palette_page.wait_for_timeout(500)

        python_command = command_palette_page.locator("#command-select-python")
        expect(python_command).to_be_visible(timeout=5000)
        python_command.click()

        interpreter_list = command_palette_page.locator("#interpreter-list")
        expect(interpreter_list).to_be_visible(timeout=15000)

        first_interpreter = interpreter_list.locator(".command-palette-item").first
        expect(first_interpreter).to_be_visible(timeout=5000)
        first_interpreter.click()
        command_palette_page.wait_for_timeout(2000)

        command_palette_overlay = command_palette_page.locator("#command-palette-overlay")
        expect(command_palette_overlay).not_to_be_visible(timeout=5000)
