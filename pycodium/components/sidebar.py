"""Defines the sidebar component for the IDE."""

import reflex as rx

from pycodium.components.file_explorer import explorer
from pycodium.state import EditorState


def sidebar() -> rx.Component:
    """The sidebar component.

    Returns:
        The sidebar component.
    """
    return rx.box(
        rx.cond(
            EditorState.active_sidebar_tab == "explorer",
            explorer(),
            rx.cond(
                EditorState.active_sidebar_tab == "search",
                rx.box(
                    rx.text("Search functionality would be here", class_name="p-4 text-sm"),
                ),
                rx.cond(
                    EditorState.active_sidebar_tab == "source_control",
                    rx.box(
                        rx.text("Source control functionality would be here", class_name="p-4 text-sm"),
                    ),
                    rx.cond(
                        EditorState.active_sidebar_tab == "debug",
                        rx.box(
                            rx.text("Debugging tools would be here", class_name="p-4 text-sm"),
                        ),
                        rx.cond(
                            EditorState.active_sidebar_tab == "extensions",
                            rx.box(
                                rx.text("Extensions marketplace would be here", class_name="p-4 text-sm"),
                            ),
                            rx.box(),
                        ),
                    ),
                ),
            ),
        ),
        class_name="h-full w-full bg-pycodium-sidebar-bg overflow-auto flex flex-col",
    )
