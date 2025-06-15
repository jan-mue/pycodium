"""Defines the sidebar component for the IDE."""

import reflex as rx
from reflex.event import EventType

from pycodium.state import EditorState


def sidebar_item(
    icon: str, active: bool, on_click: EventType[()] | None = None, tooltip: str | None = None
) -> rx.Component:
    """Create a sidebar item with an icon and optional click handler."""
    return rx.el.div(
        rx.el.div(
            rx.icon(icon, size=22, class_name=rx.cond(active, "text-pycodium-text", "text-pycodium-icon")),
            class_name=(
                "w-12 h-12 flex items-center justify-center cursor-pointer",
                rx.cond(active, "border-l-2 border-pycodium-highlight bg-pycodium-sidebar-bg", "hover:bg-black/20"),
            ),
            on_click=on_click,
            title=tooltip,
        )
    )


def activity_bar() -> rx.Component:
    """Render the activity bar with sidebar items."""
    return rx.el.div(
        rx.el.div(
            sidebar_item(
                icon="folders",
                active=EditorState.sidebar_visible & (EditorState.active_sidebar_tab == "explorer"),
                on_click=rx.cond(
                    EditorState.active_sidebar_tab == "explorer",
                    EditorState.toggle_sidebar,
                    EditorState.set_active_sidebar_tab("explorer"),
                ),
                tooltip="Explorer",
            ),
            sidebar_item(
                icon="search",
                active=EditorState.sidebar_visible & (EditorState.active_sidebar_tab == "search"),
                on_click=rx.cond(
                    EditorState.active_sidebar_tab == "search",
                    EditorState.toggle_sidebar,
                    EditorState.set_active_sidebar_tab("search"),
                ),
                tooltip="Search",
            ),
            sidebar_item(
                icon="git-branch",
                active=EditorState.sidebar_visible & (EditorState.active_sidebar_tab == "source_control"),
                on_click=rx.cond(
                    EditorState.active_sidebar_tab == "source_control",
                    EditorState.toggle_sidebar,
                    EditorState.set_active_sidebar_tab("source_control"),
                ),
                tooltip="Source Control",
            ),
            sidebar_item(
                icon="bug",
                active=EditorState.sidebar_visible & (EditorState.active_sidebar_tab == "debug"),
                on_click=rx.cond(
                    EditorState.active_sidebar_tab == "debug",
                    EditorState.toggle_sidebar,
                    EditorState.set_active_sidebar_tab("debug"),
                ),
                tooltip="Debug",
            ),
            sidebar_item(
                icon="blocks",
                active=EditorState.sidebar_visible & (EditorState.active_sidebar_tab == "extensions"),
                on_click=rx.cond(
                    EditorState.active_sidebar_tab == "extensions",
                    EditorState.toggle_sidebar,
                    EditorState.set_active_sidebar_tab("extensions"),
                ),
                tooltip="Extensions",
            ),
            class_name="flex flex-col",
        ),
        rx.el.div(
            # Bottom items
            sidebar_item(
                icon="settings",
                active=False,
                on_click=EditorState.open_settings,
                tooltip="Settings",
            ),
            class_name="mt-auto mb-2 flex flex-col",
        ),
        class_name="h-full w-12 bg-pycodium-activity-bar flex flex-col",
    )
