from __future__ import annotations

from typing import TYPE_CHECKING

from inline_snapshot import snapshot
from reflex.constants import LogLevel
from reflex.utils import exec  # noqa: A004

from pycodium import __version__
from pycodium.constants import PROJECT_ROOT_DIR
from pycodium.main import app

if TYPE_CHECKING:
    from pytest_mock import MockerFixture
    from typer.testing import CliRunner


def test_cli_prints_version(runner: CliRunner) -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.stdout == __version__ + "\n"


def test_cli_starts_ide(runner: CliRunner, mocker: MockerFixture) -> None:
    # given
    mock_reset = mocker.patch("pycodium.main.reset_disk_state_manager")
    mock_run_concurrent = mocker.patch("pycodium.main.processes.run_concurrently_context")
    mock_wait_for_port = mocker.patch("pycodium.main.wait_for_port")
    mock_create_window = mocker.patch("pycodium.main.webview.create_window")
    mock_start = mocker.patch("pycodium.main.webview.start")

    # when
    result = runner.invoke(app)
    assert result.exit_code == 0

    # then
    mock_reset.assert_called_once()
    mock_run_concurrent.assert_called_once_with((exec.run_backend_prod, "0.0.0.0", 8000, LogLevel.WARNING, True))
    mock_wait_for_port.assert_called_with(8000)
    mock_create_window.assert_called_with(
        title=snapshot("PyCodium IDE"),
        url=snapshot(str(PROJECT_ROOT_DIR / ".web" / "_static" / "index.html")),
        width=snapshot(1300),
        height=snapshot(800),
    )
    mock_start.assert_called_once()
