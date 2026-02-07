"""Defines the status bar of the IDE."""

import reflex as rx

from pycodium.components.command_palette_state import CommandPaletteState
from pycodium.state import EditorState


def status_bar() -> rx.Component:
    """Creates the status bar component for the IDE."""
    return rx.el.div(
        # Left side - Git branch and notifications
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    rx.icon("git-branch", size=14),
                    " main *",
                    class_name="flex items-center gap-1",
                ),
                class_name="status-bar-item flex items-center",
            ),
            rx.el.div(
                rx.icon("bell", size=14),
                class_name="status-bar-item",
            ),
            class_name="flex-1 flex",
        ),
        # Right side - File info and interpreter
        rx.el.div(
            # Cursor position
            rx.el.div("Ln 1, Col 1", class_name="status-bar-item"),
            # Indentation
            rx.el.div("Spaces: 4", class_name="status-bar-item"),
            # Encoding
            rx.cond(
                EditorState.active_tab,
                rx.el.div(
                    EditorState.active_tab.encoding,
                    class_name="status-bar-item",
                ),
                rx.fragment(),
            ),
            # Line ending
            rx.el.div("LF", class_name="status-bar-item"),
            # Language (from active tab - using computed var)
            rx.el.div(
                EditorState.active_language_display,
                class_name="status-bar-item",
                id="status-bar-language",
            ),
            # Python interpreter (clickable to open palette)
            rx.el.div(
                rx.icon("terminal", size=14),
                CommandPaletteState.interpreter_display,
                class_name="status-bar-item flex items-center gap-1 cursor-pointer hover:bg-white/10",
                on_click=CommandPaletteState.open_interpreter_palette,
                id="status-bar-interpreter",
            ),
            class_name="flex",
        ),
        class_name="h-6 bg-pycodium-statusbar-bg text-white flex items-center text-xs",
        id="status-bar",
    )
