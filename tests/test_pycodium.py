from collections.abc import Generator

import httpx
import pytest
from reflex.testing import AppHarness

from pycodium.constants import PROJECT_ROOT_DIR


@pytest.fixture(scope="session")
def reflex_web_app() -> Generator[AppHarness, None, None]:
    with AppHarness.create(root=PROJECT_ROOT_DIR) as harness:
        yield harness


def test_frontend_reachable(reflex_web_app: AppHarness) -> None:
    assert reflex_web_app.frontend_url is not None
    response = httpx.get(reflex_web_app.frontend_url, timeout=60)
    assert response.status_code == 200
