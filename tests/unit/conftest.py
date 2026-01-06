import pytest
from typer.testing import CliRunner


@pytest.fixture(scope="session")
def runner() -> CliRunner:
    """Create a Typer CLI runner for testing CLI commands."""
    return CliRunner()
