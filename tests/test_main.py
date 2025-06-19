from __future__ import annotations

from typing import TYPE_CHECKING

from pycodium import __version__
from pycodium.main import app

if TYPE_CHECKING:
    from typer.testing import CliRunner


def test_cli_prints_version(runner: CliRunner) -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.stdout == __version__ + "\n"
