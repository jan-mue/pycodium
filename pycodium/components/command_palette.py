"""Command Palette component for PyCodium IDE.

Provides a command palette for quick access to IDE actions
including file operations, editor commands, and Python interpreter selection.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import reflex as rx

from pycodium.components.hotkey_watcher import GlobalHotkeyWatcher

if TYPE_CHECKING:
    from collections.abc import Callable


@dataclass
class CommandItem:
    """Represents a command in the command palette."""

    id: str
    label: str
    category: str
    shortcut: str = ""
    icon: str = ""


# Define available commands
COMMANDS: list[CommandItem] = [
    CommandItem(id="new-file", label="File: New File...", category="file", shortcut="", icon="file-plus"),
    CommandItem(id="new-folder", label="File: New Folder...", category="file", shortcut="", icon="folder-plus"),
    CommandItem(id="open-file", label="File: Open File...", category="file", shortcut="⌘O", icon="file"),
    CommandItem(id="open-folder", label="File: Open Folder...", category="file", shortcut="⌘K ⌘O", icon="folder-open"),
    CommandItem(id="save", label="File: Save", category="file", shortcut="⌘S", icon="save"),
    CommandItem(id="close-tab", label="View: Close Editor", category="view", shortcut="⌘W", icon="x"),
    CommandItem(id="toggle-sidebar", label="View: Toggle Sidebar", category="view", shortcut="⌘B", icon="panel-left"),
    CommandItem(
        id="select-python", label="Python: Select Interpreter", category="python", shortcut="", icon="terminal"
    ),
    CommandItem(
        id="open-settings", label="Preferences: Open Settings", category="preferences", shortcut="⌘,", icon="settings"
    ),
    CommandItem(id="go-to-line", label="Go to Line...", category="navigation", shortcut="⌘G", icon="move-vertical"),
    CommandItem(id="go-to-file", label="Go to File...", category="navigation", shortcut="⌘P", icon="search"),
]


def command_palette_item(
    command: CommandItem,
    on_select: Callable[[], rx.event.EventSpec],
    is_selected: rx.Var[bool],
) -> rx.Component:
    """Render a single command palette item."""
    return rx.el.div(
        rx.el.div(
            rx.icon(command.icon, size=16) if command.icon else rx.fragment(),
            rx.el.span(command.label, class_name="ml-2"),
            class_name="flex items-center",
        ),
        rx.el.span(command.shortcut, class_name="text-xs text-muted-foreground") if command.shortcut else rx.fragment(),
        class_name=rx.cond(
            is_selected,
            "command-palette-item bg-pycodium-highlight",
            "command-palette-item",
        ),
        on_click=on_select,
        id=f"command-{command.id}",
    )


def command_palette_overlay(
    is_open: rx.Var[bool],
    on_close: rx.event.EventSpec,
) -> rx.Component:
    """Render the command palette overlay (backdrop)."""
    return rx.cond(
        is_open,
        rx.el.div(
            class_name="fixed inset-0 bg-black/50 z-40",
            on_click=on_close,
            id="command-palette-overlay",
        ),
        rx.fragment(),
    )


def command_palette_input(
    search_query: rx.Var[str],
    on_change: Callable[[str], rx.event.EventSpec],
    placeholder: rx.Var[str] | str = "Type a command or search...",
) -> rx.Component:
    """Render the command palette search input."""
    return rx.input(
        type="text",
        placeholder=placeholder,
        value=search_query,
        on_change=on_change,
        class_name="w-full px-4 py-3 bg-transparent border-b border-border text-pycodium-text focus:outline-none box-border min-h-[48px]",
        auto_focus=True,
        id="command-palette-input",
    )


def command_palette_list(
    filtered_ids: rx.Var[list[str]],
    selected_index: rx.Var[int],
    on_select: Callable[[str], rx.event.EventSpec],
) -> rx.Component:
    """Render the list of filtered commands."""
    return rx.el.div(
        rx.foreach(
            filtered_ids,
            lambda cmd_id, idx: rx.cond(
                # Find the command by ID and render it
                rx.Var.create(True),  # Always render
                command_palette_item_by_id(cmd_id, idx, selected_index, on_select),
                rx.fragment(),
            ),
        ),
        class_name="max-h-[300px] overflow-y-auto py-1",
        id="command-palette-list",
    )


def command_palette_item_by_id(
    cmd_id: rx.Var[str],
    idx: rx.Var[int],
    selected_index: rx.Var[int],
    on_select: Callable[[str], rx.event.EventSpec],
) -> rx.Component:
    """Render a command item by its ID."""

    # We create specific on_click handlers for each command to avoid lambda capture issues
    def make_cmd_item(cmd: CommandItem) -> tuple[str, rx.Component]:
        return (
            cmd.id,
            rx.el.div(
                rx.el.div(
                    rx.icon(cmd.icon, size=16) if cmd.icon else rx.fragment(),
                    rx.el.span(cmd.label, class_name="ml-2"),
                    class_name="flex items-center",
                ),
                rx.el.span(cmd.shortcut, class_name="text-xs text-muted-foreground") if cmd.shortcut else rx.fragment(),
                class_name=rx.cond(
                    selected_index == idx,
                    "command-palette-item bg-pycodium-highlight",
                    "command-palette-item",
                ),
                on_click=on_select(cmd.id),
                id=f"command-{cmd.id}",
            ),
        )

    return rx.match(
        cmd_id,
        *[make_cmd_item(cmd) for cmd in COMMANDS],
        rx.fragment(),  # Default case
    )


def python_interpreter_item(
    path: rx.Var[str],
    version: rx.Var[str],
    is_selected: rx.Var[bool],
    on_select: Callable[[str], rx.event.EventSpec],
) -> rx.Component:
    """Render a Python interpreter selection item."""
    return rx.el.div(
        rx.el.div(
            rx.icon("terminal", size=16),
            rx.el.div(
                rx.el.span(version, class_name="font-medium"),
                rx.el.span(path, class_name="text-xs text-muted-foreground ml-2"),
                class_name="ml-2",
            ),
            class_name="flex items-center",
        ),
        rx.cond(
            is_selected,
            rx.icon("check", size=16, class_name="text-green-500"),
            rx.fragment(),
        ),
        class_name=rx.cond(
            is_selected,
            "command-palette-item bg-pycodium-highlight",
            "command-palette-item",
        ),
        on_click=lambda: on_select(path),
        id=f"interpreter-{path}",
    )


def command_palette(
    is_open: rx.Var[bool],
    search_query: rx.Var[str],
    filtered_command_ids: rx.Var[list[str]],
    selected_index: rx.Var[int],
    mode: rx.Var[str],  # "commands" or "interpreters"
    python_interpreters: rx.Var[list[dict]],
    current_interpreter: rx.Var[str],
    on_close: rx.event.EventSpec,
    on_search_change: Callable[[str], rx.event.EventSpec],
    on_key_down: Callable[[str, rx.event.KeyInputInfo], rx.event.EventSpec],
    on_select_command: Callable[[str], rx.event.EventSpec],
    on_select_interpreter: Callable[[str], rx.event.EventSpec],
) -> rx.Component:
    """Main command palette component."""
    return rx.fragment(
        command_palette_overlay(is_open, on_close),
        rx.cond(
            is_open,
            rx.fragment(
                # Use GlobalHotkeyWatcher for keyboard navigation when palette is open
                GlobalHotkeyWatcher.create(on_key_down=on_key_down),
                rx.el.div(
                    rx.el.div(
                        command_palette_input(
                            search_query,
                            on_search_change,
                            placeholder=rx.cond(
                                mode == "interpreters",
                                "Select Python Interpreter",
                                "Type a command or search...",
                            ),
                        ),
                        rx.cond(
                            mode == "interpreters",
                            # Python interpreter selection mode
                            rx.el.div(
                                rx.foreach(
                                    python_interpreters,
                                    lambda interp, idx: rx.el.div(
                                        rx.el.div(
                                            rx.icon("terminal", size=16),
                                            rx.el.div(
                                                rx.el.span(interp["version"], class_name="font-medium"),
                                                rx.el.span(
                                                    interp["path"], class_name="text-xs text-muted-foreground ml-2"
                                                ),
                                                class_name="ml-2 flex flex-col",
                                            ),
                                            class_name="flex items-center",
                                        ),
                                        rx.cond(
                                            current_interpreter == interp["path"],
                                            rx.icon("check", size=16, class_name="text-green-500"),
                                            rx.fragment(),
                                        ),
                                        class_name=rx.cond(
                                            selected_index == idx,
                                            "command-palette-item bg-pycodium-highlight",
                                            "command-palette-item",
                                        ),
                                        on_click=on_select_interpreter(interp["path"]),
                                    ),
                                ),
                                class_name="max-h-[300px] overflow-y-auto py-1",
                                id="interpreter-list",
                            ),
                            # Commands mode
                            command_palette_list(
                                filtered_command_ids,
                                selected_index,
                                on_select_command,
                            ),
                        ),
                        rx.cond(
                            (mode == "commands") & (filtered_command_ids.length() == 0),
                            rx.el.div(
                                "No commands found",
                                class_name="px-4 py-3 text-sm text-muted-foreground text-center",
                            ),
                            rx.fragment(),
                        ),
                        class_name="command-palette w-[600px] max-w-[90vw] rounded-md overflow-hidden pointer-events-auto",
                    ),
                    class_name="fixed inset-0 flex items-start justify-center pt-[15vh] z-50 pointer-events-none",
                    id="command-palette-container",
                ),
            ),
            rx.fragment(),
        ),
    )
