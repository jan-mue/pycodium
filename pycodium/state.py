"""State and event handlers for the IDE."""

from __future__ import annotations

import asyncio
import logging
import os
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import uuid4

import aiofiles
import reflex as rx
from typing_extensions import Unpack
from watchfiles import Change, awatch

from pycodium.constants import INITIAL_PATH_ENV_VAR
from pycodium.models.files import FilePath
from pycodium.models.monaco import (
    CompletionItem,
    CompletionRequest,
    DeclarationRequest,
    HoverRequest,
    PrepareRenameRequest,
    ReferenceRequest,
    RenameRequest,
    SignatureHelpRequest,
)
from pycodium.models.tabs import EditorTab
from pycodium.utils.detect_encoding import decode
from pycodium.utils.detect_lang import detect_programming_language
from pycodium.utils.lsp_client import get_lsp_client

if TYPE_CHECKING:
    from reflex.event import EventCallback, EventSpec, KeyInputInfo

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class EditorState(rx.State):
    """Global state of the IDE."""

    # UI state variables
    sidebar_visible: bool = True
    panel_visible: bool = True
    active_sidebar_tab: str = "explorer"

    # Editor state
    tabs: list[EditorTab] = []
    active_tab_id: str | None = None
    active_tab_history: list[str] = []
    completion_response: dict[str, list[CompletionItem]] = {}
    hover_info: dict[str, str] = {}
    declaration_response: dict[str, Any] = {}
    signature_help_response: dict[str, Any] = {}
    reference_response: dict[str, Any] = {}
    rename_response: dict[str, Any] = {}
    prepare_rename_response: dict[str, Any] = {}

    # Explorer state
    project_root: Path = Path.cwd()
    expanded_folders: set[str] = set()
    file_tree: FilePath | None = None

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
        logger.debug(f"Toggling folder {folder_path}")
        if folder_path in self.expanded_folders:
            self.expanded_folders.remove(folder_path)
        else:
            # Lazily load directory contents when first expanded
            self._load_directory_contents(folder_path)
            self.expanded_folders.add(folder_path)

    def _stop_updating_active_tab(self) -> None:
        if not (active_tab := self.active_tab):
            logger.warning("No active tab to stop updating")
            return
        active_tab.on_not_active.set()  # Signal to stop watching the file for changes

    async def _read_and_decode_file(self, path: Path) -> tuple[str, str] | None:
        """Read and decode a file's content.

        Args:
            path: The path to the file to read.

        Returns:
            A tuple of (decoded_content, encoding) if successful, None if the file
            is binary or uses an unsupported encoding.
        """
        async with aiofiles.open(path, "rb") as f:
            file_content = await f.read()

        # PEP3120 suggests using UTF-8 as the default encoding for Python source files
        path_str = str(path)
        default_encoding = "utf-8" if path_str.endswith((".py", ".pyw", ".ipy", ".pyi")) else None
        decoded_content, encoding = decode(file_content, default_encoding=default_encoding)
        if encoding.endswith("-guessed"):
            return None
        logger.debug(f"Detected encoding for {path}: {encoding}")
        return decoded_content, encoding

    async def _create_tab(self, file_path: str, title: str, content: str, encoding: str) -> EditorTab:
        """Create a new editor tab for a file.

        Args:
            file_path: The path to the file (used as tab identifier).
            title: The title to display in the tab.
            content: The decoded file content.
            encoding: The file's encoding.

        Returns:
            The newly created EditorTab.
        """
        tab = EditorTab(
            id=str(uuid4()),
            title=title,
            language=detect_programming_language(file_path).lower(),
            content=content,
            encoding=encoding,
            path=file_path,
            on_not_active=asyncio.Event(),
        )
        self.tabs.append(tab)
        logger.debug(f"Created tab {tab.id} for {file_path}")
        lsp_client = await get_lsp_client()
        uri = f"file://{self.project_root.parent / file_path}"
        await lsp_client.open_document(uri, content, language_id=tab.language)
        return tab

    def _activate_tab(self, tab: EditorTab) -> EventCallback[Unpack[tuple[()]]]:
        """Activate a tab, updating history and stopping the previous tab's file watcher.

        Args:
            tab: The tab to activate.

        Returns:
            The event callback to keep the tab content updated.
        """
        if self.active_tab_id:
            self.active_tab_history.append(self.active_tab_id)
            self._stop_updating_active_tab()
        self.active_tab_id = tab.id
        return EditorState.keep_active_tab_content_updated

    @rx.event
    async def open_file(self, file_path: str) -> EventSpec | EventCallback[Unpack[tuple[()]]] | None:
        """Open a file in the editor.

        Args:
            file_path: The path to the file to open.
        """
        logger.debug(f"Opening file {file_path}")

        tab = next((tab for tab in self.tabs if tab.path == file_path), None)
        if not tab:
            result = await self._read_and_decode_file(self.project_root.parent / file_path)
            if result is None:
                return rx.toast.error("The file is either binary or uses an unsupported text encoding.")
            decoded_content, encoding = result
            tab = await self._create_tab(file_path, title=file_path, content=decoded_content, encoding=encoding)

        return self._activate_tab(tab)

    async def _save_current_file(self) -> None:
        """Save the content of the currently active tab to its file."""
        active_tab = self.active_tab
        if not active_tab:
            logger.warning("No active tab to save")
            return

        logger.debug(f"Saving content of tab {active_tab.id} to {active_tab.path}")
        async with aiofiles.open(self.project_root.parent / active_tab.path, "w", encoding=active_tab.encoding) as f:
            await f.write(active_tab.content)
        logger.debug(f"Content of tab {active_tab.id} saved successfully")

    @rx.event
    async def menu_open_file(self, file_path: str) -> EventSpec | EventCallback[Unpack[tuple[()]]] | None:
        """Open a file from an absolute path (triggered by native file dialog).

        Args:
            file_path: The absolute path to the file to open.
        """
        logger.debug(f"Opening file from menu: {file_path}")
        path = Path(file_path)

        if not path.exists():
            return rx.toast.error(f"File not found: {file_path}")

        if not path.is_file():
            return rx.toast.error(f"Not a file: {file_path}")

        tab = next((tab for tab in self.tabs if tab.path == file_path), None)
        if not tab:
            result = await self._read_and_decode_file(path)
            if result is None:
                return rx.toast.error("The file is either binary or uses an unsupported text encoding.")
            decoded_content, encoding = result
            tab = await self._create_tab(file_path, title=path.name, content=decoded_content, encoding=encoding)

        return self._activate_tab(tab)

    @rx.event
    async def menu_open_folder(self, folder_path: str) -> EventSpec | EventCallback[Unpack[tuple[()]]] | None:
        """Open a folder as the project root (triggered by native folder dialog).

        Args:
            folder_path: The absolute path to the folder to open.
        """
        logger.debug(f"Opening folder from menu: {folder_path}")
        path = Path(folder_path)

        if not path.exists():
            return rx.toast.error(f"Folder not found: {folder_path}")

        if not path.is_dir():
            return rx.toast.error(f"Not a folder: {folder_path}")

        self._set_project_root(path)
        logger.info(f"Project root changed to: {folder_path}")

    @rx.event
    async def menu_save(self) -> None:
        """Save the current file (triggered by menu)."""
        await self._save_current_file()

    @rx.event
    async def menu_save_as(self) -> None:
        """Save the current file with a new name (triggered by menu).

        Note: This currently just saves the file. A proper implementation
        would need to open a save dialog, which requires additional
        JavaScript integration.
        """
        # TODO: Implement save as with native dialog
        await self._save_current_file()

    @rx.event
    async def menu_close_tab(self) -> None:
        """Close the current tab (triggered by menu)."""
        if self.active_tab_id:
            await self.close_tab(self.active_tab_id)

    @rx.event
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

        tab = next((t for t in self.tabs if t.id == tab_id), None)
        if tab:
            lsp_client = await get_lsp_client()
            uri = f"file://{self.project_root.parent / tab.path}"
            await lsp_client.close_document(uri)

    @rx.event
    async def set_active_tab(self, tab_id: str) -> EventCallback[Unpack[tuple[()]]] | None:
        """Set the active tab by its ID.

        Args:
            tab_id: The ID of the tab to set as active.
        """
        tab = next((tab for tab in self.tabs if tab.id == tab_id), None)
        if tab is None:
            logger.warning(f"Tab {tab_id} not found in open tabs")
            return
        if self.active_tab_id == tab_id:
            logger.debug(f"Tab {tab_id} is already active, no change needed")
            return
        logger.debug(f"Setting active tab {tab_id}")
        tab.on_not_active.clear()
        return self._activate_tab(tab)

    @rx.var
    def active_tab(self) -> EditorTab | None:
        """Get the currently active tab as a computed variable.

        Returns:
            The active `EditorTab` instance, or None if no tab is active.
        """
        return next((tab for tab in self.tabs if tab.id == self.active_tab_id), None)

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
    def active_language_display(self) -> str:
        """Get the formatted language name for the status bar.

        Returns:
            A properly capitalized language name.
        """
        active_tab = self.active_tab
        if not active_tab or not active_tab.language:
            return "Plain Text"

        language = active_tab.language.lower()
        language_map = {
            "python": "Python",
            "javascript": "JavaScript",
            "typescript": "TypeScript",
            "html": "HTML",
            "css": "CSS",
            "json": "JSON",
            "yaml": "YAML",
            "markdown": "Markdown",
            "rust": "Rust",
            "go": "Go",
            "java": "Java",
            "c": "C",
            "cpp": "C++",
            "csharp": "C#",
            "ruby": "Ruby",
            "php": "PHP",
            "swift": "Swift",
            "kotlin": "Kotlin",
            "shell": "Shell",
            "bash": "Bash",
            "sql": "SQL",
            "toml": "TOML",
            "xml": "XML",
            "plaintext": "Plain Text",
        }
        return language_map.get(language, language.capitalize())

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
    async def update_tab_content(self, tab_id: str, content: str) -> None:
        """Update the content of a specific tab.

        Args:
            tab_id: The ID of the tab to update.
            content: The new content for the tab.
        """
        logger.debug(f"Updating content of tab {tab_id}")
        for tab in self.tabs:
            if tab.id == tab_id:
                tab.content = content
                break

    def _list_directory(self, path: Path) -> list[FilePath]:
        """List the contents of a directory as FilePath objects.

        Args:
            path: The directory path to list.

        Returns:
            A sorted list of FilePath objects (directories first, then by name).
        """
        sub_paths = [
            FilePath(name=file_path.name, is_dir=file_path.is_dir(), loaded=not file_path.is_dir())
            for file_path in path.iterdir()
        ]
        sub_paths.sort(key=lambda x: (not x.is_dir, x.name.lower()))
        return sub_paths

    def _build_file_tree(self, path: Path) -> FilePath:
        """Build a shallow file tree for a given path (immediate children only).

        Args:
            path: The path to build the tree for.

        Returns:
            FilePath: The file tree with only immediate children loaded.
        """
        return FilePath(name=path.name, loaded=True, sub_paths=self._list_directory(path))

    def _find_node_by_path(self, path: str) -> FilePath | None:
        """Find a node in the file tree by its path.

        Args:
            path: The path to find (e.g., "project/src/utils").

        Returns:
            The FilePath node if found, None otherwise.
        """
        if self.file_tree is None:
            return None

        parts = path.split("/")
        if not parts or parts[0] != self.file_tree.name:
            return None

        current = self.file_tree
        for part in parts[1:]:
            found = None
            for sub_path in current.sub_paths:
                if sub_path.name == part:
                    found = sub_path
                    break
            if found is None:
                return None
            current = found

        return current

    def _load_directory_contents(self, folder_path: str) -> None:
        """Load the contents of a directory lazily.

        Args:
            folder_path: The path to the folder to load (e.g., "project/src").
        """
        node = self._find_node_by_path(folder_path)
        if node is None:
            logger.warning(f"Could not find node for path: {folder_path}")
            return

        if node.loaded:
            return

        parts = folder_path.split("/")
        relative_parts = parts[1:]
        full_path = self.project_root / "/".join(relative_parts) if relative_parts else self.project_root

        if not full_path.exists() or not full_path.is_dir():
            logger.warning(f"Path does not exist or is not a directory: {full_path}")
            return

        node.sub_paths = self._list_directory(full_path)
        node.loaded = True
        # Trigger frontend update
        self.file_tree = self.file_tree

    def _sort_file_tree(self, file_tree: FilePath) -> None:
        """Sort the file tree by name with directories first.

        Args:
            file_tree: The file tree to sort.

        """
        file_tree.sub_paths.sort(key=lambda x: (not x.is_dir, x.name))
        for sub_path in file_tree.sub_paths:
            if sub_path.is_dir:
                self._sort_file_tree(sub_path)

    def _set_project_root(self, path: Path) -> None:
        """Set the project root and rebuild the file tree.

        Args:
            path: The path to set as the project root.
        """
        self.project_root = path
        self.expanded_folders.clear()
        self.file_tree = self._build_file_tree(self.project_root)
        self._sort_file_tree(self.file_tree)
        self.expanded_folders.add(self.project_root.name)

    @rx.event
    def open_project(self) -> EventSpec | EventCallback[Unpack[tuple[()]]] | None:
        """Open a project in the editor."""
        path_str = os.environ.get(INITIAL_PATH_ENV_VAR)
        if path_str is None:
            logger.info("No initial path provided, opening empty IDE")
            self.file_tree = None
            self.expanded_folders.clear()
            return None

        initial_path = Path(path_str)
        is_file = initial_path.is_file()
        project_root = initial_path.parent if is_file else initial_path

        logger.debug(f"Opening project {project_root}")
        start_time = time.perf_counter()
        self._set_project_root(project_root)
        logger.debug(f"File tree built in {time.perf_counter() - start_time:.2f} seconds")

        if is_file:
            file_path = f"{project_root.name}/{initial_path.name}"
            logger.debug(f"Opening initial file {file_path}")
            return EditorState.open_file(file_path)
        return None

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
            await self._save_current_file()
        elif key_info["meta_key"] and key.lower() == "w" and self.active_tab_id:
            await self.close_tab(self.active_tab_id)

    @rx.event(background=True)
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
                    async with aiofiles.open(file_path, encoding=active_tab.encoding) as f, self:
                        active_tab.content = await f.read()

                        # workaround for https://github.com/orgs/reflex-dev/discussions/1644
                        self.tabs = self.tabs
                    logger.debug(f"Updated content of tab {active_tab.id} from file {file_path}")
        logger.debug(f"Stopped watching tab {active_tab.id} for changes from file {file_path}")

    @rx.event
    async def handle_completion_request(self, request: CompletionRequest) -> None:
        """Handle completion requests from the editor using the basedpyright LSP server."""
        text = request.get("text", "")
        position = request.get("position", {})
        line = position.get("line", 0)
        column = position.get("column", 0)
        file_path = request.get("file_path")

        # Fall back to active tab's path if file_path is not provided or is an in-memory URI
        if not file_path or file_path.startswith("inmemory://"):
            active_tab = self.get_active_tab()
            if active_tab and active_tab.path:
                file_path = active_tab.path

        logger.debug(f"Received completion request for file {file_path}, line {line}, column {column}")
        if not file_path:
            # Return empty completions instead of raising an error
            logger.warning("No file path available for completion request, returning empty results")
            self.completion_response = {"items": []}
            return

        lsp_client = await get_lsp_client()
        uri = f"file://{self.project_root.parent / file_path}"
        await lsp_client.open_document(uri, text)
        completions = await lsp_client.get_completions(uri, line, column)

        def lsp_to_monaco(item: dict[str, Any]) -> CompletionItem:
            return CompletionItem(
                label=item.get("label", ""),
                kind=item.get("kind", 1),
                insert_text=item.get("insertText", item.get("label", "")),
                documentation=item.get("documentation", ""),
                detail=item.get("detail", ""),
            )

        completion_items = [lsp_to_monaco(item) for item in completions]
        self.completion_response = {"items": completion_items}
        logger.debug(f"Updated completion response for file {file_path}, line {line}, column {column}")

    @rx.event
    async def handle_hover_request(self, request: HoverRequest) -> None:
        """Handle hover requests from the editor using the basedpyright LSP server."""
        text = request.get("text", "")
        position = request.get("position", {})
        line = position.get("line", 0)
        column = position.get("column", 0)
        file_path = request.get("file_path")

        # Fall back to active tab's path if file_path is not provided or is an in-memory URI
        if not file_path or file_path.startswith("inmemory://"):
            active_tab = self.get_active_tab()
            if active_tab and active_tab.path:
                file_path = active_tab.path

        logger.debug(f"Received hover request for file {file_path}, line {line}, column {column}")
        if not file_path:
            # Return empty hover info instead of raising an error
            logger.warning("No file path available for hover request, returning empty results")
            self.hover_info = {}
            return
        lsp_client = await get_lsp_client()
        uri = f"file://{self.project_root.parent / file_path}"
        await lsp_client.open_document(uri, text)
        hover = await lsp_client.get_hover_info(uri, line, column)

        # TODO: refactor this
        contents = ""
        if hover:
            hover_contents = hover.get("contents")
            if isinstance(hover_contents, dict):
                contents = hover_contents.get("value", str(hover_contents))
            elif isinstance(hover_contents, list):
                # Join all values if list of dicts/strings
                values = []
                for item in hover_contents:
                    if isinstance(item, dict):
                        values.append(item.get("value", str(item)))
                    else:
                        values.append(str(item))
                contents = "\n".join(values)
            elif isinstance(hover_contents, str):
                contents = hover_contents
            else:
                contents = str(hover_contents)
        self.hover_info = {"contents": contents} if contents else {}
        logger.debug(f"Updated hover info for file {file_path}, line {line}, column {column}")

    @rx.event
    async def handle_declaration_request(self, request: DeclarationRequest) -> None:
        """Handle declaration requests from the editor using the basedpyright LSP server."""
        text = request.get("text", "")
        position = request.get("position", {})
        line = position.get("line", 0)
        column = position.get("column", 0)
        file_path = request.get("file_path")

        # Fall back to active tab's path if file_path is not provided or is an in-memory URI
        if not file_path or file_path.startswith("inmemory://"):
            active_tab = self.get_active_tab()
            if active_tab and active_tab.path:
                file_path = active_tab.path

        logger.debug(f"Received declaration request for file {file_path}, line {line}, column {column}")
        if not file_path:
            # Return empty declaration info instead of raising an error
            logger.warning("No file path available for declaration request, returning empty results")
            self.declaration_response = {"items": []}
            return
        lsp_client = await get_lsp_client()
        uri = f"file://{self.project_root.parent / file_path}"
        await lsp_client.open_document(uri, text)
        declaration = await lsp_client.get_declaration(uri, line, column)

        def lsp_to_monaco_location(item: dict[str, Any]) -> dict[str, Any]:
            """Convert LSP location to Monaco location format.

            LSP uses 0-indexed line/character with format:
            { uri, range: { start: { line, character }, end: { line, character } } }

            Monaco uses 1-indexed lineNumber/column with format:
            { uri, range: { startLineNumber, startColumn, endLineNumber, endColumn } }
            """
            lsp_range = item.get("range", {})
            start = lsp_range.get("start", {})
            end = lsp_range.get("end", {})
            return {
                "uri": item.get("uri", uri),
                "range": {
                    "startLineNumber": start.get("line", 0) + 1,
                    "startColumn": start.get("character", 0) + 1,
                    "endLineNumber": end.get("line", 0) + 1,
                    "endColumn": end.get("character", 0) + 1,
                },
            }

        locations = []
        if isinstance(declaration, list):
            locations = [lsp_to_monaco_location(item) for item in declaration if isinstance(item, dict)]
        elif isinstance(declaration, dict):
            locations = [lsp_to_monaco_location(declaration)]
        self.declaration_response = {"items": locations}
        logger.debug(f"Updated declaration response for file {file_path}, line {line}, column {column}")

    @rx.event
    async def handle_signature_help_request(self, request: SignatureHelpRequest) -> None:
        """Handle signature help requests from the editor using the basedpyright LSP server."""
        text = request.get("text", "")
        position = request.get("position", {})
        line = position.get("line", 0)
        column = position.get("column", 0)
        file_path = request.get("file_path")

        if not file_path or file_path.startswith("inmemory://"):
            active_tab = self.get_active_tab()
            if active_tab and active_tab.path:
                file_path = active_tab.path

        logger.debug(f"Received signature help request for file {file_path}, line {line}, column {column}")
        if not file_path:
            self.signature_help_response = {}
            return

        lsp_client = await get_lsp_client()
        uri = f"file://{self.project_root.parent / file_path}"
        await lsp_client.open_document(uri, text)
        signature_help = await lsp_client.get_signature_help(uri, line, column)

        if signature_help:
            # Convert LSP SignatureHelp to Monaco format
            signatures = []
            for sig in signature_help.get("signatures", []):
                monaco_sig = {
                    "label": sig.get("label", ""),
                    "documentation": sig.get("documentation", ""),
                    "parameters": [
                        {"label": p.get("label", ""), "documentation": p.get("documentation", "")}
                        for p in sig.get("parameters", [])
                    ],
                }
                signatures.append(monaco_sig)

            self.signature_help_response = {
                "signatures": signatures,
                "activeSignature": signature_help.get("activeSignature", 0),
                "activeParameter": signature_help.get("activeParameter", 0),
            }
        else:
            self.signature_help_response = {}
        logger.debug(f"Updated signature help for file {file_path}, line {line}, column {column}")

    @rx.event
    async def handle_reference_request(self, request: ReferenceRequest) -> None:
        """Handle reference requests from the editor using the basedpyright LSP server."""
        text = request.get("text", "")
        position = request.get("position", {})
        line = position.get("line", 0)
        column = position.get("column", 0)
        file_path = request.get("file_path")

        if not file_path or file_path.startswith("inmemory://"):
            active_tab = self.get_active_tab()
            if active_tab and active_tab.path:
                file_path = active_tab.path

        logger.debug(f"Received reference request for file {file_path}, line {line}, column {column}")
        if not file_path:
            self.reference_response = {"items": []}
            return

        lsp_client = await get_lsp_client()
        uri = f"file://{self.project_root.parent / file_path}"
        await lsp_client.open_document(uri, text)
        references = await lsp_client.get_references(uri, line, column)

        def lsp_to_monaco_location(item: dict[str, Any]) -> dict[str, Any]:
            """Convert LSP location to Monaco location format."""
            lsp_range = item.get("range", {})
            start = lsp_range.get("start", {})
            end = lsp_range.get("end", {})
            return {
                "uri": item.get("uri", uri),
                "range": {
                    "startLineNumber": start.get("line", 0) + 1,
                    "startColumn": start.get("character", 0) + 1,
                    "endLineNumber": end.get("line", 0) + 1,
                    "endColumn": end.get("character", 0) + 1,
                },
            }

        locations = [lsp_to_monaco_location(ref) for ref in references if isinstance(ref, dict)]
        self.reference_response = {"items": locations}
        logger.debug(f"Updated reference response for file {file_path}, line {line}, column {column}")

    @rx.event
    async def handle_prepare_rename_request(self, request: PrepareRenameRequest) -> None:
        """Handle prepare rename requests from the editor."""
        text = request.get("text", "")
        position = request.get("position", {})
        line = position.get("line", 0)
        column = position.get("column", 0)
        file_path = request.get("file_path")

        if not file_path or file_path.startswith("inmemory://"):
            active_tab = self.get_active_tab()
            if active_tab and active_tab.path:
                file_path = active_tab.path

        logger.debug(f"Received prepare rename request for file {file_path}, line {line}, column {column}")
        if not file_path:
            self.prepare_rename_response = {}
            return

        lsp_client = await get_lsp_client()
        uri = f"file://{self.project_root.parent / file_path}"
        await lsp_client.open_document(uri, text)
        prepare_result = await lsp_client.prepare_rename(uri, line, column)

        if prepare_result:
            # Can be a Range or { range: Range, placeholder: string }
            if "range" in prepare_result:
                self.prepare_rename_response = prepare_result
            else:
                # It's just a range
                self.prepare_rename_response = {"range": prepare_result}
        else:
            self.prepare_rename_response = {}
        logger.debug(f"Updated prepare rename response for file {file_path}, line {line}, column {column}")

    @rx.event
    async def handle_rename_request(self, request: RenameRequest) -> None:
        """Handle rename requests from the editor."""
        text = request.get("text", "")
        position = request.get("position", {})
        line = position.get("line", 0)
        column = position.get("column", 0)
        file_path = request.get("file_path")
        new_name = request.get("new_name", "")

        if not file_path or file_path.startswith("inmemory://"):
            active_tab = self.get_active_tab()
            if active_tab and active_tab.path:
                file_path = active_tab.path

        logger.debug(f"Received rename request for file {file_path}, line {line}, column {column}, new_name={new_name}")
        if not file_path or not new_name:
            self.rename_response = {}
            return

        lsp_client = await get_lsp_client()
        uri = f"file://{self.project_root.parent / file_path}"
        await lsp_client.open_document(uri, text)
        workspace_edit = await lsp_client.rename_symbol(uri, line, column, new_name)

        if workspace_edit:
            # Convert LSP WorkspaceEdit to a format usable by Monaco
            self.rename_response = {"edit": workspace_edit}
        else:
            self.rename_response = {}
        logger.debug(f"Updated rename response for file {file_path}, line {line}, column {column}")
