"""Shared conftest for all integration tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from reflex.testing import AppHarness

from pycodium.constants import PROJECT_ROOT_DIR

if TYPE_CHECKING:
    from collections.abc import Generator

    from playwright.sync_api import Page


@pytest.fixture(scope="session")
def reflex_web_app() -> Generator[AppHarness, None, None]:
    """Start the PyCodium Reflex app for the test session.

    Yields:
        Running AppHarness instance.
    """
    with AppHarness.create(root=PROJECT_ROOT_DIR) as harness:
        yield harness


@pytest.fixture
def app_page(reflex_web_app: AppHarness, page: Page) -> Page:
    """Navigate to the app's frontend URL and return the page.

    Args:
        reflex_web_app: The running AppHarness instance.
        page: Playwright page fixture.

    Returns:
        Playwright page navigated to the app's frontend URL.
    """
    assert reflex_web_app.frontend_url is not None
    page.goto(reflex_web_app.frontend_url)
    # Wait for the app to be ready (Reflex apps show a loading spinner initially)
    page.wait_for_load_state("networkidle")
    return page
