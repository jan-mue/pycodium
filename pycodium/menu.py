"""Menu configuration for the PyCodium IDE."""

import json
import logging

from pytauri import AppHandle
from pytauri.menu import Menu, MenuEvent, MenuItem, PredefinedMenuItem, Submenu
from pytauri.webview import WebviewWindow

__all__ = ["init_menu"]

logger = logging.getLogger(__name__)

# Menu item IDs
MENU_OPEN_FILE = "open_file"
MENU_OPEN_FOLDER = "open_folder"
MENU_SAVE = "save"
MENU_SAVE_AS = "save_as"
MENU_CLOSE_TAB = "close_tab"


def init_menu(app_handle: AppHandle, webview_window: WebviewWindow) -> None:
    """Initialize the application menu.

    Args:
        app_handle: The Tauri application handle.
        webview_window: The main webview window.
    """
    file_submenu = Submenu.with_items(
        app_handle,
        "File",
        True,
        (
            MenuItem.with_id(app_handle, MENU_OPEN_FILE, "Open File...", True, "CmdOrCtrl+O"),
            MenuItem.with_id(app_handle, MENU_OPEN_FOLDER, "Open Folder...", True, "CmdOrCtrl+Shift+O"),
            PredefinedMenuItem.separator(app_handle),
            MenuItem.with_id(app_handle, MENU_SAVE, "Save", True, "CmdOrCtrl+S"),
            MenuItem.with_id(app_handle, MENU_SAVE_AS, "Save As...", True, "CmdOrCtrl+Shift+S"),
            PredefinedMenuItem.separator(app_handle),
            MenuItem.with_id(app_handle, MENU_CLOSE_TAB, "Close Tab", True, "CmdOrCtrl+W"),
            PredefinedMenuItem.separator(app_handle),
            PredefinedMenuItem.close_window(app_handle, "Close Window"),
        ),
    )
    edit_submenu = Submenu.with_items(
        app_handle,
        "Edit",
        True,
        (
            PredefinedMenuItem.undo(app_handle, "Undo"),
            PredefinedMenuItem.redo(app_handle, "Redo"),
            PredefinedMenuItem.separator(app_handle),
            PredefinedMenuItem.cut(app_handle, "Cut"),
            PredefinedMenuItem.copy(app_handle, "Copy"),
            PredefinedMenuItem.paste(app_handle, "Paste"),
            PredefinedMenuItem.select_all(app_handle, "Select All"),
        ),
    )
    view_submenu = Submenu.with_items(
        app_handle,
        "View",
        True,
        (PredefinedMenuItem.fullscreen(app_handle, "Toggle Full Screen"),),
    )
    window_submenu = Submenu.with_items(
        app_handle,
        "Window",
        True,
        (
            PredefinedMenuItem.minimize(app_handle, "Minimize"),
            PredefinedMenuItem.maximize(app_handle, "Maximize"),
        ),
    )
    menu = Menu.with_items(
        app_handle,
        (
            file_submenu,
            edit_submenu,
            view_submenu,
            window_submenu,
        ),
    )

    # Set the menu on the app (for macOS) and window (for Windows/Linux)
    app_handle.set_menu(menu)
    webview_window.set_menu(menu)

    def on_menu_event(_window: WebviewWindow, menu_event: MenuEvent) -> None:
        """Handle menu events by emitting them to the frontend.

        Args:
            _window: The webview window that received the event.
            menu_event: The menu event ID string.
        """
        logger.debug(f"Menu event received: {menu_event}")

        action_map = {
            MENU_OPEN_FILE: "open_file",
            MENU_OPEN_FOLDER: "open_folder",
            MENU_SAVE: "save",
            MENU_SAVE_AS: "save_as",
            MENU_CLOSE_TAB: "close_tab",
        }

        action = action_map.get(menu_event)
        if action:
            payload = json.dumps({"action": action})
            js_code = f"window.__PYCODIUM_MENU__ && window.__PYCODIUM_MENU__({payload})"
            try:
                webview_window.eval(js_code)
                logger.debug(f"Emitted menu action to frontend: {action}")
            except Exception:
                logger.exception(f"Failed to emit menu action: {action}")

    webview_window.on_menu_event(on_menu_event)
    logger.info("Application menu initialized")
