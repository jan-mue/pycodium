"""Verify real language server results through the Monaco UI and Reflex bridge."""

from __future__ import annotations

import mimetypes
from typing import TYPE_CHECKING
from urllib.parse import urlparse

import pytest
from playwright.sync_api import expect

from pycodium.constants import PROJECT_ROOT_DIR
from tests.helpers import navigate_to_app_with_path, open_file, wait_for_editor_visible

if TYPE_CHECKING:
    from pathlib import Path

    from playwright.sync_api import Page, Route
    from reflex.testing import AppHarness

CONTENT = '''def greet(name: str) -> str:
    """Greet a person."""
    return name

result = greet("World")
'''
EDITOR = "window.monaco.editor.getEditors()[0]"


@pytest.fixture
def lsp_page(reflex_web_app: AppHarness, page: Page, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Page:
    def serve_monaco(route: Route) -> None:
        # Serve the installed, unmodified Monaco assets without requiring CDN access.
        relative = urlparse(route.request.url).path.split("/min/vs/", 1)[1]
        asset = PROJECT_ROOT_DIR / ".web/node_modules/monaco-editor/min/vs" / relative
        route.fulfill(
            path=asset,
            content_type=mimetypes.guess_type(str(asset))[0] or "application/javascript",
            headers={"Access-Control-Allow-Origin": "*"},
        )

    page.route("https://cdn.jsdelivr.net/npm/monaco-editor@*/min/vs/**", serve_monaco)
    (tmp_path / "main.py").write_text(CONTENT)
    navigate_to_app_with_path(reflex_web_app, page, tmp_path, monkeypatch)
    open_file(page, "main.py")
    wait_for_editor_visible(page)
    page.wait_for_function("window.monaco?.editor.getEditors().length > 0")
    return page


def action(page: Page, command: str, line: int, column: int) -> None:
    """Invoke an editor action at a known symbol without platform specific keys."""
    page.evaluate(
        """({command, line, column}) => {
            const editor = window.monaco.editor.getEditors()[0];
            editor.focus();
            editor.setPosition({lineNumber: line, column});
            editor.trigger('test', command, null);
        }""",
        {"command": command, "line": line, "column": column},
    )


def test_repeated_hover(lsp_page: Page) -> None:
    for _ in range(2):
        action(lsp_page, "editor.action.showHover", 5, 11)
        hover = lsp_page.locator(".monaco-hover-content").first
        expect(hover).to_be_visible(timeout=15000)
        expect(hover).to_contain_text("Greet a person")
        lsp_page.keyboard.press("Escape")
        expect(hover).not_to_be_visible()


def test_completion(lsp_page: Page) -> None:
    lsp_page.evaluate(f"{EDITOR}.setValue('import os\\nos.pa')")
    action(lsp_page, "editor.action.triggerSuggest", 2, 6)
    suggestions = lsp_page.locator(".suggest-widget.visible")
    expect(suggestions).to_be_visible(timeout=15000)
    expect(suggestions).to_contain_text("path")


def test_definition(lsp_page: Page) -> None:
    action(lsp_page, "editor.action.revealDefinition", 5, 11)
    lsp_page.wait_for_function(f"{EDITOR}.getPosition().lineNumber === 1", timeout=15000)


def test_signature_help(lsp_page: Page) -> None:
    lsp_page.evaluate(f"{EDITOR}.setValue({CONTENT!r} + '\\ngreet(')")
    action(lsp_page, "editor.action.triggerParameterHints", 7, 7)
    hints = lsp_page.locator(".parameter-hints-widget.visible")
    expect(hints).to_be_visible(timeout=15000)
    expect(hints).to_contain_text("name")


def test_references(lsp_page: Page) -> None:
    action(lsp_page, "editor.action.referenceSearch.trigger", 1, 6)
    references = lsp_page.locator(".reference-zone-widget")
    expect(references).to_be_visible(timeout=15000)
    expect(references).to_contain_text("main.py")


def test_rename_applies_edits(lsp_page: Page) -> None:
    action(lsp_page, "editor.action.rename", 1, 6)
    rename = lsp_page.locator(".rename-box input")
    expect(rename).to_be_visible(timeout=15000)
    rename.fill("welcome")
    rename.press("Enter")
    lsp_page.wait_for_function(f"{EDITOR}.getValue().includes('result = welcome(')", timeout=15000)
    assert "def welcome(" in lsp_page.evaluate(f"{EDITOR}.getValue()")


def test_diagnostics_update_and_clear(lsp_page: Page) -> None:
    lsp_page.evaluate(f"{EDITOR}.setValue('value: int = \"wrong\"')")
    lsp_page.wait_for_function(
        "window.monaco.editor.getModelMarkers({owner: 'basedpyright'}).some(m => m.severity === 8)", timeout=20000
    )
    expect(lsp_page.locator(".squiggly-error").first).to_be_visible()
    lsp_page.evaluate(f"{EDITOR}.setValue('value: int = 1')")
    lsp_page.wait_for_function(
        "window.monaco.editor.getModelMarkers({owner: 'basedpyright'}).length === 0", timeout=20000
    )


def test_lsp_after_interpreter_change(lsp_page: Page) -> None:
    lsp_page.keyboard.press("Control+Shift+p")
    palette = lsp_page.locator("#command-palette-input")
    expect(palette).to_be_visible()
    palette.fill("Python: Select Interpreter")
    lsp_page.locator("#command-select-python").click()
    interpreter = lsp_page.locator("#interpreter-list .command-palette-item").first
    expect(interpreter).to_be_visible(timeout=15000)
    interpreter.click()
    expect(lsp_page.get_by_text("Python interpreter set to:", exact=False)).to_be_visible(timeout=15000)
    expect(lsp_page.locator("#command-palette-container")).not_to_be_visible()
    action(lsp_page, "editor.action.showHover", 5, 11)
    expect(lsp_page.locator(".monaco-hover-content").first).to_contain_text("Greet a person", timeout=15000)
