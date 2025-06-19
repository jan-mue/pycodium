import asyncio
from pathlib import Path

import pytest

from pycodium.models.tabs import EditorTab
from pycodium.state import EditorState


@pytest.fixture
def state() -> EditorState:
    return EditorState()


@pytest.mark.asyncio
async def test_toggle_sidebar(state: EditorState) -> None:
    initial = state.sidebar_visible
    await state.toggle_sidebar()
    assert state.sidebar_visible is not initial


@pytest.mark.asyncio
async def test_set_active_sidebar_tab(state: EditorState) -> None:
    await state.set_active_sidebar_tab("settings")
    assert state.active_sidebar_tab == "settings"


@pytest.mark.asyncio
async def test_toggle_folder(state: EditorState) -> None:
    folder = "folder1"
    await state.toggle_folder(folder)
    assert folder in state.expanded_folders
    await state.toggle_folder(folder)
    assert folder not in state.expanded_folders


@pytest.mark.asyncio
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


@pytest.mark.asyncio
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


@pytest.mark.asyncio
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
