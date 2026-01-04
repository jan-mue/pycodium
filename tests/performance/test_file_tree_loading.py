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

    The initial path is set via the set_initial_path function before the
    Reflex app starts, simulating the CLI argument behavior.

    Args:
        reflex_web_app: The running AppHarness instance.
        page: Playwright page fixture.
        fastapi_repo: Path to the cloned FastAPI repository.
    """
    assert reflex_web_app.frontend_url is not None
    folder_name = fastapi_repo.name

    # Navigate to the app - the initial path is already set via conftest
    page.goto(reflex_web_app.frontend_url)
    page.wait_for_load_state("networkidle")

    # Verify explorer is visible
    file_explorer = page.locator('[data-testid="file-explorer"]')
    expect(file_explorer).to_be_visible()

    # Wait for the folder to appear in the file explorer
    # The folder name should be visible as the root of the tree
    # Use .first because there may be a subfolder also named "fastapi"
    folder_locator = page.locator(f'.folder-item:has-text("{folder_name}")').first
    folder_locator.wait_for(state="visible", timeout=30000)

    # Verify the folder is visible
    expect(folder_locator).to_be_visible()


@pytest.mark.benchmark
def test_subdirectory_lazy_load_time(
    reflex_web_app: AppHarness,
    page: Page,
    fastapi_repo: Path,
) -> None:
    """Benchmark the lazy loading time when expanding a subdirectory.

    This test measures the time from clicking a folder to seeing its contents.
    Tests the lazy loading optimization.

    Args:
        reflex_web_app: The running AppHarness instance.
        page: Playwright page fixture.
        fastapi_repo: Path to the cloned FastAPI repository.
    """
    assert reflex_web_app.frontend_url is not None
    folder_name = fastapi_repo.name

    # Navigate to the app
    page.goto(reflex_web_app.frontend_url)
    page.wait_for_load_state("networkidle")

    # Wait for root folder to appear
    # Use .first because there may be a subfolder also named "fastapi"
    root_folder = page.locator(f'.folder-item:has-text("{folder_name}")').first
    root_folder.wait_for(state="visible", timeout=30000)

    # The root folder should already be expanded (it's in expanded_folders)
    # Look for the "fastapi" subfolder which contains the main source code
    # Use .nth(1) because the first match is the root folder, second is the subfolder
    subfolder = page.locator('.folder-item:has-text("fastapi")').nth(1)

    # Click to expand the subdirectory (this triggers lazy loading)
    subfolder.click()

    # Wait for files to appear (e.g., __init__.py in the fastapi/ directory)
    child_file = page.locator('.file-item:has-text("__init__.py")')
    child_file.first.wait_for(state="visible", timeout=10000)

    # Verify expansion worked
    expect(child_file.first).to_be_visible()
