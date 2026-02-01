"""Conftest for performance tests."""

from __future__ import annotations

import shutil
import subprocess
from typing import TYPE_CHECKING

import pytest

from tests.helpers import create_app_harness_with_path, navigate_to_app

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

    from playwright.sync_api import Page
    from reflex.testing import AppHarness


FASTAPI_REPO_URL = "https://github.com/fastapi/fastapi.git"
FASTAPI_TAG = "0.128.0"


@pytest.fixture(scope="session")
def fastapi_repo(tmp_path_factory: pytest.TempPathFactory) -> Generator[Path, None, None]:
    """Clone the FastAPI repository at a specific tag for performance testing."""
    repo_path = tmp_path_factory.mktemp("repos") / "fastapi"

    subprocess.run(
        ["git", "clone", "--depth", "1", "--branch", FASTAPI_TAG, FASTAPI_REPO_URL, str(repo_path)], check=True
    )

    yield repo_path
    shutil.rmtree(repo_path, ignore_errors=True)


@pytest.fixture(scope="session")
def reflex_web_app(fastapi_repo: Path) -> Generator[AppHarness, None, None]:
    """Start the app with the FastAPI repo as initial path."""
    yield from create_app_harness_with_path(fastapi_repo)


@pytest.fixture
def app_page(reflex_web_app: AppHarness, page: Page) -> Page:
    """Navigate to the app's frontend URL and return the page."""
    return navigate_to_app(reflex_web_app, page)
