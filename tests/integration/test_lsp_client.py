from __future__ import annotations

from typing import TYPE_CHECKING

import pytest_asyncio

from pycodium.utils.lsp_client import TyLSPClient

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

TEST_URI = "file:///tmp/test_lsp_client_integration.py"
TEST_CONTENT = """
def hello(name: str) -> str:
    return f"Hello, {name}!"

x = hello("world")
reveal_type(x)
"""


@pytest_asyncio.fixture
async def lsp_client() -> AsyncGenerator[TyLSPClient, None]:
    client = TyLSPClient()
    await client.start_server()
    yield client
    await client.stop_server()


async def test_tylspclient_integration(lsp_client: TyLSPClient) -> None:
    await lsp_client.open_document(TEST_URI, TEST_CONTENT)

    completions = await lsp_client.get_completions(TEST_URI, 4, 10)
    assert isinstance(completions, list)
    assert completions, "Completions should not be empty"

    hover = await lsp_client.get_hover_info(TEST_URI, 4, 5)
    assert hover is not None, "Hover info should not be None"

    await lsp_client.close_document(TEST_URI)
