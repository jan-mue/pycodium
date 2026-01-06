"""Central conftest for all test types (unit, integration, performance).

Shared fixtures and utilities that can be used across all test directories.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from reflex.testing import AppHarness
from typer.testing import CliRunner

from pycodium.constants import INITIAL_PATH_ENV_VAR, PROJECT_ROOT_DIR

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

    from playwright.sync_api import Page


@pytest.fixture(scope="session")
def runner() -> CliRunner:
    """Create a Typer CLI runner for testing CLI commands."""
    return CliRunner()


@pytest.fixture(scope="session")
def reflex_web_app() -> Generator[AppHarness, None, None]:
    """Start the PyCodium Reflex app for the test session."""
    with AppHarness.create(root=PROJECT_ROOT_DIR) as harness:
        yield harness


@pytest.fixture
def app_page(reflex_web_app: AppHarness, page: Page) -> Page:
    """Navigate to the app's frontend URL and return the page."""
    assert reflex_web_app.frontend_url is not None
    page.goto(reflex_web_app.frontend_url)
    page.wait_for_load_state("networkidle")
    return page


def create_app_harness_with_path(path: Path | str) -> Generator[AppHarness, None, None]:
    """Create an AppHarness with a specific initial path."""
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setenv(INITIAL_PATH_ENV_VAR, str(path))
        with AppHarness.create(root=PROJECT_ROOT_DIR) as harness:
            yield harness


def navigate_to_app(harness: AppHarness, page: Page) -> Page:
    """Navigate a Playwright page to the app's frontend URL."""
    assert harness.frontend_url is not None
    page.goto(harness.frontend_url)
    page.wait_for_load_state("networkidle")
    return page
