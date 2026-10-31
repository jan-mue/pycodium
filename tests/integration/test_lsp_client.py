from __future__ import annotations

import asyncio
import sys
from typing import TYPE_CHECKING

import pytest_asyncio

from pycodium.utils.lsp_client import BasedPyrightLSPClient

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator
    from pathlib import Path

TEST_URI = "file:///tmp/test_lsp_client_integration.py"
TEST_CONTENT = """
def hello(name: str) -> str:
    return f"Hello, {name}!"

x = hello("world")
reveal_type(x)
"""


@pytest_asyncio.fixture
async def lsp_client() -> AsyncGenerator[BasedPyrightLSPClient, None]:
    client = BasedPyrightLSPClient()
    await client.start_server()
    yield client
    await client.stop_server()


async def test_basedpyright_lsp_client_integration(lsp_client: BasedPyrightLSPClient) -> None:
    await lsp_client.open_document(TEST_URI, TEST_CONTENT)

    completions = await lsp_client.get_completions(TEST_URI, 4, 10)
    assert isinstance(completions, list)
    assert completions, "Completions should not be empty"

    hover = await lsp_client.get_hover_info(TEST_URI, 4, 5)
    assert hover is not None, "Hover info should not be None"

    await lsp_client.close_document(TEST_URI)


async def test_document_changes_refresh_diagnostics(lsp_client: BasedPyrightLSPClient) -> None:
    await lsp_client.open_document(TEST_URI, 'value: int = "wrong"')
    diagnostics = await lsp_client.get_diagnostics(TEST_URI)
    assert any(item.get("severity") == 1 for item in diagnostics)
    await lsp_client.open_document(TEST_URI, "value: int = 1")
    assert await lsp_client.get_diagnostics(TEST_URI) == []
    assert lsp_client.documents[TEST_URI][0] == 2
    await lsp_client.close_document(TEST_URI)


async def test_selected_interpreter_controls_import_resolution(tmp_path: Path) -> None:
    """The pushed pythonPath must expose packages from the selected environment."""
    environment = tmp_path / "selected"
    process = await asyncio.create_subprocess_exec(sys.executable, "-m", "venv", "--without-pip", str(environment))
    assert await process.wait() == 0
    site_packages = environment / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"
    (site_packages / "selected_environment_module.py").write_text("selected_value: int = 42\n")
    client = BasedPyrightLSPClient(python_path=str(environment / "bin/python"))
    await client.start_server()
    try:
        uri = (tmp_path / "main.py").as_uri()
        await client.open_document(
            uri, "import selected_environment_module\nvalue = selected_environment_module.selected_value\n"
        )
        diagnostics = await client.get_diagnostics(uri)
        assert not any(item.get("code") == "reportMissingImports" for item in diagnostics)
        hover = await client.get_hover_info(uri, 1, 43)
        assert hover is not None
        assert "int" in str(hover["contents"])
    finally:
        await client.stop_server()
