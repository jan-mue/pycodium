"""Welcome to Reflex! This file outlines the steps to create a basic app."""

import reflex as rx

from pycodium.components.activity_bar import activity_bar
from pycodium.components.editor_area import editor_area
from pycodium.components.resizable_panels import group, handle, panel
from pycodium.components.sidebar import sidebar
from pycodium.components.status_bar import status_bar
from pycodium.state import EditorState, GlobalHotkeyWatcher


def index() -> rx.Component:
    """Main page of the PyCodium IDE. Test."""
    return rx.el.div(
        GlobalHotkeyWatcher.create(
            on_key_down=lambda key, key_info: rx.cond(
                key_info.meta_key, EditorState.on_key_down(key, key_info).prevent_default, None
            )
        ),
        rx.el.div(
            activity_bar(),
            group(
                rx.cond(
                    EditorState.sidebar_visible,
                    rx.fragment(
                        panel(
                            sidebar(),
                            default_size=20,
                            min_size=15,
                            max_size=40,
                            class_name="h-full",
                        ),
                        handle(
                            class_name="w-1 hover:bg-pycodium-highlight hover:cursor-col-resize",
                        ),
                    ),
                ),
                panel(
                    rx.el.div(
                        group(
                            panel(
                                editor_area(),
                                class_name="h-full overflow-hidden",
                            ),
                            direction="vertical",
                            class_name="h-full",
                        ),
                        class_name="h-full flex flex-col overflow-hidden",
                    ),
                    class_name="h-full",
                ),
                direction="horizontal",
                class_name="flex-1",
            ),
            class_name="flex-1 flex overflow-hidden",
        ),
        status_bar(),
        class_name="h-screen flex flex-col overflow-hidden",
    )


app = rx.App(theme=rx.theme(appearance="dark"), stylesheets=["/index.css"])
app.add_page(index, title="PyCodium", description="A modern Python IDE.", on_load=EditorState.open_project)
