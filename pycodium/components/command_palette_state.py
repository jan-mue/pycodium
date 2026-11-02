"""Command palette state and actions."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import reflex as rx
from typing_extensions import Unpack

from pycodium.components.command_palette import COMMANDS
from pycodium.state import EditorState
from pycodium.utils import lsp_client as lsp_module
from pycodium.utils.python_interpreters import discover_python_interpreters

logger = logging.getLogger(__name__)


class CommandPaletteState(rx.State):
    """State for the command palette."""

    is_open: bool = False
    search_query: str = ""
    filtered_command_ids: list[str] = [cmd.id for cmd in COMMANDS]
    selected_index: int = 0
    mode: str = "commands"
    python_interpreters: list[dict[str, str]] = []
    current_interpreter: str = ""

    @rx.event
    async def open_command_palette(self) -> None:
        """Open the command palette."""
        self.is_open = True
        self.search_query = ""
        self.selected_index = 0
        self.mode = "commands"
        self.filtered_command_ids = [cmd.id for cmd in COMMANDS]
        logger.debug("Command palette opened")

    @rx.event
    async def close_command_palette(self) -> None:
        """Close the command palette."""
        self.is_open = False
        self.search_query = ""
        self.selected_index = 0
        self.mode = "commands"
        logger.debug("Command palette closed")

    @rx.event
    async def toggle_command_palette(self) -> None:
        """Toggle the command palette visibility."""
        if self.is_open:
            await self.close_command_palette()
        else:
            await self.open_command_palette()

    @rx.event
    async def open_interpreter_palette(self) -> None:
        """Open the command palette directly in interpreter selection mode."""
        self.is_open = True
        self.search_query = ""
        self.selected_index = 0
        self.mode = "interpreters"
        await self._discover_python_interpreters()
        logger.debug("Interpreter palette opened")

    @rx.event
    async def update_search(self, query: str) -> None:
        """Update the search query and filter commands."""
        self.search_query = query
        self.selected_index = 0

        if self.mode == "commands":
            query_lower = query.lower()
            self.filtered_command_ids = [
                cmd.id for cmd in COMMANDS if query_lower in cmd.label.lower() or query_lower in cmd.category.lower()
            ]
        logger.debug(f"Search updated: '{query}', filtered: {len(self.filtered_command_ids)} commands")

    @rx.event
    async def handle_key_down(
        self, key: str, _key_info: rx.event.KeyInputInfo
    ) -> rx.event.EventSpec | rx.event.EventCallback[Unpack[tuple[()]]] | None:
        """Handle keyboard navigation in the command palette.

        Args:
            key: The key that was pressed.
            key_info: Additional key event information (modifiers).
        """
        if key == "Escape":
            await self.close_command_palette()
            return

        if key == "ArrowDown":
            max_index = (
                len(self.filtered_command_ids) - 1 if self.mode == "commands" else len(self.filtered_interpreters) - 1
            )
            if self.selected_index < max_index:
                self.selected_index += 1
            return

        if key == "ArrowUp":
            if self.selected_index > 0:
                self.selected_index -= 1
            return

        if key == "Enter":
            return await self._execute_selected()

    async def _execute_selected(self) -> rx.event.EventSpec | rx.event.EventCallback[Unpack[tuple[()]]] | None:
        """Execute the currently selected item."""
        if self.mode == "commands" and 0 <= self.selected_index < len(self.filtered_command_ids):
            cmd_id = self.filtered_command_ids[self.selected_index]
            return await self.select_command(cmd_id)
        elif self.mode == "interpreters" and 0 <= self.selected_index < len(self.filtered_interpreters):
            interp = self.filtered_interpreters[self.selected_index]
            return await self.select_interpreter(interp["path"])

    @rx.event
    async def select_command(
        self, command_id: str
    ) -> rx.event.EventSpec | rx.event.EventCallback[Unpack[tuple[()]]] | None:
        """Execute a command by its ID."""
        logger.info(f"Executing command: {command_id}")

        if command_id == "select-python":
            return await self._handle_select_python()

        await self.close_command_palette()
        return self._get_command_action(command_id)

    async def _handle_select_python(self) -> None:
        """Switch to Python interpreter selection mode."""
        self.mode = "interpreters"
        self.search_query = ""
        self.selected_index = 0
        await self._discover_python_interpreters()

    def _get_command_action(
        self, command_id: str
    ) -> rx.event.EventSpec | rx.event.EventCallback[Unpack[tuple[()]]] | None:
        """Get the action for a command ID."""
        state_actions = {
            "toggle-sidebar": EditorState.toggle_sidebar,
            "open-settings": EditorState.open_settings,
            "save": EditorState.menu_save,
            "close-tab": EditorState.menu_close_tab,
        }

        if command_id in state_actions:
            return state_actions[command_id]

        script_commands = {
            "open-file": "window.__PYCODIUM_MENU__({ action: 'open_file' })",
            "open-folder": "window.__PYCODIUM_MENU__({ action: 'open_folder' })",
            "go-to-line": """
                if (window.monaco && window.monaco.editor) {
                    const editors = window.monaco.editor.getEditors();
                    if (editors.length > 0) {
                        editors[0].trigger('keyboard', 'editor.action.gotoLine', null);
                    }
                }
            """,
        }

        if command_id in script_commands:
            return rx.call_script(script_commands[command_id])

        placeholder_messages = {
            "new-file": "New File: Feature coming soon",
            "new-folder": "New Folder: Feature coming soon",
            "go-to-file": "Go to File: Feature coming soon",
        }

        if command_id in placeholder_messages:
            return rx.toast.info(placeholder_messages[command_id])

        return None

    @rx.event
    async def select_interpreter(
        self, interpreter_path: str
    ) -> rx.event.EventSpec | rx.event.EventCallback[Unpack[tuple[()]]] | None:
        """Select a Python interpreter and restart the LSP server."""
        logger.info(f"Selecting Python interpreter: {interpreter_path}")

        try:
            await self._restart_lsp_with_interpreter(interpreter_path)
            self.current_interpreter = interpreter_path
            await self.close_command_palette()
            return rx.toast.success(f"Python interpreter set to: {interpreter_path}")
        except (OSError, RuntimeError, asyncio.TimeoutError) as e:
            logger.error(f"Failed to set Python interpreter: {e}")
            return rx.toast.error(f"Failed to set interpreter: {e}")

    async def _restart_lsp_with_interpreter(self, interpreter_path: str) -> None:
        """Restart the LSP server with the specified Python interpreter."""
        interpreter_dir = Path(interpreter_path).parent
        langserver_path = interpreter_dir / "basedpyright-langserver"
        langserver_path_str = str(langserver_path) if langserver_path.exists() else "basedpyright-langserver"

        candidate = lsp_module.BasedPyrightLSPClient(server_path=langserver_path_str, python_path=interpreter_path)
        await candidate.start_server()
        previous = lsp_module.lsp_client
        try:
            if previous is not None:
                await previous.stop_server()
        except (OSError, RuntimeError, asyncio.TimeoutError, asyncio.CancelledError):
            await candidate.stop_server()
            raise
        lsp_module.lsp_client = candidate
        logger.info(f"LSP server restarted with interpreter: {interpreter_path}")

    async def _discover_python_interpreters(self) -> None:
        """Refresh interpreters for the project currently open in the editor."""
        editor = await self.get_state(EditorState)
        self.python_interpreters = await asyncio.to_thread(
            discover_python_interpreters, editor.project_root, self.current_interpreter
        )

    @rx.var
    def filtered_interpreters(self) -> list[dict[str, str]]:
        """Get filtered interpreters based on search query."""
        if not self.search_query:
            return self.python_interpreters

        query = self.search_query.lower()
        return [
            interp
            for interp in self.python_interpreters
            if query in interp["path"].lower() or query in interp["version"].lower()
        ]

    @rx.var
    def interpreter_display(self) -> str:
        """Get formatted interpreter display for the status bar.

        Returns:
            Formatted string like 'uv (.venv) (Python 3.12)'.
        """
        if not self.current_interpreter:
            return "Select Interpreter"

        path = self.current_interpreter
        parts = path.split("/")

        python_version = self._extract_python_version(parts)

        package_manager, venv_name = self._detect_venv_info(path, parts)

        display_parts = []

        if package_manager:
            display_parts.append(package_manager)

        if venv_name:
            display_parts.append(f"({venv_name})")

        version_str = f"(Python {python_version})" if python_version else "(Python)"
        display_parts.append(version_str)

        return " ".join(display_parts) if display_parts else "Python"

    def _extract_python_version(self, parts: list[str]) -> str:
        """Extract Python version from path parts."""
        if not parts:
            return ""
        name = parts[-1]
        if name.startswith("python"):
            version = name.replace("python", "")
            return version if version else ""
        return ""

    def _detect_venv_info(self, path: str, parts: list[str]) -> tuple[str, str]:
        """Detect package manager and venv name from path."""
        package_manager = ""
        venv_name = ""

        if ".venv" not in path and "venv" not in path and "envs" not in path:
            return package_manager, venv_name

        for i, part in enumerate(parts):
            if part in (".venv", "venv"):
                venv_name = part
                break
            if part == "envs" and i + 1 < len(parts):
                venv_name = parts[i + 1]
                break

        path_lower = path.lower()
        package_manager_patterns = [
            (".venv", "uv"),
            ("conda", "conda"),
            ("miniconda", "conda"),
            ("mamba", "mamba"),
            ("pyenv", "pyenv"),
            ("poetry", "poetry"),
            ("pipenv", "pipenv"),
        ]

        for pattern, manager in package_manager_patterns:
            if pattern in path_lower:
                package_manager = manager
                break

        if not package_manager and venv_name:
            package_manager = "venv"

        return package_manager, venv_name
