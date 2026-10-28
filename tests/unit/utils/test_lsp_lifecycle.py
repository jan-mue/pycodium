"""Regressions for language server failures and process cleanup."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest

from pycodium.utils.lsp_client import BasedPyrightLSPClient

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


@pytest.mark.parametrize("failure", [RuntimeError("LSP shutdown error"), BrokenPipeError(), TimeoutError()])
async def test_shutdown_failure_reaps_process(mocker: MockerFixture, failure: Exception) -> None:
    client = BasedPyrightLSPClient()
    process = mocker.Mock(returncode=None)
    process.wait = mocker.AsyncMock(return_value=0)
    client.process = process
    mocker.patch.object(client, "_send_request", new_callable=mocker.AsyncMock, side_effect=failure)
    await client.stop_server()
    process.terminate.assert_called_once()
    process.wait.assert_awaited_once()
    assert client.process is None


async def test_unresponsive_process_is_killed(mocker: MockerFixture) -> None:
    client = BasedPyrightLSPClient()
    process = mocker.Mock(returncode=None)
    process.wait = mocker.AsyncMock(side_effect=[asyncio.TimeoutError(), 0])
    client.process = process
    mocker.patch.object(client, "_send_request", new_callable=mocker.AsyncMock, side_effect=RuntimeError("shutdown"))
    await client.stop_server()
    process.terminate.assert_called_once()
    process.kill.assert_called_once()
    assert process.wait.await_count == 2
    assert client.process is None


async def test_initialization_failure_reaps_candidate(mocker: MockerFixture) -> None:
    client = BasedPyrightLSPClient()
    process = mocker.Mock(returncode=None)
    process.wait = mocker.AsyncMock(return_value=0)
    process.stdout.read = mocker.AsyncMock(return_value=b"")
    mocker.patch("asyncio.create_subprocess_exec", new_callable=mocker.AsyncMock, return_value=process)
    mocker.patch.object(client, "_initialize", new_callable=mocker.AsyncMock, side_effect=RuntimeError("initialize"))
    with pytest.raises(RuntimeError, match="initialize"):
        await client.start_server()
    process.terminate.assert_called_once()
    process.wait.assert_awaited_once()
    assert client.process is None
