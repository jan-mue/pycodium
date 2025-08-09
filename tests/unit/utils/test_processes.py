from __future__ import annotations

import time
from typing import TYPE_CHECKING

import pytest

from pycodium.utils.processes import terminate_or_kill_process_on_port, wait_for_port

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
