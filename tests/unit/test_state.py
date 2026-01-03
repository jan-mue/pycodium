from __future__ import annotations

import asyncio
import os
import tempfile
from typing import TYPE_CHECKING

import pytest

from pycodium.models.tabs import EditorTab
from pycodium.state import EditorState

if TYPE_CHECKING:
    from pathlib import Path

    from pytest_mock import MockerFixture
    from reflex.event import KeyInputInfo


@pytest.fixture
def state() -> EditorState:
    return EditorState()


async def test_toggle_sidebar(state: EditorState) -> None:
    initial = state.sidebar_visible
    await state.toggle_sidebar()
    assert state.sidebar_visible is not initial


async def test_set_active_sidebar_tab(state: EditorState) -> None:
    await state.set_active_sidebar_tab("settings")
    assert state.active_sidebar_tab == "settings"


async def test_toggle_folder(state: EditorState) -> None:
    folder = "folder1"
    await state.toggle_folder(folder)
    assert folder in state.expanded_folders
    await state.toggle_folder(folder)
    assert folder not in state.expanded_folders


async def test_close_tab_switches_to_previous(state: EditorState) -> None:
    tab1 = EditorTab(
        id="1", title="t1", language="py", content="", encoding="utf-8", path="f1.py", on_not_active=asyncio.Event()
    )
    tab2 = EditorTab(
        id="2", title="t2", language="py", content="", encoding="utf-8", path="f2.py", on_not_active=asyncio.Event()
    )
    state.tabs = [tab1, tab2]
    state.active_tab_id = "2"
    state.active_tab_history = ["1"]
    await state.close_tab("2")
    assert state.active_tab_id == "1"
    assert all(tab.id != "2" for tab in state.tabs)
    assert tab2.on_not_active.is_set(), "on_not_active should be set for the closed tab"
    assert not tab1.on_not_active.is_set(), "on_not_active should be cleared for the new active tab"


async def test_close_tab_no_previous(state: EditorState) -> None:
    tab1 = EditorTab(
        id="1", title="t1", language="py", content="", encoding="utf-8", path="f1.py", on_not_active=asyncio.Event()
    )
    state.tabs = [tab1]
    state.active_tab_id = "1"
    state.active_tab_history = []
    await state.close_tab("1")
    assert state.active_tab_id is None
    assert not state.tabs
    assert tab1.on_not_active.is_set(), "on_not_active should be set for the closed tab"


def test_active_tab(state: EditorState) -> None:
    tab = EditorTab(
        id="1", title="t", language="py", content="", encoding="utf-8", path="f.py", on_not_active=asyncio.Event()
    )
    state.tabs = [tab]
    state.active_tab_id = "1"
    assert state.active_tab == tab


def test_editor_content_and_current_file(state: EditorState) -> None:
    tab = EditorTab(
        id="1", title="t", language="py", content="abc", encoding="utf-8", path="f.py", on_not_active=asyncio.Event()
    )
    state.tabs = [tab]
    state.active_tab_id = "1"
    assert state.editor_content == "abc"
    assert state.current_file == "f.py"


def test_editor_content_empty(state: EditorState) -> None:
    state.tabs = []
    state.active_tab_id = None
    assert state.editor_content == ""
    assert state.current_file is None


async def test_update_tab_content(state: EditorState) -> None:
    tab = EditorTab(
        id="1", title="t", language="py", content="abc", encoding="utf-8", path="f.py", on_not_active=asyncio.Event()
    )
    state.tabs = [tab]
    state.active_tab_id = "1"
    await state.update_tab_content("1", "def")
    assert tab.content == "def"


def test_open_project(tmp_path: Path, state: EditorState) -> None:
    (tmp_path / "dir").mkdir()
    (tmp_path / "file.txt").write_text("hi")
    state.project_root = tmp_path
    state.open_project()
    assert state.file_tree is not None
    assert tmp_path.name in state.expanded_folders


async def test_open_file_new_and_existing(state: EditorState) -> None:
    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as tmp:
        tmp.write(b'print("hello")')
        tmp_path = tmp.name
    rel_path = os.path.relpath(tmp_path, start=state.project_root.parent)
    # Open new file
    await state.open_file(rel_path)
    assert any(tab.path == rel_path for tab in state.tabs)
    assert state.active_tab_id is not None
    # Open the same file again (should not duplicate tab)
    prev_tab_count = len(state.tabs)
    await state.open_file(rel_path)
    assert len(state.tabs) == prev_tab_count
    os.unlink(tmp_path)


async def test_open_file_binary_error(state: EditorState) -> None:
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"\x00\x01\x02\x03")
        tmp_path = tmp.name
    rel_path = os.path.relpath(tmp_path, start=state.project_root.parent)
    result = await state.open_file(rel_path)
    assert result is not None  # Should return a toast error
    os.unlink(tmp_path)


async def test_set_active_tab_switch_and_noop(state: EditorState) -> None:
    tab1 = EditorTab(
        id="1", title="t1", language="py", content="", encoding="utf-8", path="f1.py", on_not_active=asyncio.Event()
    )
    tab2 = EditorTab(
        id="2", title="t2", language="py", content="", encoding="utf-8", path="f2.py", on_not_active=asyncio.Event()
    )
    state.tabs = [tab1, tab2]
    state.active_tab_id = "1"
    # Switch to another tab
    await state.set_active_tab("2")
    assert state.active_tab_id == "2"
    # Switch to same tab (noop)
    await state.set_active_tab("2")
    assert state.active_tab_id == "2"
    # Switch to non-existent tab
    await state.set_active_tab("nonexistent")
    assert state.active_tab_id == "2"


async def test_on_key_down_save_and_close(state: EditorState, mocker: MockerFixture) -> None:
    tab = EditorTab(
        id="1", title="t1", language="py", content="", encoding="utf-8", path="f1.py", on_not_active=asyncio.Event()
    )
    state.tabs = [tab]
    state.active_tab_id = "1"
    key_info: KeyInputInfo = {"meta_key": True, "alt_key": False, "ctrl_key": False, "shift_key": False}
    save_mock = mocker.patch.object(EditorState, "_save_current_file", new=mocker.AsyncMock())
    await state.on_key_down("s", key_info)
    save_mock.assert_awaited_once()
    # Test close (Cmd+W):
    await state.on_key_down("w", key_info)
    # After closing, active_tab_id should be None and tabs should be empty
    assert state.active_tab_id is None
    assert len(state.tabs) == 0


async def test_menu_open_file_success(state: EditorState, tmp_path: Path) -> None:
    """Test menu_open_file opens a file from absolute path."""
    test_file = tmp_path / "test.py"
    test_file.write_text("print('hello')")

    result = await state.menu_open_file(str(test_file))

    assert any(tab.path == str(test_file) for tab in state.tabs)
    assert state.active_tab_id is not None
    # Returns the background task handler
    assert result is not None


async def test_menu_open_file_not_found(state: EditorState, tmp_path: Path) -> None:
    """Test menu_open_file returns error toast for non-existent file."""
    result = await state.menu_open_file(str(tmp_path / "nonexistent.py"))
    assert result is not None  # Should return a toast error


async def test_menu_open_file_not_a_file(state: EditorState, tmp_path: Path) -> None:
    """Test menu_open_file returns error toast when path is a directory."""
    result = await state.menu_open_file(str(tmp_path))
    assert result is not None  # Should return a toast error


async def test_menu_open_file_binary_error(state: EditorState, tmp_path: Path) -> None:
    """Test menu_open_file returns error toast for binary file."""
    test_file = tmp_path / "binary.bin"
    test_file.write_bytes(b"\x00\x01\x02\x03")

    result = await state.menu_open_file(str(test_file))
    assert result is not None  # Should return a toast error


async def test_menu_open_file_existing_tab(state: EditorState, tmp_path: Path) -> None:
    """Test menu_open_file switches to existing tab if file already open."""
    test_file = tmp_path / "test.py"
    test_file.write_text("print('hello')")

    # Open file first time
    await state.menu_open_file(str(test_file))
    initial_tab_count = len(state.tabs)

    # Open same file again
    await state.menu_open_file(str(test_file))

    assert len(state.tabs) == initial_tab_count


async def test_menu_open_folder_success(state: EditorState, tmp_path: Path) -> None:
    """Test menu_open_folder opens a folder as project root."""
    (tmp_path / "subdir").mkdir()
    (tmp_path / "file.txt").write_text("content")

    await state.menu_open_folder(str(tmp_path))

    assert state.project_root == tmp_path
    assert state.file_tree is not None
    assert tmp_path.name in state.expanded_folders


async def test_menu_open_folder_not_found(state: EditorState, tmp_path: Path) -> None:
    """Test menu_open_folder handles non-existent folder."""
    original_root = state.project_root
    await state.menu_open_folder(str(tmp_path / "nonexistent"))
    # Should not change project root
    assert state.project_root == original_root


async def test_menu_open_folder_not_a_directory(state: EditorState, tmp_path: Path) -> None:
    """Test menu_open_folder handles path that is a file."""
    test_file = tmp_path / "file.txt"
    test_file.write_text("content")
    original_root = state.project_root

    await state.menu_open_folder(str(test_file))
    # Should not change project root
    assert state.project_root == original_root


async def test_menu_save(state: EditorState, tmp_path: Path) -> None:
    """Test menu_save calls _save_current_file."""
    test_file = tmp_path / "test.py"
    test_file.write_text("original")

    tab = EditorTab(
        id="1",
        title="test.py",
        language="py",
        content="saved content",
        encoding="utf-8",
        path=str(test_file),
        on_not_active=asyncio.Event(),
    )
    state.tabs = [tab]
    state.active_tab_id = "1"
    state.project_root = tmp_path / "subdir"

    await state.menu_save()

    assert test_file.read_text() == "saved content"


async def test_menu_save_as(state: EditorState, tmp_path: Path) -> None:
    """Test menu_save_as calls _save_current_file (current implementation)."""
    test_file = tmp_path / "test.py"
    test_file.write_text("original")

    tab = EditorTab(
        id="1",
        title="test.py",
        language="py",
        content="saved as content",
        encoding="utf-8",
        path=str(test_file),
        on_not_active=asyncio.Event(),
    )
    state.tabs = [tab]
    state.active_tab_id = "1"
    state.project_root = tmp_path / "subdir"

    await state.menu_save_as()

    assert test_file.read_text() == "saved as content"


async def test_menu_close_tab(state: EditorState) -> None:
    """Test menu_close_tab closes the active tab."""
    tab = EditorTab(
        id="1", title="t1", language="py", content="", encoding="utf-8", path="f1.py", on_not_active=asyncio.Event()
    )
    state.tabs = [tab]
    state.active_tab_id = "1"

    await state.menu_close_tab()

    assert state.active_tab_id is None
    assert len(state.tabs) == 0


async def test_menu_close_tab_no_active(state: EditorState) -> None:
    """Test menu_close_tab does nothing when no active tab."""
    state.tabs = []
    state.active_tab_id = None

    await state.menu_close_tab()

    assert state.active_tab_id is None


async def test_close_tab_not_active_tab(state: EditorState) -> None:
    """Test closing a tab that is not the active one."""
    tab1 = EditorTab(
        id="1", title="t1", language="py", content="", encoding="utf-8", path="f1.py", on_not_active=asyncio.Event()
    )
    tab2 = EditorTab(
        id="2", title="t2", language="py", content="", encoding="utf-8", path="f2.py", on_not_active=asyncio.Event()
    )
    state.tabs = [tab1, tab2]
    state.active_tab_id = "1"
    state.active_tab_history = []

    # Close tab2 which is not active
    await state.close_tab("2")

    assert state.active_tab_id == "1"  # Active tab unchanged
    assert len(state.tabs) == 1
    assert state.tabs[0].id == "1"


async def test_open_settings(state: EditorState) -> None:
    """Test open_settings creates and opens settings tab."""
    state.tabs = []
    state.active_tab_id = None

    await state.open_settings()

    assert any(tab.id == "settings" for tab in state.tabs)
    assert state.active_tab_id == "settings"
    settings_tab = next(tab for tab in state.tabs if tab.id == "settings")
    assert settings_tab.is_special is True
    assert settings_tab.special_component == "settings"


async def test_open_settings_existing(state: EditorState) -> None:
    """Test open_settings switches to existing settings tab."""
    settings_tab = EditorTab(
        id="settings",
        title="Settings",
        language="json",
        content="{}",
        encoding="utf-8",
        path="settings.json",
        on_not_active=asyncio.Event(),
        is_special=True,
        special_component="settings",
    )
    state.tabs = [settings_tab]
    state.active_tab_id = None

    await state.open_settings()

    assert len(state.tabs) == 1  # No new tab created
    assert state.active_tab_id == "settings"


async def test_open_file_with_active_tab_history(state: EditorState, tmp_path: Path) -> None:
    """Test open_file adds previous tab to history."""
    test_file = tmp_path / "new.py"
    test_file.write_text("print('new')")

    tab1 = EditorTab(
        id="1", title="t1", language="py", content="", encoding="utf-8", path="f1.py", on_not_active=asyncio.Event()
    )
    state.tabs = [tab1]
    state.active_tab_id = "1"
    state.project_root = tmp_path / "subdir"
    state.active_tab_history = []

    rel_path = os.path.relpath(str(test_file), start=str(state.project_root.parent))
    await state.open_file(rel_path)

    assert "1" in state.active_tab_history
    assert tab1.on_not_active.is_set()
