from __future__ import annotations

import time
from typing import TYPE_CHECKING

import psutil
import pytest

from pycodium.utils.processes import get_process_on_port, terminate_or_kill_process_on_port, wait_for_port

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


def test_terminate_or_kill_process_on_port(mocker: MockerFixture) -> None:
    mock_proc = mocker.Mock()
    mocker.patch("pycodium.utils.processes.get_process_on_port", return_value=mock_proc)
    mock_proc.wait.return_value = None

    terminate_or_kill_process_on_port(9999, timeout=1)

    mock_proc.terminate.assert_called_once()
    mock_proc.wait.assert_called_once_with(timeout=1)


def test_terminate_or_kill_process_on_port_no_proc(mocker: MockerFixture) -> None:
    mock_logger = mocker.patch("pycodium.utils.processes.logger")
    mocker.patch("pycodium.utils.processes.get_process_on_port", return_value=None)

    terminate_or_kill_process_on_port(8888, timeout=1)

    mock_logger.warning.assert_called_with("No process found on port 8888.")


def test_wait_for_port_success(mocker: MockerFixture) -> None:
    mock_get_process_on_port = mocker.patch("pycodium.utils.processes.get_process_on_port")
    wait_for_port(12345, timeout=1)
    mock_get_process_on_port.assert_called_with(12345)


def test_wait_for_port_timeout(mocker: MockerFixture) -> None:
    mocker.patch("pycodium.utils.processes.get_process_on_port", return_value=None)
    start = time.time()
    with pytest.raises(TimeoutError):
        wait_for_port(54321, timeout=1)
    assert time.time() - start >= 1


def test_get_process_on_port_found(mocker: MockerFixture) -> None:
    mock_process = mocker.Mock()
    mock_process.pid = 1234
    mock_process.name.return_value = "test_process"

    mock_connection = mocker.Mock()
    mock_connection.laddr.port = 8080

    mock_process.net_connections.return_value = [mock_connection]

    mocker.patch("pycodium.utils.processes.psutil.process_iter", return_value=[mock_process])

    result = get_process_on_port(8080)

    assert result == mock_process
    mock_process.net_connections.assert_called_once_with(kind="inet")


def test_get_process_on_port_not_found(mocker: MockerFixture) -> None:
    mock_process = mocker.Mock()
    mock_connection = mocker.Mock()
    mock_connection.laddr.port = 9090
    mock_process.net_connections.return_value = [mock_connection]

    mocker.patch("pycodium.utils.processes.psutil.process_iter", return_value=[mock_process])

    result = get_process_on_port(8080)

    assert result is None


def test_get_process_on_port_no_processes(mocker: MockerFixture) -> None:
    mocker.patch("pycodium.utils.processes.psutil.process_iter", return_value=[])

    result = get_process_on_port(8080)

    assert result is None


def test_get_process_on_port_handles_exceptions(mocker: MockerFixture) -> None:
    mock_process1 = mocker.Mock()
    mock_process1.net_connections.side_effect = psutil.NoSuchProcess(pid=123)

    mock_process2 = mocker.Mock()
    mock_connection = mocker.Mock()
    mock_connection.laddr.port = 8080
    mock_process2.net_connections.return_value = [mock_connection]

    mocker.patch("pycodium.utils.processes.psutil.process_iter", return_value=[mock_process1, mock_process2])

    result = get_process_on_port(8080)

    assert result == mock_process2


def test_get_process_on_port_multiple_connections(mocker: MockerFixture) -> None:
    mock_process = mocker.Mock()

    mock_connection1 = mocker.Mock()
    mock_connection1.laddr.port = 9090

    mock_connection2 = mocker.Mock()
    mock_connection2.laddr.port = 8080

    mock_connection3 = mocker.Mock()
    mock_connection3.laddr.port = 3000

    mock_process.net_connections.return_value = [mock_connection1, mock_connection2, mock_connection3]

    mocker.patch("pycodium.utils.processes.psutil.process_iter", return_value=[mock_process])

    result = get_process_on_port(8080)

    assert result == mock_process
