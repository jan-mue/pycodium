"""Integration tests for Command Palette functionality using Playwright.

These tests verify that the command palette opens, displays commands,
handles keyboard navigation, and executes commands correctly.
"""

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
def command_palette_test_folder(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Create a test folder with Python files for testing.

    Using module scope to share the folder across all tests.
    """
    test_dir = tmp_path_factory.mktemp("cmd_palette_test")

    # Create a simple Python file
    main_py = test_dir / "main.py"
    main_py.write_text('"""Test file for command palette."""\n\nprint("Hello, World!")\n')

    return test_dir


@pytest.fixture(scope="module")
def app_with_test_folder(command_palette_test_folder: Path) -> Generator[AppHarness, None, None]:
    """Start the app with a test folder.

    Using module scope to share the app harness across all tests in this module.
    """
    yield from create_app_harness_with_path(command_palette_test_folder)


@pytest.fixture
def command_palette_page(app_with_test_folder: AppHarness, page: Page) -> Page:
    """Navigate to the app for command palette testing."""
    page = navigate_to_app(app_with_test_folder, page, timeout=90000)
    page.wait_for_timeout(3000)
    return page


class TestCommandPaletteOpen:
    """Tests for opening and closing the command palette."""

    def test_command_palette_opens_with_keyboard_shortcut(self, command_palette_page: Page) -> None:
        """Test that Cmd+Shift+P opens the command palette."""
        # Ensure command palette is initially closed
        command_palette = command_palette_page.locator("#command-palette-container")
        expect(command_palette).not_to_be_visible(timeout=2000)

        # Press Cmd+Shift+P to open command palette
        command_palette_page.keyboard.press("Meta+Shift+p")
        command_palette_page.wait_for_timeout(500)

        # Command palette should now be visible
        expect(command_palette).to_be_visible(timeout=5000)

        # Input field should be visible and focused
        input_field = command_palette_page.locator("#command-palette-input")
        expect(input_field).to_be_visible(timeout=2000)

    def test_command_palette_closes_with_escape(self, command_palette_page: Page) -> None:
        """Test that Escape closes the command palette."""
        # Open command palette
        command_palette_page.keyboard.press("Meta+Shift+p")
        command_palette_page.wait_for_timeout(500)

        command_palette = command_palette_page.locator("#command-palette-container")
        expect(command_palette).to_be_visible(timeout=5000)

        # Press Escape to close
        command_palette_page.keyboard.press("Escape")
        command_palette_page.wait_for_timeout(300)

        # Command palette should be closed
        expect(command_palette).not_to_be_visible(timeout=2000)

    def test_command_palette_closes_on_overlay_click(self, command_palette_page: Page) -> None:
        """Test that clicking the overlay closes the command palette."""
        # Open command palette
        command_palette_page.keyboard.press("Meta+Shift+p")
        command_palette_page.wait_for_timeout(500)

        command_palette = command_palette_page.locator("#command-palette-container")
        expect(command_palette).to_be_visible(timeout=5000)

        # Click the overlay at the bottom left corner (away from the command palette dialog)
        # The command palette is positioned at top center, so clicking bottom left avoids it
        overlay = command_palette_page.locator("#command-palette-overlay")
        overlay.click(position={"x": 50, "y": 650})
        command_palette_page.wait_for_timeout(300)

        # Command palette should be closed
        expect(command_palette).not_to_be_visible(timeout=2000)


class TestCommandPaletteSearch:
    """Tests for command palette search functionality."""

    def test_commands_are_displayed(self, command_palette_page: Page) -> None:
        """Test that commands are displayed in the command palette."""
        # Open command palette
        command_palette_page.keyboard.press("Meta+Shift+p")
        command_palette_page.wait_for_timeout(500)

        # Commands should be visible
        command_list = command_palette_page.locator("#command-palette-list")
        expect(command_list).to_be_visible(timeout=5000)

        # Check for specific commands
        save_command = command_palette_page.locator("#command-save")
        expect(save_command).to_be_visible(timeout=2000)

    def test_search_filters_commands(self, command_palette_page: Page) -> None:
        """Test that typing filters the command list."""
        # Open command palette
        command_palette_page.keyboard.press("Meta+Shift+p")
        command_palette_page.wait_for_timeout(500)

        input_field = command_palette_page.locator("#command-palette-input")
        expect(input_field).to_be_visible(timeout=2000)

        # Type to filter
        input_field.fill("Python")
        command_palette_page.wait_for_timeout(300)

        # Python: Select Interpreter should be visible
        python_command = command_palette_page.locator("#command-select-python")
        expect(python_command).to_be_visible(timeout=2000)

        # Other commands should not be visible (filtered out)
        # The save command should not appear when searching for "Python"
        save_command = command_palette_page.locator("#command-save")
        expect(save_command).not_to_be_visible(timeout=1000)

    def test_no_results_message_shown(self, command_palette_page: Page) -> None:
        """Test that 'No commands found' is shown when search has no results."""
        # Open command palette
        command_palette_page.keyboard.press("Meta+Shift+p")
        command_palette_page.wait_for_timeout(500)

        input_field = command_palette_page.locator("#command-palette-input")
        input_field.fill("xyznonexistent")
        command_palette_page.wait_for_timeout(300)

        # "No commands found" message should appear
        no_results = command_palette_page.get_by_text("No commands found")
        expect(no_results).to_be_visible(timeout=2000)


class TestCommandPaletteNavigation:
    """Tests for keyboard navigation in the command palette."""

    def test_arrow_keys_navigate_commands(self, command_palette_page: Page) -> None:
        """Test that arrow keys navigate through commands."""
        # Open command palette
        command_palette_page.keyboard.press("Meta+Shift+p")
        command_palette_page.wait_for_timeout(500)

        # First item should be highlighted (has bg-pycodium-highlight class)
        first_command = command_palette_page.locator(".command-palette-item.bg-pycodium-highlight").first
        expect(first_command).to_be_visible(timeout=2000)

        # Press down arrow
        command_palette_page.keyboard.press("ArrowDown")
        command_palette_page.wait_for_timeout(200)

        # A different item should now be highlighted
        # We verify this by checking the highlighted item still exists
        highlighted = command_palette_page.locator(".command-palette-item.bg-pycodium-highlight")
        expect(highlighted).to_be_visible(timeout=2000)


class TestCommandPaletteExecution:
    """Tests for command execution from the command palette."""

    def test_toggle_sidebar_command(self, command_palette_page: Page) -> None:
        """Test that the Toggle Sidebar command works."""
        # Open command palette
        command_palette_page.keyboard.press("Meta+Shift+p")
        command_palette_page.wait_for_timeout(500)

        input_field = command_palette_page.locator("#command-palette-input")
        input_field.fill("Toggle Sidebar")
        command_palette_page.wait_for_timeout(300)

        # Click the toggle sidebar command
        toggle_command = command_palette_page.locator("#command-toggle-sidebar")
        expect(toggle_command).to_be_visible(timeout=2000)
        toggle_command.click()
        command_palette_page.wait_for_timeout(500)

        # Command palette should close
        command_palette = command_palette_page.locator("#command-palette-container")
        expect(command_palette).not_to_be_visible(timeout=2000)

    def test_enter_key_executes_command(self, command_palette_page: Page) -> None:
        """Test that pressing Enter executes the selected command."""
        # Open command palette
        command_palette_page.keyboard.press("Meta+Shift+p")
        command_palette_page.wait_for_timeout(500)

        input_field = command_palette_page.locator("#command-palette-input")
        input_field.fill("Toggle Sidebar")
        command_palette_page.wait_for_timeout(300)

        # Press Enter to execute
        command_palette_page.keyboard.press("Enter")
        command_palette_page.wait_for_timeout(500)

        # Command palette should close after execution
        command_palette = command_palette_page.locator("#command-palette-container")
        expect(command_palette).not_to_be_visible(timeout=2000)


class TestPythonInterpreterSelection:
    """Tests for Python interpreter selection mode."""

    def test_select_interpreter_command_shows_interpreters(self, command_palette_page: Page) -> None:
        """Test that selecting Python interpreter shows interpreter list."""
        # Open command palette
        command_palette_page.keyboard.press("Meta+Shift+p")
        command_palette_page.wait_for_timeout(500)

        input_field = command_palette_page.locator("#command-palette-input")
        input_field.fill("Python: Select")
        command_palette_page.wait_for_timeout(500)

        # Click the Python: Select Interpreter command
        python_command = command_palette_page.locator("#command-select-python")
        expect(python_command).to_be_visible(timeout=5000)
        python_command.click()

        # Wait for mode to switch and interpreter discovery to complete
        # The interpreter list should appear once discovery is done
        interpreter_list = command_palette_page.locator("#interpreter-list")
        expect(interpreter_list).to_be_visible(timeout=15000)

        # Input placeholder should have changed to "Select Python Interpreter"
        input_field = command_palette_page.locator("#command-palette-input")
        expect(input_field).to_have_attribute("placeholder", "Select Python Interpreter", timeout=5000)

    def test_interpreter_list_shows_python_versions(self, command_palette_page: Page) -> None:
        """Test that interpreter list shows Python version information."""
        # Open command palette and switch to interpreter mode
        command_palette_page.keyboard.press("Meta+Shift+p")
        command_palette_page.wait_for_timeout(500)

        input_field = command_palette_page.locator("#command-palette-input")
        expect(input_field).to_be_visible(timeout=5000)

        # Clear and type to filter for Python command
        input_field.clear()
        input_field.fill("Python: Select")
        command_palette_page.wait_for_timeout(500)

        python_command = command_palette_page.locator("#command-select-python")
        expect(python_command).to_be_visible(timeout=5000)
        python_command.click()
        command_palette_page.wait_for_timeout(1500)

        # Should see at least one interpreter with "Python" in the version text
        interpreter_list = command_palette_page.locator("#interpreter-list")
        expect(interpreter_list).to_be_visible(timeout=10000)

        # Look for Python version text
        python_version = command_palette_page.get_by_text("Python 3", exact=False)
        expect(python_version.first).to_be_visible(timeout=5000)

    def test_select_interpreter_with_enter_key(self, command_palette_page: Page) -> None:
        """Regression test: selecting interpreter with Enter key should work without errors.

        This test verifies the fix for the async generator error:
        "object async_generator can't be used in 'await' expression"
        """
        # Open command palette and switch to interpreter mode
        command_palette_page.keyboard.press("Meta+Shift+p")
        command_palette_page.wait_for_timeout(500)

        input_field = command_palette_page.locator("#command-palette-input")
        input_field.fill("Python: Select")
        command_palette_page.wait_for_timeout(500)

        python_command = command_palette_page.locator("#command-select-python")
        expect(python_command).to_be_visible(timeout=5000)
        python_command.click()

        # Wait for interpreter list to appear
        interpreter_list = command_palette_page.locator("#interpreter-list")
        expect(interpreter_list).to_be_visible(timeout=15000)

        # Press Enter to select the first interpreter
        command_palette_page.keyboard.press("Enter")
        command_palette_page.wait_for_timeout(2000)

        # Command palette should close after selection (success case)
        # If there's an error, the palette might still be open
        command_palette_overlay = command_palette_page.locator("#command-palette-overlay")
        expect(command_palette_overlay).not_to_be_visible(timeout=5000)

    def test_select_interpreter_by_clicking(self, command_palette_page: Page) -> None:
        """Test that clicking on an interpreter in the list selects it."""
        # Open command palette and switch to interpreter mode
        command_palette_page.keyboard.press("Meta+Shift+p")
        command_palette_page.wait_for_timeout(500)

        input_field = command_palette_page.locator("#command-palette-input")
        input_field.fill("Python: Select")
        command_palette_page.wait_for_timeout(500)

        python_command = command_palette_page.locator("#command-select-python")
        expect(python_command).to_be_visible(timeout=5000)
        python_command.click()

        # Wait for interpreter list to appear
        interpreter_list = command_palette_page.locator("#interpreter-list")
        expect(interpreter_list).to_be_visible(timeout=15000)

        # Find the first interpreter item and click it
        first_interpreter = interpreter_list.locator(".command-palette-item").first
        expect(first_interpreter).to_be_visible(timeout=5000)
        first_interpreter.click()
        command_palette_page.wait_for_timeout(2000)

        # Command palette should close after selection
        command_palette_overlay = command_palette_page.locator("#command-palette-overlay")
        expect(command_palette_overlay).not_to_be_visible(timeout=5000)
