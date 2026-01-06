"""Central conftest for all test types (unit, integration, performance).

This module provides shared fixtures and utilities that can be used across
all test directories. Test-specific fixtures should remain in their
respective conftest.py files.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
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
    """Create a Typer CLI runner for testing CLI commands.

    Returns:
        CliRunner instance for invoking CLI commands in tests.
    """
    return CliRunner()


@contextmanager
def initial_path_env(path: Path | str | None) -> Generator[None, None, None]:
    """Context manager to temporarily set the PYCODIUM_INITIAL_PATH environment variable.

    This is useful for tests that need to start the app with a specific initial path,
    simulating what happens when the CLI is invoked with a path argument.

    Args:
        path: The path to set as the initial path. If None, the environment variable
              will be unset (if it was set) and restored to its original state on exit.

    Yields:
        None

    Example:
        with initial_path_env(tmp_path / "my_project"):
            with AppHarness.create(root=PROJECT_ROOT_DIR) as harness:
                # harness will have the initial path set
                pass
    """
    original_env = os.environ.get(INITIAL_PATH_ENV_VAR)

    if path is not None:
        os.environ[INITIAL_PATH_ENV_VAR] = str(path)
    elif INITIAL_PATH_ENV_VAR in os.environ:
        del os.environ[INITIAL_PATH_ENV_VAR]

    try:
        yield
    finally:
        if original_env is not None:
            os.environ[INITIAL_PATH_ENV_VAR] = original_env
        elif INITIAL_PATH_ENV_VAR in os.environ:
            del os.environ[INITIAL_PATH_ENV_VAR]


@pytest.fixture(scope="session")
def reflex_web_app() -> Generator[AppHarness, None, None]:
    """Start the PyCodium Reflex app for the test session.

    This fixture provides a basic app harness without any initial path set.
    For tests that require a specific initial path, use the `initial_path_env`
    context manager or create a custom fixture in the test module.

    Yields:
        Running AppHarness instance.
    """
    with AppHarness.create(root=PROJECT_ROOT_DIR) as harness:
        yield harness


@pytest.fixture
def app_page(reflex_web_app: AppHarness, page: Page) -> Page:
    """Navigate to the app's frontend URL and return the page.

    This fixture navigates to the running app and waits for it to be ready.
    It works with any `reflex_web_app` fixture (including custom ones that
    set an initial path).

    Args:
        reflex_web_app: The running AppHarness instance.
        page: Playwright page fixture.

    Returns:
        Playwright page navigated to the app's frontend URL.
    """
    assert reflex_web_app.frontend_url is not None
    page.goto(reflex_web_app.frontend_url)
    page.wait_for_load_state("networkidle")
    return page


def create_app_harness_with_path(path: Path | str) -> Generator[AppHarness, None, None]:
    """Create an AppHarness with a specific initial path.

    This is a helper generator function for creating custom app harness fixtures
    that need a specific initial path. Use this in test-specific conftest.py files.

    Args:
        path: The initial path to set for the app.

    Yields:
        Running AppHarness instance.

    Example:
        @pytest.fixture(scope="session")
        def my_custom_app(tmp_path_factory):
            test_dir = tmp_path_factory.mktemp("test") / "project"
            test_dir.mkdir()
            yield from create_app_harness_with_path(test_dir)
    """
    with initial_path_env(path), AppHarness.create(root=PROJECT_ROOT_DIR) as harness:
        yield harness


def navigate_to_app(harness: AppHarness, page: Page) -> Page:
    """Navigate a Playwright page to the app's frontend URL.

    This is a helper function for creating custom page fixtures that work
    with custom app harness fixtures.

    Args:
        harness: The running AppHarness instance.
        page: Playwright page fixture.

    Returns:
        Playwright page navigated to the app's frontend URL.
    """
    assert harness.frontend_url is not None
    page.goto(harness.frontend_url)
    page.wait_for_load_state("networkidle")
    return page
