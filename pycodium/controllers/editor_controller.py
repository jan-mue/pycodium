
"""Editor controller for managing editor operations."""

import asyncio
import logging
import time
from pathlib import Path
from typing import Optional
from uuid import uuid4

import aiofiles
from watchfiles import Change, awatch

from pycodium.models.files import FilePath
from pycodium.models.tabs import EditorTab
from pycodium.utils.detect_encoding import decode
from pycodium.utils.detect_lang import detect_programming_language

logger = logging.getLogger(__name__)


class EditorController:
    """Controller for managing editor operations and state."""

    def __init__(self, project_root: Path):
        """Initialize the editor controller.

        Args:
            project_root: The root path of the project.
        """
        self.project_root = project_root
        self.tabs: list[EditorTab] = []
        self.active_tab_id: Optional[str] = None
        self.active_tab_history: list[str] = []
        self.expanded_folders: set[str] = set()
        self.file_tree: Optional[FilePath] = None

    async def open_file(self, file_path: str) -> Optional[EditorTab]:
        """Open a file in the editor.

        Args:
            file_path: The path to the file to open.

        Returns:
            The opened tab or None if the file couldn't be opened.
        """
        logger.debug(f"Opening file {file_path}")

        tab = next((tab for tab in self.tabs if tab.path == file_path), None)

        # Add to open files if not already open
        if not tab:
            try:
                async with aiofiles.open(self.project_root.parent / file_path, "rb") as f:
                    file_content = await f.read()

                # PEP3120 suggests using UTF-8 as the default encoding for Python source files
                default_encoding = "utf-8" if file_path.endswith((".py", ".pyw", ".ipy", ".pyi")) else None
                decoded_file_content, encoding = decode(file_content, default_encoding=default_encoding)
                if encoding.endswith("-guessed"):
                    logger.error("The file is either binary or uses an unsupported text encoding.")
                    return None
                logger.debug(f"Detected encoding for {file_path}: {encoding}")

                tab = EditorTab(
                    id=str(uuid4()),
                    title=file_path,
                    language=detect_programming_language(file_path).lower(),
                    content=decoded_file_content,
                    encoding=encoding,
                    path=file_path,
                    on_not_active=asyncio.Event(),
                )
                self.tabs.append(tab)
                logger.debug(f"Created tab {tab.id}")
            except Exception as e:
                logger.error(f"Error opening file {file_path}: {e}")
                return None

        if self.active_tab_id:
            self.active_tab_history.append(self.active_tab_id)
            self._stop_updating_active_tab()

        self.active_tab_id = tab.id
        return tab

    async def close_tab(self, tab_id: str) -> None:
        """Close a tab by its ID.

        Args:
            tab_id: The ID of the tab to close.
        """
        logger.debug(f"Closing tab {tab_id}")
        self._stop_updating_active_tab()
        self.tabs = [tab for tab in self.tabs if tab.id != tab_id]
        self.active_tab_history = [tab for tab in self.active_tab_history if tab != tab_id]

        if self.active_tab_id == tab_id and self.active_tab_history:
            previous_tab_id = self.active_tab_history.pop()
            logger.debug(f"Switching to previous tab {previous_tab_id}")
            self.active_tab_id = previous_tab_id
        elif self.active_tab_id != tab_id:
            logger.debug("Active tab is not the one being closed, no switch needed")
        else:
            logger.debug("No previous tab to switch to, setting active tab to None")
            self.active_tab_id = None

    async def set_active_tab(self, tab_id: str) -> bool:
        """Set the active tab by its ID.

        Args:
            tab_id: The ID of the tab to set as active.

        Returns:
            True if the tab was set as active, False otherwise.
        """
        if tab_id not in {tab.id for tab in self.tabs}:
            logger.warning(f"Tab {tab_id} not found in open tabs")
            return False
        if self.active_tab_id == tab_id:
            logger.debug(f"Tab {tab_id} is already active, no change needed")
            return True
        logger.debug(f"Setting active tab {tab_id}")
        if self.active_tab_id is not None:
            self.active_tab_history.append(self.active_tab_id)
            self._stop_updating_active_tab()
        self.active_tab_id = tab_id
        active_tab = self.active_tab
        if active_tab:
            active_tab.on_not_active.clear()
        return True

    async def update_tab_content(self, tab_id: str, content: str) -> bool:
        """Update the content of a specific tab.

        Args:
            tab_id: The ID of the tab to update.
            content: The new content for the tab.

        Returns:
            True if the tab was updated, False otherwise.
        """
        logger.debug(f"Updating content of tab {tab_id}")
        for tab in self.tabs:
            if tab.id == tab_id:
                tab.content = content
                return True
        return False

    async def save_current_file(self) -> bool:
        """Save the content of the currently active tab to its file.

        Returns:
            True if the file was saved, False otherwise.
        """
        active_tab = self.active_tab
        if not active_tab:
            logger.warning("No active tab to save")
            return False

        logger.debug(f"Saving content of tab {active_tab.id} to {active_tab.path}")
        try:
            async with aiofiles.open(self.project_root.parent / active_tab.path, "w", encoding=active_tab.encoding) as f:
                await f.write(active_tab.content)
            logger.debug(f"Content of tab {active_tab.id} saved successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving file {active_tab.path}: {e}")
            return False

    async def save_file_as(self, file_path: str) -> bool:
        """Save the current file with a new name.

        Args:
            file_path: The new file path to save to.

        Returns:
            True if the file was saved, False otherwise.
        """
        active_tab = self.active_tab
        if not active_tab:
            logger.warning("No active tab to save")
            return False

        try:
            active_tab.path = file_path
            active_tab.title = Path(file_path).name
            return await self.save_current_file()
        except Exception as e:
            logger.error(f"Error saving file as {file_path}: {e}")
            return False

    async def new_file(self) -> EditorTab:
        """Create a new empty file.

        Returns:
            The newly created tab.
        """
        new_tab = EditorTab(
            id=str(uuid4()),
            title="untitled.py",
            language="python",
            content="",
            encoding="utf-8",
            path="untitled.py",
            on_not_active=asyncio.Event(),
        )
        self.tabs.append(new_tab)
        self.active_tab_id = new_tab.id
        return new_tab

    async def open_project(self, project_root: Path) -> None:
        """Open a project in the editor.

        Args:
            project_root: The root path of the project to open.
        """
        logger.debug(f"Opening project {project_root}")
        self.project_root = project_root
        start_time = time.perf_counter()
        self.file_tree = self._build_file_tree(project_root)
        self._sort_file_tree(self.file_tree)
        self.expanded_folders.add(project_root.name)
        logger.debug(f"File tree built in {time.perf_counter() - start_time:.2f} seconds")

    async def toggle_folder(self, folder_path: str) -> None:
        """Toggle the expanded state of a folder.

        Args:
            folder_path: The path of the folder to toggle.
        """
        logger.debug(f"Toggling folder {folder_path}")
        if folder_path in self.expanded_folders:
            self.expanded_folders.remove(folder_path)
        else:
            self.expanded_folders.add(folder_path)

    @property
    def active_tab(self) -> Optional[EditorTab]:
        """Get the currently active tab.

        Returns:
            The active EditorTab instance, or None if no tab is active.
        """
        return next((tab for tab in self.tabs if tab.id == self.active_tab_id), None)

    def _stop_updating_active_tab(self) -> None:
        """Stop watching the active tab for file changes."""
        if not (active_tab := self.active_tab):
            logger.warning("No active tab to stop updating")
            return
        active_tab.on_not_active.set()  # Signal to stop watching the file for changes

    def _build_file_tree(self, path: Path) -> FilePath:
        """Build the file tree for a given path.

        Args:
            path: The path to the file to build.

        Returns:
            FilePath: The file tree for the given path.
        """
        file_tree = FilePath(name=path.name)

        for file_path in path.iterdir():
            if file_path.is_dir():
                sub_tree = self._build_file_tree(file_path)
                file_tree.sub_paths.append(sub_tree)
            else:
                file_tree.sub_paths.append(FilePath(name=file_path.name, is_dir=False))

        return file_tree

    def _sort_file_tree(self, file_tree: FilePath) -> None:
        """Sort the file tree by name with directories first.

        Args:
            file_tree: The file tree to sort.
        """
        file_tree.sub_paths.sort(key=lambda x: (not x.is_dir, x.name))
        for sub_path in file_tree.sub_paths:
            if sub_path.is_dir:
                self._sort_file_tree(sub_path)

    async def keep_active_tab_content_updated(self) -> None:
        """Keep the content of the active tab updated by watching its file for changes."""
        active_tab = self.active_tab
        if not active_tab:
            logger.warning("No active tab to watch for changes")
            return
        file_path = self.project_root.parent / active_tab.path
        logger.debug(f"Starting to watch tab {active_tab.id} for changes from file {file_path}")
        async for changes in awatch(file_path, stop_event=active_tab.on_not_active):
            for change in changes:
                if change[0] == Change.modified:
                    try:
                        async with aiofiles.open(file_path, encoding=active_tab.encoding) as f:
                            active_tab.content = await f.read()
                        logger.debug(f"Updated content of tab {active_tab.id} from file {file_path}")
                    except Exception as e:
                        logger.error(f"Error updating content from file {file_path}: {e}")
        logger.debug(f"Stopped watching tab {active_tab.id} for changes from file {file_path}")

