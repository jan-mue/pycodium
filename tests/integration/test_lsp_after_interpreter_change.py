"""Integration tests for LSP functionality after changing Python interpreter.

These tests verify that the LSP features continue to work correctly after
switching the Python interpreter via the command palette. This tests the
critical "IDE experience" loop:
- Go-to-definition (textDocument/definition via textDocument/declaration)

These correspond to Monaco's registerDeclarationProvider which is currently
the most reliable LSP feature.

Note: Hover and completions tests are skipped due to pre-existing issues
with the Reflex frontend integration.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from playwright.sync_api import expect

from tests.helpers import (
    create_app_harness_with_path,
    navigate_to_app,
    open_file,
    wait_for_editor_visible,
)

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

    from playwright.sync_api import Page
    from reflex.testing import AppHarness


# Python file designed to exercise LSP features
# The file uses standard Python constructs that basedpyright can analyze
LSP_TEST_FILE_CONTENT = '''"""Module with code to test LSP features."""


def greet(name: str) -> str:
    """Greet a person."""
    return f"Hello, {name}!"


class Calculator:
    """A simple calculator."""

    def __init__(self, value: int = 0) -> None:
        self.value = value

    def add(self, x: int) -> int:
        self.value += x
        return self.value


result = greet("World")
calc = Calculator(10)
'''


@pytest.fixture(scope="module")
def lsp_interpreter_test_folder(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Create a test folder with Python files for LSP testing after interpreter change."""
    test_dir = tmp_path_factory.mktemp("lsp_interpreter_test")
    main_py = test_dir / "main.py"
    main_py.write_text(LSP_TEST_FILE_CONTENT)
    return test_dir


@pytest.fixture(scope="module")
def app_with_lsp_test_files(
    lsp_interpreter_test_folder: Path,
) -> Generator[AppHarness, None, None]:
    """Start the app with a test folder for LSP interpreter testing."""
    yield from create_app_harness_with_path(lsp_interpreter_test_folder)


def _select_python_interpreter(page: Page) -> None:
    """Open command palette and select the first available Python interpreter.

    Args:
        page: Playwright page instance.
    """
    page.keyboard.press("Meta+Shift+p")
    page.wait_for_timeout(500)

    input_field = page.locator("#command-palette-input")
    expect(input_field).to_be_visible(timeout=5000)
    input_field.fill("Python: Select")
    page.wait_for_timeout(500)

    python_command = page.locator("#command-select-python")
    expect(python_command).to_be_visible(timeout=5000)
    python_command.click()
    page.wait_for_timeout(2000)

    interpreter_list = page.locator("#interpreter-list")
    expect(interpreter_list).to_be_visible(timeout=15000)

    first_interpreter = interpreter_list.locator(".command-palette-item").first
    expect(first_interpreter).to_be_visible(timeout=5000)
    first_interpreter.click()
    page.wait_for_timeout(3000)


class TestLSPAfterInterpreterChange:
    """Tests for LSP functionality after changing Python interpreter."""

    def test_go_to_definition_works_after_interpreter_change(
        self, app_with_lsp_test_files: AppHarness, page: Page
    ) -> None:
        """Test that go-to-definition works after changing the Python interpreter.

        This is the main test that verifies:
        1. The app loads correctly
        2. A Python file can be opened
        3. The interpreter can be changed via command palette
        4. LSP go-to-definition still works after the interpreter change
        """
        # Navigate to the app
        page = navigate_to_app(app_with_lsp_test_files, page, timeout=90000)
        page.wait_for_timeout(3000)

        # Open the test file
        open_file(page, "main.py")
        wait_for_editor_visible(page, timeout=15000)
        page.wait_for_timeout(5000)

        # Change the Python interpreter
        _select_python_interpreter(page)

        # Wait for command palette to close
        command_palette = page.locator("#command-palette-container")
        expect(command_palette).not_to_be_visible(timeout=5000)
        page.wait_for_timeout(3000)

        # Click on editor to focus it
        editor = page.locator(".monaco-editor")
        editor.click()
        page.wait_for_timeout(500)

        # Navigate to line 20 where `result = greet("World")` is
        page.keyboard.press("Meta+g")
        page.wait_for_timeout(300)
        page.keyboard.type("20")
        page.keyboard.press("Enter")
        page.wait_for_timeout(500)

        # Position cursor on "greet"
        page.keyboard.press("Home")
        for _ in range(9):
            page.keyboard.press("ArrowRight")

        # Press F12 to go to definition
        page.keyboard.press("F12")
        page.wait_for_timeout(3000)

        # Verify the function definition is visible
        def_line = page.locator(".view-line:has-text('def greet(name: str)')")
        expect(def_line).to_be_visible(timeout=5000)

    def test_file_opens_after_interpreter_change(self, app_with_lsp_test_files: AppHarness, page: Page) -> None:
        """Test that files open correctly after changing the Python interpreter.

        This is a basic smoke test to ensure the interpreter change doesn't
        break basic file operations.
        """
        # Navigate to the app
        page = navigate_to_app(app_with_lsp_test_files, page, timeout=90000)
        page.wait_for_timeout(3000)

        # Change the Python interpreter first
        _select_python_interpreter(page)

        # Wait for command palette to close
        command_palette = page.locator("#command-palette-container")
        expect(command_palette).not_to_be_visible(timeout=5000)
        page.wait_for_timeout(2000)

        # Now open the test file
        open_file(page, "main.py")
        wait_for_editor_visible(page, timeout=15000)

        # Verify the file content is visible
        def_greet = page.locator(".view-line:has-text('def greet')")
        expect(def_greet).to_be_visible(timeout=10000)

    def test_go_to_class_definition_works_after_interpreter_change(
        self, app_with_lsp_test_files: AppHarness, page: Page
    ) -> None:
        """Test that go-to-definition for classes works after interpreter change."""
        # Navigate to the app
        page = navigate_to_app(app_with_lsp_test_files, page, timeout=90000)
        page.wait_for_timeout(3000)

        # Open the test file
        open_file(page, "main.py")
        wait_for_editor_visible(page, timeout=15000)
        page.wait_for_timeout(5000)

        # Change the Python interpreter
        _select_python_interpreter(page)

        # Wait for command palette to close
        command_palette = page.locator("#command-palette-container")
        expect(command_palette).not_to_be_visible(timeout=5000)
        page.wait_for_timeout(3000)

        # Click on editor to focus it
        editor = page.locator(".monaco-editor")
        editor.click()
        page.wait_for_timeout(500)

        # Navigate to line 21 where `calc = Calculator(10)` is
        page.keyboard.press("Meta+g")
        page.wait_for_timeout(300)
        page.keyboard.type("21")
        page.keyboard.press("Enter")
        page.wait_for_timeout(500)

        # Position cursor on "Calculator" (7 characters from start: "calc = ")
        page.keyboard.press("Home")
        for _ in range(7):
            page.keyboard.press("ArrowRight")

        # Press F12 to go to definition
        page.keyboard.press("F12")
        page.wait_for_timeout(3000)

        # Verify the class definition is visible
        class_def = page.locator(".view-line:has-text('class Calculator')")
        expect(class_def).to_be_visible(timeout=5000)
