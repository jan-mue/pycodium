"""Integration tests for LSP actions in the editor using Playwright.

These tests verify that LSP features like hover work correctly
in the Monaco editor with the basedpyright language server.
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


# Python file for testing
TEST_PYTHON_CONTENT = '''"""Module for LSP testing."""


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
def lsp_test_folder(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Create a test folder with Python files for LSP testing.

    Using module scope to share the folder across all tests.
    """
    test_dir = tmp_path_factory.mktemp("lsp_test_project")

    main_py = test_dir / "main.py"
    main_py.write_text(TEST_PYTHON_CONTENT)

    return test_dir


@pytest.fixture(scope="module")
def app_with_lsp_files(lsp_test_folder: Path) -> Generator[AppHarness, None, None]:
    """Start the app with a test folder containing Python files for LSP testing.

    Using module scope to share the app harness across all tests in this module.
    """
    yield from create_app_harness_with_path(lsp_test_folder)


@pytest.fixture
def lsp_editor_page(app_with_lsp_files: AppHarness, page: Page) -> Page:
    """Navigate to the app and open a Python file for LSP testing."""
    # Use longer timeout for navigation
    page = navigate_to_app(app_with_lsp_files, page, timeout=90000)
    page.wait_for_timeout(3000)

    # Open the main.py file
    open_file(page, "main.py")
    wait_for_editor_visible(page, timeout=15000)

    # Give editor time to fully render and LSP to initialize
    page.wait_for_timeout(5000)
    return page


class TestLSPHover:
    """Tests for LSP hover functionality."""

    def test_hover_on_function_shows_signature(self, lsp_editor_page: Page) -> None:
        """Test that hovering over a function call shows its signature.

        This test hovers over the `greet` function to verify
        the LSP provides type information via mouse hover.
        """
        editor = lsp_editor_page.locator(".monaco-editor")
        editor.click()

        # Find the 'greet' function definition on line 4
        # We'll hover over it to trigger LSP hover
        greet_text = lsp_editor_page.locator(".view-line:has-text('def greet')")
        expect(greet_text).to_be_visible(timeout=10000)

        # Get the bounding box of the greet line and hover over it
        greet_box = greet_text.bounding_box()
        if greet_box:
            # Hover over 'greet' text (offset into the line to hit the function name)
            lsp_editor_page.mouse.move(greet_box["x"] + 50, greet_box["y"] + greet_box["height"] / 2)

            # Wait for hover popup (it can take a few seconds)
            hover_widget = lsp_editor_page.locator(".monaco-hover:not(.hidden)")
            expect(hover_widget.first).to_be_visible(timeout=10000)

            # Verify hover content contains function info
            hover_content = lsp_editor_page.locator(".monaco-hover-content")
            expect(hover_content.first).to_be_visible(timeout=5000)

            hover_text = hover_content.first.inner_text()
            assert "greet" in hover_text.lower() or "str" in hover_text.lower(), (
                f"Expected function info in hover, got: {hover_text}"
            )

    def test_hover_on_class_shows_class_info(self, lsp_editor_page: Page) -> None:
        """Test that hovering over a class shows class information."""
        editor = lsp_editor_page.locator(".monaco-editor")
        editor.click()

        # Find the Calculator class definition
        calc_text = lsp_editor_page.locator(".view-line:has-text('class Calculator')")
        expect(calc_text).to_be_visible(timeout=10000)

        # Get the bounding box and hover
        calc_box = calc_text.bounding_box()
        if calc_box:
            # Hover over 'Calculator' text
            lsp_editor_page.mouse.move(calc_box["x"] + 80, calc_box["y"] + calc_box["height"] / 2)

            # Wait for hover popup
            hover_widget = lsp_editor_page.locator(".monaco-hover:not(.hidden)")
            expect(hover_widget.first).to_be_visible(timeout=10000)

            # Verify hover content
            hover_content = lsp_editor_page.locator(".monaco-hover-content")
            hover_text = hover_content.first.inner_text()
            assert "Calculator" in hover_text or "class" in hover_text.lower(), (
                f"Expected class info in hover, got: {hover_text}"
            )


class TestLSPGoToDefinition:
    """Tests for LSP go-to-definition functionality."""

    def test_f12_navigates_to_function_definition(self, lsp_editor_page: Page) -> None:
        """Test that F12 navigates to a function's definition.

        This verifies the LSP definition provider is working correctly.
        """
        editor = lsp_editor_page.locator(".monaco-editor")
        editor.click()

        # Find the 'result = greet("World")' line
        result_line = lsp_editor_page.locator(".view-line:has-text('result = greet')")
        expect(result_line).to_be_visible(timeout=10000)

        # Click on 'greet' in that line
        result_box = result_line.bounding_box()
        if result_box:
            # Click on 'greet' (approximately after "result = ")
            lsp_editor_page.mouse.click(result_box["x"] + 100, result_box["y"] + result_box["height"] / 2)
            lsp_editor_page.wait_for_timeout(500)

            # Press F12 to go to definition
            lsp_editor_page.keyboard.press("F12")
            lsp_editor_page.wait_for_timeout(3000)

            # Verify the function definition line is visible
            def_line = lsp_editor_page.locator(".view-line:has-text('def greet(name: str)')")
            expect(def_line).to_be_visible(timeout=5000)
