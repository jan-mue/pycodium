"""Settings component for the IDE."""

import reflex as rx


class SettingsState(rx.State):
    """State for the settings component."""

    active_tab: str = "user"
    search_query: str = ""
    expanded_category: str = "workbench"
    expanded_workbench: str | None = "appearance"

    @rx.event
    async def toggle_category(self, category: str) -> None:
        """Toggle the visibility of a settings category."""
        self.expanded_category = "commonly-used" if self.expanded_category == category else category

    @rx.event
    async def toggle_workbench_category(self, category: str) -> None:
        """Toggle the visibility of a workbench settings category."""
        self.expanded_workbench = None if self.expanded_workbench == category else category

    @rx.event
    async def set_active_tab(self, tab: str) -> None:
        """Set the active tab in the settings."""
        self.active_tab = tab

    @rx.event
    async def update_search_query(self, query: str) -> None:
        """Update the search query for settings."""
        self.search_query = query


def settings() -> rx.Component:
    """Creates the settings component for the IDE."""
    return rx.vstack(
        # Search bar
        rx.box(
            rx.box(
                rx.input(
                    type="text",
                    placeholder="Search settings",
                    value=SettingsState.search_query,
                    on_change=SettingsState.update_search_query,
                    class_name="w-full bg-pycodium-sidebar-bg border border-border rounded h-10 px-9 text-sm "
                    "focus:outline-none focus:ring-1 focus:ring-pycodium-highlight",
                ),
                class_name="relative w-full",
            ),
            class_name="p-2 flex flex-col gap-2",
        ),
        # Tabs
        rx.hstack(
            rx.button(
                "User",
                on_click=lambda: SettingsState.set_active_tab("user"),
                class_name=rx.cond(
                    SettingsState.active_tab == "user",
                    "px-3 py-2 text-sm border-b-2 border-pycodium-highlight",
                    "px-3 py-2 text-sm text-muted-foreground",
                ),
            ),
            rx.button(
                "Workspace",
                on_click=lambda: SettingsState.set_active_tab("workspace"),
                class_name=rx.cond(
                    SettingsState.active_tab == "workspace",
                    "px-3 py-2 text-sm border-b-2 border-pycodium-highlight",
                    "px-3 py-2 text-sm text-muted-foreground",
                ),
            ),
            rx.box(
                "Last synced: 1 wk ago",
                class_name="ml-auto text-xs text-muted-foreground flex items-center px-3",
            ),
            class_name="flex border-b border-border",
        ),
        # Sidebar and Content
        rx.hstack(
            # Sidebar
            rx.box(
                rx.foreach(
                    [
                        ("commonly-used", "Commonly Used"),
                        ("text-editor", "Text Editor"),
                        ("workbench", "Workbench"),
                        ("window", "Window"),
                        ("features", "Features"),
                        ("application", "Application"),
                        ("security", "Security"),
                        ("extensions", "Extensions"),
                    ],
                    lambda item: rx.button(
                        item[1],
                        on_click=lambda: SettingsState.toggle_category(item[0]),
                        class_name="w-full text-left flex items-center py-1 px-2 hover:bg-white/5 rounded",
                    ),
                ),
                class_name="w-64 border-r border-border overflow-y-auto p-2",
            ),
            # Content
            rx.box(
                rx.cond(
                    SettingsState.expanded_category == "workbench",
                    rx.box(
                        rx.foreach(
                            [
                                ("appearance", "Appearance"),
                                ("breadcrumbs", "Breadcrumbs"),
                                ("editor-management", "Editor Management"),
                                ("settings-editor", "Settings Editor"),
                                ("zen-mode", "Zen Mode"),
                                ("screencast-mode", "Screencast Mode"),
                            ],
                            lambda item: rx.button(
                                item[1],
                                on_click=lambda: SettingsState.toggle_workbench_category(item[0]),
                                class_name="w-full text-left px-2 py-1 hover:bg-white/5 rounded",
                            ),
                        ),
                        class_name="pl-4",
                    ),
                ),
                class_name="flex-1 overflow-y-auto",
            ),
            class_name="flex flex-1 overflow-hidden",
        ),
        class_name="h-full flex flex-col bg-pycodium-bg text-white",
    )
