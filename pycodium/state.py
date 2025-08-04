"""State and event handlers for the IDE."""

import asyncio
import logging
from pathlib import Path

import reflex as rx
from reflex.event import EventCallback, KeyInputInfo, key_event
from reflex.utils import imports
from typing_extensions import Unpack, override

from pycodium.controllers import EditorController
from pycodium.models.files import FilePath
from pycodium.models.tabs import EditorTab

logger = logging.getLogger(__name__)


class EditorState(rx.State):
    """Global state of the IDE."""

    # UI state variables
    sidebar_visible: bool = True
    panel_visible: bool = True
    active_sidebar_tab: str = "explorer"

    # Editor state variables (for direct access in tests)
    tabs: list[EditorTab] = []
    active_tab_id: str | None = None
    active_tab_history: list[str] = []
    expanded_folders: set[str] = set()
    file_tree: FilePath | None = None

    # Editor state - delegated to controller
    _controller: EditorController | None = None

    @property
    def controller(self) -> EditorController:
        """Get the editor controller instance."""
        if self._controller is None:
            self._controller = EditorController(self.project_root)
            # Sync state with controller
            self._controller.tabs = self.tabs
            self._controller.active_tab_id = self.active_tab_id
            self._controller.active_tab_history = self.active_tab_history
            self._controller.expanded_folders = self.expanded_folders
            self._controller.file_tree = self.file_tree
        return self._controller

    # Explorer state
    project_root: Path = Path.cwd()

    @rx.event
    async def toggle_sidebar(self) -> None:
        """Toggle the sidebar visibility."""
        logger.debug(f"Sidebar visibility changed to {not self.sidebar_visible}")
        self.sidebar_visible = not self.sidebar_visible

    @rx.event
    async def set_active_sidebar_tab(self, tab: str) -> None:
        """Set the active sidebar tab."""
        logger.debug(f"Active sidebar tab changed to {tab}")
        self.active_sidebar_tab = tab

    @rx.event
    async def toggle_folder(self, folder_path: str) -> None:
        """Toggle the expanded state of a folder.

        Args:
            folder_path: The path of the folder to toggle.
        """
        await self.controller.toggle_folder(folder_path)
        # Sync state back from controller
        self.expanded_folders = self.controller.expanded_folders

    @rx.event
    async def open_file(self, file_path: str) -> EventCallback[Unpack[tuple[()]]] | None:
        """Open a file in the editor.

        Args:
            file_path: The path to the file to open.
        """
        tab = await self.controller.open_file(file_path)
        if tab:
            # Sync state back from controller
            self.tabs = self.controller.tabs
            self.active_tab_id = self.controller.active_tab_id
            self.active_tab_history = self.controller.active_tab_history
            return EditorState.keep_active_tab_content_updated
        return None

    @rx.event
    async def close_tab(self, tab_id: str) -> None:
        """Close a tab by its ID.

        Args:
            tab_id: The ID of the tab to close.
        """
        await self.controller.close_tab(tab_id)
        # Sync state back from controller
        self.tabs = self.controller.tabs
        self.active_tab_id = self.controller.active_tab_id
        self.active_tab_history = self.controller.active_tab_history

    @rx.event
    async def set_active_tab(self, tab_id: str) -> EventCallback[Unpack[tuple[()]]] | None:
        """Set the active tab by its ID.

        Args:
            tab_id: The ID of the tab to set as active.
        """
        success = await self.controller.set_active_tab(tab_id)
        if success:
            # Sync state back from controller
            self.active_tab_id = self.controller.active_tab_id
            self.active_tab_history = self.controller.active_tab_history
            return EditorState.keep_active_tab_content_updated
        return None

    @rx.event
    async def update_tab_content(self, tab_id: str, content: str) -> None:
        """Update the content of a specific tab.

        Args:
            tab_id: The ID of the tab to update.
            content: The new content for the tab.
        """
        await self.controller.update_tab_content(tab_id, content)
        # Sync state back from controller
        self.tabs = self.controller.tabs

    @rx.event
    def open_project(self) -> None:
        """Open a project in the editor."""
        asyncio.create_task(self._open_project_async())

    async def _open_project_async(self) -> None:
        """Async helper to open a project."""
        await self.controller.open_project(self.project_root)
        # Sync state back from controller
        self.file_tree = self.controller.file_tree
        self.expanded_folders = self.controller.expanded_folders

    # Properties that delegate to controller
    @rx.var
    def active_tab(self) -> EditorTab | None:
        """Get the currently active tab as a computed variable.

        Returns:
            The active `EditorTab` instance, or None if no tab is active.
        """
        return self.controller.active_tab

    @rx.var
    def editor_content(self) -> str:
        """Get the content of the currently active tab.

        Returns:
            The content of the active tab as a string.
        """
        active_tab = self.active_tab
        if not active_tab:
            return ""
        return active_tab.content

    @rx.var
    def current_file(self) -> str | None:
        """Get the path of the currently active tab.

        Returns:
            The path of the active tab as a string.
        """
        active_tab = self.active_tab
        if not active_tab:
            return None
        return active_tab.path

    @rx.event
    async def open_settings(self) -> None:
        """Open the settings tab."""
        logger.debug("Opening settings tab")
        settings_tab = next((tab for tab in self.tabs if tab.id == "settings"), None)
        if not settings_tab:
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
            self.tabs.append(settings_tab)
        await self.set_active_tab(settings_tab.id)

    @rx.event
    async def on_key_down(self, key: str, key_info: KeyInputInfo) -> None:
        """Handle global key down events."""
        logger.debug(f"Key pressed: {key}, Key Info: {key_info}")
        # TODO: make this work in pywebview
        if key_info["meta_key"] and key.lower() == "s":
            await self.controller.save_current_file()
        elif key_info["meta_key"] and key.lower() == "w" and self.active_tab_id:
            await self.close_tab(self.active_tab_id)

    @rx.event(background=True)
    async def keep_active_tab_content_updated(self) -> None:
        """Keep the content of the active tab updated by watching its file for changes."""
        await self.controller.keep_active_tab_content_updated()


class GlobalHotkeyWatcher(rx.Fragment):
    """A component that listens for key events globally.

    Copied from https://reflex.dev/docs/api-reference/browser-javascript/#using-react-hooks
    """

    on_key_down: rx.EventHandler[key_event]

    @override
    def add_imports(self) -> imports.ImportDict:
        """Add the imports for the component."""
        return {
            "react": [imports.ImportVar(tag="useEffect")],
        }

    @override
    def add_hooks(self) -> list[str | rx.Var[str]]:
        """Add the hooks for the component."""
        return [
            """
            useEffect(() => {
                const handle_key = %s;
                document.addEventListener("keydown", handle_key, false);
                return () => {
                    document.removeEventListener("keydown", handle_key, false);
                }
            })
            """  # noqa: UP031
            % str(rx.Var.create(self.event_triggers["on_key_down"]))
        ]
