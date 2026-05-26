"""Performance test for editor file loading.

This test measures the complete time from page navigation to displaying
a file's content in the Monaco editor.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.helpers import navigate_to_app_with_path, wait_for_editor_content

if TYPE_CHECKING:
    from pathlib import Path

    from playwright.sync_api import Page
    from reflex.testing import AppHarness


FILE_CONTENT = """# Test file
print("Hello, World!")
"""


@pytest.fixture(scope="module")
def test_file(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Create a test file for performance testing."""
    project_dir = tmp_path_factory.mktemp("perf_test_project")
    test_file_path = project_dir / "test_file.py"
    test_file_path.write_text(FILE_CONTENT)
    return test_file_path


@pytest.mark.benchmark
def test_app_startup_to_editor_display_time(
    reflex_web_app: AppHarness, test_file: Path, page: Page, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Benchmark the time from page navigation to seeing file content in the editor."""
    navigate_to_app_with_path(reflex_web_app, page, test_file, monkeypatch)
    wait_for_editor_content(page, "Hello, World!", timeout=10000)
