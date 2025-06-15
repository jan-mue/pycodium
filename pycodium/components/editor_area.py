"""Builds the editor area component, which includes the editor tabs and the editor content."""

import reflex as rx

from pycodium.components.editor_tabs import editor_tabs
from pycodium.components.monaco import monaco
from pycodium.components.settings import settings
from pycodium.state import EditorState

default_monaco_options = {
    "selectOnLineNumbers": True,
    "roundedSelection": False,
    "readOnly": False,
    "cursorStyle": "line",
    "automaticLayout": True,
    "minimap": {"enabled": True},
    "scrollBeyondLastLine": False,
    "lineNumbers": "on",
}


def editor_content() -> rx.Component:
    """Builds the editor content area based on the active tab."""
    active_tab = EditorState.active_tab

    return rx.cond(
        active_tab.is_none(),
        rx.el.div(
            rx.el.div("Welcome to PyCodium", class_name="text-xl mb-2"),
            rx.el.div("Open a file to start editing", class_name="text-sm"),
            class_name="flex-1 flex items-center justify-center text-muted-foreground flex-col",
        ),
        rx.el.div(
            rx.cond(
                active_tab.is_special & (active_tab.special_component == "settings"),
                settings(),
                monaco(
                    value=active_tab.content,
                    language=active_tab.language,
                    path=active_tab.path,
                    theme="vs-dark",
                    options=default_monaco_options,
                    on_change=lambda content: EditorState.update_tab_content(active_tab.id, content),
                ),
            ),
            class_name="flex-1",
        ),
    )


def editor_area() -> rx.Component:
    """Build the editor area component, which includes the editor tabs and the editor content."""
    return rx.el.div(
        editor_tabs(),
        editor_content(),
        class_name="flex flex-col h-full",
    )
