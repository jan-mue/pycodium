"""Performance test for editor file loading.

This test measures the complete time from app startup to displaying
a file's content in the Monaco editor.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.helpers import create_app_harness_with_path, wait_for_editor_content

if TYPE_CHECKING:
    from pathlib import Path

    from playwright.sync_api import Page


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
def test_app_startup_to_editor_display_time(test_file: Path, page: Page) -> None:
    """Benchmark the time from app startup to seeing file content in the editor."""
    for harness in create_app_harness_with_path(test_file):
        assert harness.frontend_url is not None

        page.goto(harness.frontend_url)
        page.wait_for_load_state("networkidle")

        wait_for_editor_content(page, "Hello, World!", timeout=10000)
