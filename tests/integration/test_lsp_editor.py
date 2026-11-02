"""Integration tests for LSP actions in the editor using Playwright.

These tests verify that LSP features like hover work correctly
in the Monaco editor with the basedpyright language server.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from playwright.sync_api import expect

from tests.helpers import (
    navigate_to_app_with_path,
    open_file,
    wait_for_editor_visible,
)

if TYPE_CHECKING:
    from pathlib import Path

    from playwright.sync_api import Page
    from reflex.testing import AppHarness


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


@pytest.fixture
def lsp_editor_page(
    reflex_web_app: AppHarness, page: Page, lsp_test_folder: Path, monkeypatch: pytest.MonkeyPatch
) -> Page:
    """Navigate to the app and open a Python file for LSP testing."""
    page = navigate_to_app_with_path(reflex_web_app, page, lsp_test_folder, monkeypatch)
    page.wait_for_timeout(3000)

    open_file(page, "main.py")
    wait_for_editor_visible(page, timeout=15000)

    page.wait_for_timeout(5000)
    return page


class TestLSPHover:
    """Tests for LSP hover functionality."""

    def test_hover_on_function_shows_signature(self, lsp_editor_page: Page) -> None:
        """Test that hovering over a function call shows its signature.

        This test navigates to the `greet` function call and triggers hover
        to verify the LSP provides type information.
        """
        editor = lsp_editor_page.locator(".monaco-editor")
        editor.click()

        lsp_editor_page.keyboard.press("Meta+g")
        lsp_editor_page.wait_for_timeout(300)
        lsp_editor_page.keyboard.type("20")
        lsp_editor_page.keyboard.press("Enter")
        lsp_editor_page.wait_for_timeout(500)

        lsp_editor_page.keyboard.press("Home")
        for _ in range(9):  # Move past "result = "
            lsp_editor_page.keyboard.press("ArrowRight")

        lsp_editor_page.keyboard.press("Meta+k")
        lsp_editor_page.wait_for_timeout(100)
        lsp_editor_page.keyboard.press("Meta+i")

        hover_widget = lsp_editor_page.locator(".monaco-hover")
        expect(hover_widget).to_be_visible(timeout=15000)

        hover_content = lsp_editor_page.locator(".monaco-hover-content")
        expect(hover_content).to_be_visible(timeout=5000)

        hover_text = hover_content.inner_text()
        assert "greet" in hover_text, f"Expected 'greet' in hover, got: {hover_text}"

    def test_hover_on_class_shows_class_info(self, lsp_editor_page: Page) -> None:
        """Test that hovering over a class shows class information."""
        editor = lsp_editor_page.locator(".monaco-editor")
        editor.click()

        lsp_editor_page.keyboard.press("Meta+g")
        lsp_editor_page.wait_for_timeout(300)
        lsp_editor_page.keyboard.type("21")
        lsp_editor_page.keyboard.press("Enter")
        lsp_editor_page.wait_for_timeout(500)

        lsp_editor_page.keyboard.press("Home")
        for _ in range(7):  # Move past "calc = "
            lsp_editor_page.keyboard.press("ArrowRight")

        lsp_editor_page.keyboard.press("Meta+k")
        lsp_editor_page.wait_for_timeout(100)
        lsp_editor_page.keyboard.press("Meta+i")

        hover_widget = lsp_editor_page.locator(".monaco-hover")
        expect(hover_widget).to_be_visible(timeout=15000)

        hover_content = lsp_editor_page.locator(".monaco-hover-content")
        hover_text = hover_content.inner_text()
        assert "Calculator" in hover_text, f"Expected 'Calculator' in hover, got: {hover_text}"


class TestLSPGoToDefinition:
    """Tests for LSP go-to-definition functionality."""

    def test_f12_navigates_to_function_definition(self, lsp_editor_page: Page) -> None:
        """Test that F12 navigates to a function's definition.

        This verifies the LSP definition provider is working correctly.
        """
        editor = lsp_editor_page.locator(".monaco-editor")
        editor.click()

        lsp_editor_page.keyboard.press("Meta+g")
        lsp_editor_page.wait_for_timeout(300)
        lsp_editor_page.keyboard.type("20")
        lsp_editor_page.keyboard.press("Enter")
        lsp_editor_page.wait_for_timeout(500)

        lsp_editor_page.keyboard.press("Home")
        for _ in range(9):
            lsp_editor_page.keyboard.press("ArrowRight")

        lsp_editor_page.keyboard.press("F12")
        lsp_editor_page.wait_for_timeout(3000)

        lsp_editor_page.wait_for_timeout(500)

        def_line = lsp_editor_page.locator(".view-line:has-text('def greet(name: str)')")
        expect(def_line).to_be_visible(timeout=5000)
