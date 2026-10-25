"""Regression tests for keyboard command dispatch and interpreter filtering."""

from __future__ import annotations

from typing import TYPE_CHECKING

import reflex as rx

from pycodium.components.command_palette_state import CommandPaletteState
from pycodium.state import EditorState

if TYPE_CHECKING:
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
