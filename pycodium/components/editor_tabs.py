"""Builds the editor tabs component."""

import reflex as rx

from pycodium.state import EditorState


def editor_tabs():
    """Creates the editor tabs component."""
    return rx.el.div(
        rx.el.div(
            rx.foreach(
                EditorState.tabs,
                lambda tab: rx.el.div(
                    rx.el.span(tab.title, class_name="ml-2"),
                    rx.el.button(
                        rx.icon("x", size=14),
                        class_name="ml-2 opacity-50 hover:opacity-100",
                        on_click=EditorState.close_tab(tab.id),
                    ),
                    class_name=(
                        "flex items-center px-3 py-1 border-r border-black/20 cursor-pointer flex-shrink-0 editor-tab",
                        rx.cond(
                            tab.id == EditorState.active_tab_id,
                            "active bg-pycodium-terminal-bg border-t-2 border-t-pycodium-highlight",
                            "hover:bg-black/10",
                        ),
                    ),
                    on_click=EditorState.set_active_tab(tab.id),
                ),
            ),
            class_name="flex overflow-x-auto tabs-scrollbar",
        ),
        class_name="flex h-9 bg-pycodium-tab-inactive text-sm justify-start",
    )
