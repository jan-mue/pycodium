"""Central conftest for all test types (unit, integration, performance).

Shared fixtures that can be used across all test directories.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from reflex.testing import AppHarness

from pycodium.constants import PROJECT_ROOT_DIR

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture(scope="session")
def reflex_web_app() -> Generator[AppHarness, None, None]:
    """Start the PyCodium Reflex app for the test session."""
    with AppHarness.create(root=PROJECT_ROOT_DIR) as harness:
        yield harness
