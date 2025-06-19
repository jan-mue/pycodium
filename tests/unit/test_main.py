from __future__ import annotations

import time
from typing import TYPE_CHECKING

import pytest
from inline_snapshot import snapshot
from reflex.constants import LogLevel
from reflex.utils import exec  # noqa: A004

from pycodium import __version__
from pycodium.constants import PROJECT_ROOT_DIR
from pycodium.main import app, terminate_or_kill_process_on_port, wait_for_port

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


def test_terminate_or_kill_process_on_port(mocker: MockerFixture) -> None:
    mock_processes = mocker.patch("pycodium.main.processes")
    mock_proc = mocker.Mock()
    mock_processes.get_process_on_port.return_value = mock_proc
    mock_proc.wait.return_value = None

    terminate_or_kill_process_on_port(9999, timeout=1)

    mock_proc.terminate.assert_called_once()
    mock_proc.wait.assert_called_once_with(timeout=1)


def test_terminate_or_kill_process_on_port_no_proc(mocker: MockerFixture) -> None:
    mock_processes = mocker.patch("pycodium.main.processes")
    mock_logger = mocker.patch("pycodium.main.logger")
    mock_processes.get_process_on_port.return_value = None

    terminate_or_kill_process_on_port(8888, timeout=1)

    mock_logger.warning.assert_called_with("No process found on port 8888.")


def test_wait_for_port_success(mocker: MockerFixture) -> None:
    mock_is_process_on_port = mocker.patch("pycodium.main.processes.is_process_on_port", return_value=True)
    wait_for_port(12345, timeout=1)
    mock_is_process_on_port.assert_called_with(12345)


def test_wait_for_port_timeout(mocker: MockerFixture) -> None:
    mocker.patch("pycodium.main.processes.is_process_on_port", return_value=False)
    start = time.time()
    with pytest.raises(TimeoutError):
        wait_for_port(54321, timeout=1)
    assert time.time() - start >= 1
