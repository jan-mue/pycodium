"""Defines the sidebar component for the IDE."""

import reflex as rx

from pycodium.components.file_explorer import explorer
from pycodium.state import EditorState


def sidebar() -> rx.Component:
    """The sidebar component.

    Returns:
        The sidebar component.
    """
    return rx.el.div(
        rx.cond(
            EditorState.active_sidebar_tab == "explorer",
            explorer(),
            rx.cond(
                EditorState.active_sidebar_tab == "search",
                rx.el.div("Search functionality would be here", class_name="p-4 text-sm"),
                rx.cond(
                    EditorState.active_sidebar_tab == "source_control",
                    rx.el.div("Source control functionality would be here", class_name="p-4 text-sm"),
                    rx.cond(
                        EditorState.active_sidebar_tab == "debug",
                        rx.el.div("Debugging tools would be here", class_name="p-4 text-sm"),
                        rx.cond(
                            EditorState.active_sidebar_tab == "extensions",
                            rx.el.div("Extensions marketplace would be here", class_name="p-4 text-sm"),
                        ),
                    ),
                ),
            ),
        ),
        class_name="h-full w-full bg-pycodium-sidebar-bg overflow-auto flex flex-col",
    )
