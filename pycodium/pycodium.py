"""Welcome to Reflex! This file outlines the steps to create a basic app."""

import logging

import reflex as rx
from reflex.event import EventSpec
from reflex.utils.exec import is_prod_mode

from pycodium.components.activity_bar import activity_bar
from pycodium.components.command_palette import command_palette
from pycodium.components.command_palette_state import CommandPaletteState
from pycodium.components.editor_area import editor_area
from pycodium.components.hotkey_watcher import GlobalHotkeyWatcher
from pycodium.components.menu_events import tauri_menu_handler
from pycodium.components.resizable_panels import group, handle, panel
from pycodium.components.sidebar import sidebar
from pycodium.components.status_bar import status_bar
from pycodium.state import EditorState

logger = logging.getLogger(__name__)


def backend_exception_handler(exception: Exception) -> EventSpec:
    """Handle backend exceptions and show appropriate toast messages.

    Args:
        exception: The exception that occurred.

    Returns:
        An EventSpec with an error toast describing the error.
    """
    if isinstance(exception, PermissionError):
        logger.error("Permission denied: %s", exception)
        return rx.toast.error(f"Permission denied: {exception.filename or 'unknown file'}")

    if isinstance(exception, FileNotFoundError):
        logger.error("File not found: %s", exception)
        return rx.toast.error(f"File not found: {exception.filename or 'unknown file'}")

    if isinstance(exception, IsADirectoryError):
        logger.error("Is a directory: %s", exception)
        return rx.toast.error(f"Cannot open directory as file: {exception.filename or 'unknown'}")

    if isinstance(exception, OSError):
        logger.error("I/O error: %s", exception)
        return rx.toast.error(f"I/O error: {exception.strerror or str(exception)}")

    logger.exception("Unhandled exception: %s", exception)
    if is_prod_mode():
        error_message = "An unexpected error occurred. Please try again."
    else:
        error_message = f"{type(exception).__name__}: {exception}"

    return rx.toast(
        "An error occurred.",
        level="error",
        description=error_message,
        position="top-center",
        id="backend_error",
        style={"width": "500px"},
    )


def index() -> rx.Component:
    """Main page of the PyCodium IDE."""
    return rx.el.div(
        # Command Palette
        command_palette(
            is_open=CommandPaletteState.is_open,
            search_query=CommandPaletteState.search_query,
            filtered_command_ids=CommandPaletteState.filtered_command_ids,
            selected_index=CommandPaletteState.selected_index,
            mode=CommandPaletteState.mode,
            python_interpreters=CommandPaletteState.python_interpreters,
            current_interpreter=CommandPaletteState.current_interpreter,
            on_close=CommandPaletteState.close_command_palette,
            on_search_change=CommandPaletteState.update_search,
            on_key_down=CommandPaletteState.handle_key_down,
            on_select_command=CommandPaletteState.select_command,
            on_select_interpreter=CommandPaletteState.select_interpreter,
        ),
        GlobalHotkeyWatcher.create(
            on_key_down=lambda key, key_info: rx.cond(
                # Cmd+Shift+P to open command palette
                key_info.meta_key & key_info.shift_key & (key == "p"),
                CommandPaletteState.toggle_command_palette.prevent_default,
                rx.cond(
                    key_info.meta_key & rx.Var.create(["s", "w"]).contains(key),
                    EditorState.on_key_down(key, key_info).prevent_default,
                    None,
                ),
            )
        ),
        tauri_menu_handler(
            on_file_selected=EditorState.menu_open_file,
            on_folder_selected=EditorState.menu_open_folder,
            on_save=EditorState.menu_save,
            on_save_as=EditorState.menu_save_as,
            on_close_tab=EditorState.menu_close_tab,
        ),
        rx.el.div(
            activity_bar(),
            group(
                rx.cond(
                    EditorState.sidebar_visible,
                    rx.fragment(
                        panel(
                            sidebar(),
                            default_size=20,
                            min_size=15,
                            max_size=40,
                            class_name="h-full",
                        ),
                        handle(
                            class_name="w-1 hover:bg-pycodium-highlight hover:cursor-col-resize",
                        ),
                    ),
                ),
                panel(
                    rx.el.div(
                        group(
                            panel(
                                editor_area(),
                                class_name="h-full overflow-hidden",
                            ),
                            direction="vertical",
                            class_name="h-full",
                        ),
                        class_name="h-full flex flex-col overflow-hidden",
                    ),
                    class_name="h-full",
                ),
                direction="horizontal",
                class_name="flex-1",
            ),
            class_name="flex-1 flex overflow-hidden",
        ),
        status_bar(),
        class_name="h-screen flex flex-col overflow-hidden",
    )


app = rx.App(
    theme=rx.theme(appearance="dark"),
    stylesheets=["/index.css"],
    backend_exception_handler=backend_exception_handler,
)
app.add_page(index, title="PyCodium", description="A modern Python IDE.", on_load=EditorState.open_project)
