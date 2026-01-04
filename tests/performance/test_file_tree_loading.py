"""Performance tests for file tree loading using CodSpeed benchmarking.

These tests measure how quickly PyCodium can display a large directory structure
in the file explorer. The FastAPI repository is used as a real-world benchmark.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from playwright.sync_api import expect

if TYPE_CHECKING:
    from pathlib import Path

    from playwright.sync_api import Page
    from reflex.testing import AppHarness


@pytest.mark.benchmark
def test_file_tree_initial_load_time(
    reflex_web_app: AppHarness,
    page: Page,
    fastapi_repo: Path,
) -> None:
    """Benchmark the initial file tree loading time for a large repository.

    This test measures the time from page load to seeing the root folder
    in the explorer. Uses FastAPI repo (~1000+ files) as a real-world benchmark.

    Args:
        reflex_web_app: The running AppHarness instance.
        page: Playwright page fixture.
        fastapi_repo: Path to the cloned FastAPI repository.
    """
    assert reflex_web_app.frontend_url is not None
    folder_name = fastapi_repo.name

    page.goto(reflex_web_app.frontend_url)
    page.wait_for_load_state("networkidle")

    file_explorer = page.locator('[data-testid="file-explorer"]')
    expect(file_explorer).to_be_visible()

    folder_locator = page.locator(f'.folder-item:has-text("{folder_name}")').first
    folder_locator.wait_for(state="visible", timeout=30000)
    expect(folder_locator).to_be_visible()


@pytest.mark.benchmark
def test_subdirectory_lazy_load_time(
    reflex_web_app: AppHarness,
    page: Page,
    fastapi_repo: Path,
) -> None:
    """Benchmark the lazy loading time when expanding a subdirectory.

    This test measures the time from clicking a folder to seeing its contents.

    Args:
        reflex_web_app: The running AppHarness instance.
        page: Playwright page fixture.
        fastapi_repo: Path to the cloned FastAPI repository.
    """
    assert reflex_web_app.frontend_url is not None
    folder_name = fastapi_repo.name

    page.goto(reflex_web_app.frontend_url)
    page.wait_for_load_state("networkidle")

    root_folder = page.locator(f'.folder-item:has-text("{folder_name}")').first
    root_folder.wait_for(state="visible", timeout=30000)

    subfolder = page.locator('.folder-item:has-text("docs")').first
    child_file = page.locator('.file-item:has-text(".md")').first

    if child_file.is_visible():
        subfolder.click()
        page.wait_for_timeout(500)

    subfolder.click()
    child_file.wait_for(state="visible", timeout=10000)
    expect(child_file).to_be_visible()
