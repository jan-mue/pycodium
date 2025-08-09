
"""Menu system for PyCodium IDE using Pywebview."""

import asyncio
import threading
from pathlib import Path
from typing import Any, Coroutine

import webview
import webview.menu as wm


def _run_async(coro: Coroutine[Any, Any, Any]) -> None:
    """Run an async coroutine in a thread-safe way."""
    try:
        # Try to get the current event loop
        loop = asyncio.get_running_loop()
        # We're in an async context, create task directly
        loop.create_task(coro)
    except RuntimeError:
        # No event loop in current thread, use thread-safe method
        try:
            # Try to get the main thread's event loop
            main_loop = asyncio.get_event_loop_policy().get_event_loop()
            if main_loop.is_running():
                # Schedule on the main event loop
                asyncio.run_coroutine_threadsafe(coro, main_loop)
            else:
                # Main loop not running, run in new thread with new loop
                def run_in_thread() -> None:
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        new_loop.run_until_complete(coro)
                    finally:
                        new_loop.close()

                threading.Thread(target=run_in_thread, daemon=True).start()
        except RuntimeError:
            # No event loop available, run in new thread
            def run_in_thread() -> None:
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    new_loop.run_until_complete(coro)
                finally:
                    new_loop.close()

            threading.Thread(target=run_in_thread, daemon=True).start()


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
            _run_async(_open_files_async(file_paths))


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
            _run_async(_open_folder_async(folder_path))


def save_file_dialog():
    """Open a save file dialog to save the current file."""
    active_window = webview.active_window()
    if active_window:
        _run_async(_save_current_file_async())


def save_as_dialog():
    """Open a save as dialog to save the current file with a new name."""
    active_window = webview.active_window()
    if active_window:
        result = active_window.create_file_dialog(
            webview.SAVE_DIALOG,
            directory='/',
            save_filename='untitled.py'
        )
        if result and isinstance(result, str):
            file_path = str(Path(result))
            _run_async(_save_file_as_async(file_path))
        elif result and isinstance(result, (list, tuple)) and len(result) > 0:
            file_path = str(Path(result[0]))
            _run_async(_save_file_as_async(file_path))


def new_file():
    """Create a new empty file."""
    _run_async(_new_file_async())


def exit_application():
    """Exit the application."""
    active_window = webview.active_window()
    if active_window:
        active_window.destroy()


async def _open_files_async(file_paths: list[str]) -> None:
    """Async helper to open multiple files."""
    try:
        import reflex as rx
        from pycodium.state import EditorState
        
        # Get the current state instance from Reflex
        state = await EditorState.get_state()
        for file_path in file_paths:
            await state.open_file(file_path)
    except Exception as e:
        print(f"Error opening files: {e}")


async def _open_folder_async(folder_path: str) -> None:
    """Async helper to open a folder."""
    try:
        from pathlib import Path
        import reflex as rx
        from pycodium.state import EditorState
        
        # Get the current state instance from Reflex
        state = await EditorState.get_state()
        state.project_root = Path(folder_path)
        await state._open_project_async()
    except Exception as e:
        print(f"Error opening folder: {e}")


async def _save_current_file_async() -> None:
    """Async helper to save the current file."""
    try:
        import reflex as rx
        from pycodium.state import EditorState
        
        # Get the current state instance from Reflex
        state = await EditorState.get_state()
        await state.controller.save_current_file()
    except Exception as e:
        print(f"Error saving file: {e}")


async def _save_file_as_async(file_path: str) -> None:
    """Async helper to save file with new name."""
    try:
        import reflex as rx
        from pycodium.state import EditorState
        
        # Get the current state instance from Reflex
        state = await EditorState.get_state()
        await state.controller.save_file_as(file_path)
    except Exception as e:
        print(f"Error saving file as: {e}")


async def _new_file_async() -> None:
    """Async helper to create a new file."""
    try:
        import reflex as rx
        from pycodium.state import EditorState
        
        # Get the current state instance from Reflex
        state = await EditorState.get_state()
        await state.controller.new_file()
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
