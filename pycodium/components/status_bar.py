"""Defines the status bar of the IDE."""

import reflex as rx

from pycodium.state import EditorState


def status_bar() -> rx.Component:
    """Creates the status bar component for the IDE."""
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    rx.icon("check", size=14),
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
        rx.el.div(
            rx.el.div("Ln 1, Col 1", class_name="status-bar-item"),
            rx.el.div("Spaces: 2", class_name="status-bar-item"),
            rx.el.div(EditorState.active_tab.encoding, class_name="status-bar-item"),
            rx.el.div("CRLF", class_name="status-bar-item"),
            rx.el.div("TypeScript", class_name="status-bar-item"),
            class_name="flex",
        ),
        class_name="h-6 bg-pycodium-statusbar-bg text-white flex items-center text-xs",
    )
