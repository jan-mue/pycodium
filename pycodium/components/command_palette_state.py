"""Command Palette state management for PyCodium IDE.

Manages the command palette state including:
- Opening/closing the palette
- Search filtering
- Keyboard navigation
- Command execution
- Python interpreter discovery and selection
"""

from __future__ import annotations

import asyncio
import logging
import subprocess
from pathlib import Path

import reflex as rx

from pycodium.components.command_palette import COMMANDS

logger = logging.getLogger(__name__)


# Command handlers are defined as a mapping to simplify the select_command method
# Keys are command IDs, values are tuples of (requires_close, handler_type, handler_data)


class CommandPaletteState(rx.State):
    """State for the command palette."""

    # Command palette visibility
    is_open: bool = False

    # Search and filtering
    search_query: str = ""
    filtered_command_ids: list[str] = [cmd.id for cmd in COMMANDS]

    # Navigation
    selected_index: int = 0

    # Palette mode (commands or interpreters)
    mode: str = "commands"

    # Python interpreters
    python_interpreters: list[dict[str, str]] = []
    current_interpreter: str = ""
    _interpreters_loaded: bool = False

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
        if not self._interpreters_loaded:
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
    async def handle_key_down(self, key: str, _key_info: rx.event.KeyInputInfo) -> None:
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
                len(self.filtered_command_ids) - 1 if self.mode == "commands" else len(self.python_interpreters) - 1
            )
            if self.selected_index < max_index:
                self.selected_index += 1
            return

        if key == "ArrowUp":
            if self.selected_index > 0:
                self.selected_index -= 1
            return

        if key == "Enter":
            await self._execute_selected()

    async def _execute_selected(self) -> None:
        """Execute the currently selected item."""
        if self.mode == "commands" and 0 <= self.selected_index < len(self.filtered_command_ids):
            cmd_id = self.filtered_command_ids[self.selected_index]
            await self.select_command(cmd_id)
        elif self.mode == "interpreters" and 0 <= self.selected_index < len(self.python_interpreters):
            interp = self.python_interpreters[self.selected_index]
            await self.select_interpreter(interp["path"])

    @rx.event
    async def select_command(self, command_id: str) -> rx.event.EventSpec | None:
        """Execute a command by its ID."""
        logger.info(f"Executing command: {command_id}")

        # Handle interpreter selection mode switch
        if command_id == "select-python":
            return await self._handle_select_python()

        # Close palette and execute command
        await self.close_command_palette()
        return self._get_command_action(command_id)

    async def _handle_select_python(self) -> None:
        """Switch to Python interpreter selection mode."""
        self.mode = "interpreters"
        self.search_query = ""
        self.selected_index = 0
        if not self._interpreters_loaded:
            await self._discover_python_interpreters()

    def _get_command_action(self, command_id: str) -> rx.event.EventSpec | None:
        """Get the action for a command ID."""
        # Lazy import to avoid circular imports
        from pycodium.state import EditorState  # noqa: PLC0415

        # Map command IDs to their actions
        state_actions = {
            "toggle-sidebar": EditorState.toggle_sidebar,
            "open-settings": EditorState.open_settings,
            "save": EditorState.menu_save,
            "close-tab": EditorState.menu_close_tab,
        }

        if command_id in state_actions:
            return state_actions[command_id]

        # Script-based commands
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

        # Feature placeholders
        placeholder_messages = {
            "new-file": "New File: Feature coming soon",
            "new-folder": "New Folder: Feature coming soon",
            "go-to-file": "Go to File: Feature coming soon",
        }

        if command_id in placeholder_messages:
            return rx.toast.info(placeholder_messages[command_id])

        return None

    @rx.event
    async def select_interpreter(self, interpreter_path: str) -> rx.event.EventSpec | None:
        """Select a Python interpreter and restart the LSP server."""
        logger.info(f"Selecting Python interpreter: {interpreter_path}")
        self.current_interpreter = interpreter_path

        try:
            await self._restart_lsp_with_interpreter(interpreter_path)
            await self.close_command_palette()
            return rx.toast.success(f"Python interpreter set to: {interpreter_path}")
        except Exception as e:  # noqa: BLE001
            logger.error(f"Failed to set Python interpreter: {e}")
            return rx.toast.error(f"Failed to set interpreter: {e}")

    async def _restart_lsp_with_interpreter(self, interpreter_path: str) -> None:
        """Restart the LSP server with the specified Python interpreter."""
        from pycodium.utils import lsp_client as lsp_module  # noqa: PLC0415
        from pycodium.utils.lsp_client import BasedPyrightLSPClient  # noqa: PLC0415

        # Stop existing client
        if lsp_module.lsp_client is not None:
            await lsp_module.lsp_client.stop_server()
            lsp_module.lsp_client = None

        # Find basedpyright-langserver in the interpreter's environment
        interpreter_dir = Path(interpreter_path).parent
        langserver_path = interpreter_dir / "basedpyright-langserver"
        langserver_path_str = str(langserver_path) if langserver_path.exists() else "basedpyright-langserver"

        # Create new client with updated path
        lsp_module.lsp_client = BasedPyrightLSPClient(server_path=langserver_path_str)
        await lsp_module.lsp_client.start_server()
        logger.info(f"LSP server restarted with interpreter: {interpreter_path}")

    async def _discover_python_interpreters(self) -> None:
        """Discover available Python interpreters on the system using pythonfinder.

        Uses the pythonfinder library for fast, cross-platform Python discovery.
        This is much faster than spawning subprocesses for each interpreter.
        """
        logger.debug("Discovering Python interpreters...")

        # Run pythonfinder in a thread pool to avoid blocking the event loop
        interpreters = await asyncio.get_event_loop().run_in_executor(None, self._discover_interpreters_sync)

        self.python_interpreters = interpreters
        self._interpreters_loaded = True

        if not self.current_interpreter and interpreters:
            self.current_interpreter = interpreters[0]["path"]

        logger.info(f"Discovered {len(interpreters)} Python interpreters")

    def _discover_interpreters_sync(self) -> list[dict[str, str]]:
        """Synchronous interpreter discovery using pythonfinder.

        This method is called in a thread pool to avoid blocking.
        """
        interpreters: list[dict[str, str]] = []
        seen_paths: set[str] = set()

        # Discover interpreters using pythonfinder
        self._discover_with_pythonfinder(interpreters, seen_paths)

        # Also check for local venv which pythonfinder might miss
        self._discover_local_venvs(interpreters, seen_paths)

        return interpreters

    def _discover_with_pythonfinder(self, interpreters: list[dict[str, str]], seen_paths: set[str]) -> None:
        """Use pythonfinder to discover Python interpreters."""
        from pythonfinder import Finder  # noqa: PLC0415

        try:
            finder = Finder()
            if not (finder.system_path and finder.system_path.pythons):
                return

            for path_entry in finder.system_path.pythons.values():
                if not (path_entry and path_entry.path):
                    continue

                path_str = str(path_entry.path)
                if path_str in seen_paths:
                    continue
                seen_paths.add(path_str)

                version_str = self._get_version_string(path_entry)
                interpreters.append({"path": path_str, "version": version_str})

        except Exception as e:  # noqa: BLE001
            logger.warning(f"Error discovering interpreters with pythonfinder: {e}")

    def _get_version_string(self, path_entry: object) -> str:
        """Get version string from a pythonfinder path entry."""
        version_str = "Python"
        if hasattr(path_entry, "py_version") and path_entry.py_version:
            pv = path_entry.py_version
            version_str = f"Python {pv.major}.{pv.minor}.{pv.patch}"

            # Add environment type indicator
            if hasattr(path_entry, "name") and path_entry.name:
                name = path_entry.name
                if "conda" in name.lower():
                    version_str += " (conda)"
                elif "pyenv" in str(path_entry.path).lower():
                    version_str += " (pyenv)"

        return version_str

    def _discover_local_venvs(self, interpreters: list[dict[str, str]], seen_paths: set[str]) -> None:
        """Discover local virtual environments that pythonfinder might miss."""
        cwd = Path.cwd()
        for venv_name in (".venv", "venv", ".env", "env"):
            venv_dir = cwd / venv_name
            python_path = venv_dir / "bin" / "python"
            if not python_path.exists():
                continue

            path_str = str(python_path)
            if path_str in seen_paths:
                continue

            seen_paths.add(path_str)
            version_str = self._get_venv_version(path_str)
            interpreters.insert(0, {"path": path_str, "version": version_str})

    def _get_venv_version(self, path_str: str) -> str:
        """Get version string for a venv Python interpreter."""
        try:
            result = subprocess.run(  # noqa: S603
                [path_str, "--version"],
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )
            version_str = result.stdout.strip() or "Python (venv)"
            if "venv" not in version_str.lower():
                version_str += " (venv)"
            return version_str
        except Exception:  # noqa: BLE001
            return "Python (venv)"

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

        # Extract Python version from the executable name
        python_version = self._extract_python_version(parts)

        # Detect package manager and venv name from path
        package_manager, venv_name = self._detect_venv_info(path, parts)

        # Build the display string
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

        # Not a virtual environment path
        if ".venv" not in path and "venv" not in path and "envs" not in path:
            return package_manager, venv_name

        # Find the venv directory name
        for i, part in enumerate(parts):
            if part in (".venv", "venv"):
                venv_name = part
                break
            if part == "envs" and i + 1 < len(parts):
                venv_name = parts[i + 1]
                break

        # Detect package manager using a dictionary approach
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

        # Default to venv if we detected a venv but no specific package manager
        if not package_manager and venv_name:
            package_manager = "venv"

        return package_manager, venv_name
