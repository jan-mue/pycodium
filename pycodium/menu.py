
"""Menu system for PyCodium IDE using Pywebview."""

import asyncio
import uuid
from pathlib import Path

import webview
import webview.menu as wm

from pycodium.models.tabs import EditorTab


def open_file_dialog():
    """Open a file dialog to select a file."""
    active_window = webview.active_window()
    if active_window:
        file_types = (
            "Python Files (*.py;*.pyx;*.pyi)|*.py;*.pyx;*.pyi|"
            "Text Files (*.txt)|*.txt|"
            "All Files (*.*)|*.*"
        )
        result = active_window.create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=True,
            file_types=file_types
        )
        if result:
            # Convert to string paths
            file_paths = [str(Path(f)) for f in result]
            # Use async task to open files
            asyncio.create_task(_open_files_async(file_paths))


def open_folder_dialog():
    """Open a folder dialog to select a directory."""
    active_window = webview.active_window()
    if active_window:
        result = active_window.create_file_dialog(
            webview.FOLDER_DIALOG
        )
        if result and len(result) > 0:
            folder_path = str(Path(result[0]))
            # Use async task to open folder
            asyncio.create_task(_open_folder_async(folder_path))


def save_file_dialog():
    """Open a save file dialog to save the current file."""
    active_window = webview.active_window()
    if active_window:
        asyncio.create_task(_save_current_file_async())


def save_as_dialog():
    """Open a save as dialog to save the current file with a new name."""
    active_window = webview.active_window()
    if active_window:
        result = active_window.create_file_dialog(
            webview.SAVE_DIALOG,
            directory='/',
            save_filename='untitled.py'
        )
        if result:
            file_path = str(Path(result))
            asyncio.create_task(_save_file_as_async(file_path))


def new_file():
    """Create a new empty file."""
    asyncio.create_task(_new_file_async())


def exit_application():
    """Exit the application."""
    active_window = webview.active_window()
    if active_window:
        active_window.destroy()


async def _open_files_async(file_paths: list[str]):
    """Async helper to open multiple files."""
    try:
        from pycodium.state import EditorState
        
        state = await EditorState.get_state()
        for file_path in file_paths:
            await state.open_file(file_path)
    except Exception as e:
        print(f"Error opening files: {e}")


async def _open_folder_async(folder_path: str):
    """Async helper to open a folder."""
    try:
        from pycodium.state import EditorState
        
        state = await EditorState.get_state()
        state.project_root = Path(folder_path)
        state.open_project()
    except Exception as e:
        print(f"Error opening folder: {e}")


async def _save_current_file_async():
    """Async helper to save the current file."""
    try:
        from pycodium.state import EditorState
        
        state = await EditorState.get_state()
        await state._save_current_file()
    except Exception as e:
        print(f"Error saving file: {e}")


async def _save_file_as_async(file_path: str):
    """Async helper to save file with new name."""
    try:
        from pycodium.state import EditorState
        
        state = await EditorState.get_state()
        active_tab = state.active_tab
        if active_tab:
            active_tab.path = file_path
            active_tab.title = Path(file_path).name
            await state._save_current_file()
    except Exception as e:
        print(f"Error saving file as: {e}")


async def _new_file_async():
    """Async helper to create a new file."""
    try:
        from pycodium.state import EditorState
        
        state = await EditorState.get_state()
        new_tab = EditorTab(
            id=str(uuid.uuid4()),
            title="untitled.py",
            language="python",
            content="",
            encoding="utf-8",
            path="untitled.py",
            on_not_active=asyncio.Event(),
        )
        state.tabs.append(new_tab)
        state.active_tab_id = new_tab.id
    except Exception as e:
        print(f"Error creating new file: {e}")


def get_menu_items():
    """Get the menu items for the application."""
    return [
        wm.Menu(
            'File',
            [
                wm.MenuAction('New File', new_file),
                wm.MenuSeparator(),
                wm.MenuAction('Open File...', open_file_dialog),
                wm.MenuAction('Open Folder...', open_folder_dialog),
                wm.MenuSeparator(),
                wm.MenuAction('Save', save_file_dialog),
                wm.MenuAction('Save As...', save_as_dialog),
                wm.MenuSeparator(),
                wm.MenuAction('Exit', exit_application),
            ],
        ),
        wm.Menu(
            'Edit',
            [
                wm.MenuAction('Undo', lambda: print("Undo not implemented")),
                wm.MenuAction('Redo', lambda: print("Redo not implemented")),
                wm.MenuSeparator(),
                wm.MenuAction('Cut', lambda: print("Cut not implemented")),
                wm.MenuAction('Copy', lambda: print("Copy not implemented")),
                wm.MenuAction('Paste', lambda: print("Paste not implemented")),
            ],
        ),
    ]
