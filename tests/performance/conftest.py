"""Shared fixtures for performance tests."""

from __future__ import annotations

import shutil
import subprocess
from typing import TYPE_CHECKING

import pytest
from reflex.testing import AppHarness

from pycodium.constants import PROJECT_ROOT_DIR, set_initial_path

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

    from playwright.sync_api import Page


# FastAPI repository details for performance testing
FASTAPI_REPO_URL = "https://github.com/fastapi/fastapi.git"
FASTAPI_TAG = "0.128.0"


@pytest.fixture(scope="session")
def fastapi_repo(tmp_path_factory: pytest.TempPathFactory) -> Generator[Path, None, None]:
    """Clone the FastAPI repository at a specific tag for performance testing.

    This fixture clones the repository once per test session and cleans up afterwards.

    Yields:
        Path to the cloned repository.
    """
    repo_path = tmp_path_factory.mktemp("repos") / "fastapi"

    subprocess.run(
        [
            "git",
            "clone",
            "--depth",
            "1",
            "--branch",
            FASTAPI_TAG,
            FASTAPI_REPO_URL,
            str(repo_path),
        ],
        check=True,
        capture_output=True,
    )

    yield repo_path
    shutil.rmtree(repo_path, ignore_errors=True)


@pytest.fixture(scope="session")
def reflex_web_app(fastapi_repo: Path) -> Generator[AppHarness, None, None]:
    """Start the PyCodium Reflex app with the FastAPI repo as initial path.

    Args:
        fastapi_repo: Path to the cloned FastAPI repository.

    Yields:
        Running AppHarness instance.
    """
    set_initial_path(fastapi_repo)
    with AppHarness.create(root=PROJECT_ROOT_DIR) as harness:
        yield harness
    set_initial_path(None)


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
    page.wait_for_load_state("networkidle")
    return page
