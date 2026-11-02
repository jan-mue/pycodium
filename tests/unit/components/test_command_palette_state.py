"""Regression tests for keyboard command dispatch and interpreter filtering."""

from __future__ import annotations

from typing import TYPE_CHECKING, get_type_hints

import pytest
import reflex as rx

from pycodium.components.command_palette_state import CommandPaletteState
from pycodium.state import EditorState
from pycodium.utils import lsp_client as lsp_module

if TYPE_CHECKING:
    from pathlib import Path

    from pytest_mock import MockerFixture


async def test_enter_returns_command_event() -> None:
    state = CommandPaletteState()
    await state.open_command_palette()
    await state.update_search("Toggle Sidebar")
    action = await state.handle_key_down(
        "Enter", rx.event.KeyInputInfo(alt_key=False, ctrl_key=False, meta_key=False, shift_key=False)
    )
    assert action == EditorState.toggle_sidebar
    assert not state.is_open


async def test_enter_selects_filtered_interpreter(mocker: MockerFixture) -> None:
    state = CommandPaletteState()
    state.mode = "interpreters"
    state.is_open = True
    state.python_interpreters = [
        {"path": "/one/python", "version": "Python 3.12"},
        {"path": "/two/python", "version": "Python 3.13"},
    ]
    await state.update_search("3.13")
    restart = mocker.patch.object(CommandPaletteState, "_restart_lsp_with_interpreter", new_callable=mocker.AsyncMock)
    result = await state.handle_key_down(
        "Enter", rx.event.KeyInputInfo(alt_key=False, ctrl_key=False, meta_key=False, shift_key=False)
    )
    restart.assert_awaited_once_with("/two/python")
    assert state.current_interpreter == "/two/python"
    assert result is not None
    assert not state.is_open


async def test_failed_switch_keeps_working_interpreter(mocker: MockerFixture) -> None:
    state = CommandPaletteState()
    state.current_interpreter = "/working/python"
    state.is_open = True
    previous = mocker.Mock()
    previous.stop_server = mocker.AsyncMock()
    mocker.patch.object(lsp_module, "lsp_client", previous)
    candidate = mocker.Mock()
    candidate.start_server = mocker.AsyncMock(side_effect=RuntimeError("initialize failed"))
    mocker.patch.object(lsp_module, "BasedPyrightLSPClient", return_value=candidate)
    result = await state.select_interpreter("/broken/python")
    assert result is not None
    assert state.current_interpreter == "/working/python"
    assert state.is_open
    assert lsp_module.lsp_client is previous
    previous.stop_server.assert_not_awaited()


async def test_switch_starts_candidate_before_stopping_previous(mocker: MockerFixture) -> None:
    state = CommandPaletteState()
    previous = mocker.Mock()
    previous.stop_server = mocker.AsyncMock()
    mocker.patch.object(lsp_module, "lsp_client", previous)
    candidate = mocker.Mock()

    async def start() -> None:
        assert lsp_module.lsp_client is previous
        previous.stop_server.assert_not_awaited()

    candidate.start_server = mocker.AsyncMock(side_effect=start)
    mocker.patch.object(lsp_module, "BasedPyrightLSPClient", return_value=candidate)
    await state.select_interpreter("/new/python")
    assert lsp_module.lsp_client is candidate
    assert state.current_interpreter == "/new/python"
    previous.stop_server.assert_awaited_once()


async def test_failed_previous_cleanup_reaps_candidate(mocker: MockerFixture) -> None:
    state = CommandPaletteState()
    state.current_interpreter = "/working/python"
    previous = mocker.Mock()
    previous.stop_server = mocker.AsyncMock(side_effect=OSError("termination failed"))
    mocker.patch.object(lsp_module, "lsp_client", previous)
    candidate = mocker.Mock()
    candidate.start_server = mocker.AsyncMock()
    candidate.stop_server = mocker.AsyncMock()
    mocker.patch.object(lsp_module, "BasedPyrightLSPClient", return_value=candidate)
    await state.select_interpreter("/new/python")
    candidate.stop_server.assert_awaited_once()
    assert state.current_interpreter == "/working/python"
    assert lsp_module.lsp_client is previous


@pytest.mark.parametrize(
    "handler",
    [CommandPaletteState.handle_key_down, CommandPaletteState.select_command, CommandPaletteState.select_interpreter],
)
def test_event_annotations_resolve_at_runtime(handler: rx.EventHandler) -> None:
    annotations = get_type_hints(handler.fn)
    assert "return" in annotations


async def test_interpreter_discovery_refreshes_for_current_project(mocker: MockerFixture, tmp_path: Path) -> None:
    state = CommandPaletteState()
    editor = mocker.Mock(project_root=tmp_path / "first")
    mocker.patch.object(CommandPaletteState, "get_state", new_callable=mocker.AsyncMock, return_value=editor)
    discover = mocker.patch("pycodium.components.command_palette_state.discover_python_interpreters", return_value=[])
    await state.open_interpreter_palette()
    discover.assert_called_with(tmp_path / "first", "")
    await state.close_command_palette()
    editor.project_root = tmp_path / "second"
    await state.open_interpreter_palette()
    discover.assert_called_with(tmp_path / "second", "")
    await state.close_command_palette()
    await state.open_interpreter_palette()
    assert discover.call_count == 3
