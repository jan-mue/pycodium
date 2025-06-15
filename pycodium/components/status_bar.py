"""Defines the status bar of the IDE."""

import reflex as rx

from pycodium.state import EditorState


def status_bar() -> rx.Component:
    """Creates the status bar component for the IDE."""
    return rx.box(
        rx.hstack(
            rx.hstack(
                rx.box(
                    rx.hstack(
                        rx.icon("check", size=14),
                        rx.text("main *"),
                        class_name="flex items-center gap-1",
                    ),
                    class_name="status-bar-item flex items-center",
                ),
                rx.box(
                    rx.icon("bell", size=14),
                    class_name="status-bar-item",
                ),
                class_name="flex-1 flex",
            ),
            rx.hstack(
                rx.box("Ln 1, Col 1", class_name="status-bar-item"),
                rx.box("Spaces: 2", class_name="status-bar-item"),
                rx.box(EditorState.active_tab.encoding, class_name="status-bar-item"),
                rx.box("CRLF", class_name="status-bar-item"),
                rx.box("TypeScript", class_name="status-bar-item"),
                class_name="flex",
            ),
            class_name="h-6 bg-pycodium-statusbar-bg text-white flex items-center text-xs",
        )
    )
