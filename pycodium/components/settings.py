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
    return rx.el.div(
        # Main container
        rx.el.div(
            # Search bar
            rx.el.div(
                rx.el.div(
                    rx.icon("search", size=16, class_name="absolute top-3 left-3 text-muted-foreground"),
                    rx.input(
                        type="text",
                        placeholder="Search settings",
                        value=SettingsState.search_query,
                        on_change=SettingsState.update_search_query,
                        class_name="w-full bg-pycodium-sidebar-bg border border-border rounded h-10 px-9 text-sm focus:outline-none focus:ring-1 focus:ring-pycodium-highlight",
                    ),
                    rx.icon("sliders-horizontal", size=16, class_name="absolute top-3 right-3 text-muted-foreground"),
                    class_name="relative w-full",
                ),
                class_name="p-2 flex flex-col gap-2",
            ),
            # Tabs
            rx.el.div(
                rx.el.button(
                    "User",
                    on_click=lambda: SettingsState.set_active_tab("user"),
                    class_name=rx.cond(
                        SettingsState.active_tab == "user",
                        "px-3 py-2 text-sm border-b-2 border-pycodium-highlight",
                        "px-3 py-2 text-sm text-muted-foreground",
                    ),
                ),
                rx.el.button(
                    "Workspace",
                    on_click=lambda: SettingsState.set_active_tab("workspace"),
                    class_name=rx.cond(
                        SettingsState.active_tab == "workspace",
                        "px-3 py-2 text-sm border-b-2 border-pycodium-highlight",
                        "px-3 py-2 text-sm text-muted-foreground",
                    ),
                ),
                rx.el.div(
                    "Last synced: 1 wk ago",
                    class_name="ml-auto text-xs text-muted-foreground flex items-center px-3",
                ),
                class_name="flex border-b border-border",
            ),
            class_name="flex flex-col gap-0",
        ),
        # Sidebar and Content
        rx.el.div(
            # Sidebar
            rx.el.div(
                rx.el.div(
                    # Commonly Used
                    rx.el.div(
                        rx.el.button(
                            rx.el.div(
                                rx.text(
                                    "\u25b6",
                                    class_name=rx.cond(
                                        SettingsState.expanded_category == "commonly-used",
                                        "transform rotate-90 transition-transform",
                                        "transform transition-transform",
                                    ),
                                ),
                                rx.text("Commonly Used", class_name="ml-1"),
                                class_name="flex items-center",
                            ),
                            on_click=lambda: SettingsState.toggle_category("commonly-used"),
                            class_name="w-full text-left flex items-center py-1 px-2 hover:bg-white/5 rounded",
                        ),
                        class_name="mb-2",
                    ),
                    # Text Editor
                    rx.el.div(
                        rx.el.button(
                            rx.el.div(
                                rx.text(
                                    "\u25b6",
                                    class_name=rx.cond(
                                        SettingsState.expanded_category == "text-editor",
                                        "transform rotate-90 transition-transform",
                                        "transform transition-transform",
                                    ),
                                ),
                                rx.text("Text Editor", class_name="ml-1"),
                                class_name="flex items-center",
                            ),
                            on_click=lambda: SettingsState.toggle_category("text-editor"),
                            class_name="w-full text-left flex items-center py-1 px-2 hover:bg-white/5 rounded",
                        ),
                        class_name="mb-2",
                    ),
                    # Workbench
                    rx.el.div(
                        rx.el.button(
                            rx.el.div(
                                rx.text(
                                    "\u25b6",
                                    class_name=rx.cond(
                                        SettingsState.expanded_category == "workbench",
                                        "transform rotate-90 transition-transform",
                                        "transform transition-transform",
                                    ),
                                ),
                                rx.text("Workbench", class_name="ml-1"),
                                class_name="flex items-center",
                            ),
                            on_click=lambda: SettingsState.toggle_category("workbench"),
                            class_name="w-full text-left flex items-center py-1 px-2 hover:bg-white/5 rounded",
                        ),
                        rx.cond(
                            SettingsState.expanded_category == "workbench",
                            rx.el.div(
                                rx.el.button(
                                    "Appearance",
                                    on_click=lambda: SettingsState.toggle_workbench_category("appearance"),
                                    class_name=rx.cond(
                                        SettingsState.expanded_workbench == "appearance",
                                        "w-full text-left px-2 py-1 hover:bg-white/5 rounded text-pycodium-highlight",
                                        "w-full text-left px-2 py-1 hover:bg-white/5 rounded",
                                    ),
                                ),
                                rx.el.button(
                                    "Breadcrumbs",
                                    on_click=lambda: SettingsState.toggle_workbench_category("breadcrumbs"),
                                    class_name="w-full text-left px-2 py-1 hover:bg-white/5 rounded",
                                ),
                                rx.el.button(
                                    "Editor Management",
                                    on_click=lambda: SettingsState.toggle_workbench_category("editor-management"),
                                    class_name="w-full text-left px-2 py-1 hover:bg-white/5 rounded",
                                ),
                                rx.el.button(
                                    "Settings Editor",
                                    on_click=lambda: SettingsState.toggle_workbench_category("settings-editor"),
                                    class_name="w-full text-left px-2 py-1 hover:bg-white/5 rounded",
                                ),
                                rx.el.button(
                                    "Zen Mode",
                                    on_click=lambda: SettingsState.toggle_workbench_category("zen-mode"),
                                    class_name="w-full text-left px-2 py-1 hover:bg-white/5 rounded",
                                ),
                                rx.el.button(
                                    "Screencast Mode",
                                    on_click=lambda: SettingsState.toggle_workbench_category("screencast-mode"),
                                    class_name="w-full text-left px-2 py-1 hover:bg-white/5 rounded",
                                ),
                                class_name="pl-4",
                            ),
                        ),
                        class_name="mb-2",
                    ),
                    # Window
                    rx.el.div(
                        rx.el.button(
                            rx.el.div(
                                rx.text(
                                    "\u25b6",
                                    class_name=rx.cond(
                                        SettingsState.expanded_category == "window",
                                        "transform rotate-90 transition-transform",
                                        "transform transition-transform",
                                    ),
                                ),
                                rx.text("Window", class_name="ml-1"),
                                class_name="flex items-center",
                            ),
                            on_click=lambda: SettingsState.toggle_category("window"),
                            class_name="w-full text-left flex items-center py-1 px-2 hover:bg-white/5 rounded",
                        ),
                        class_name="mb-2",
                    ),
                    # Features
                    rx.el.div(
                        rx.el.button(
                            rx.el.div(
                                rx.text(
                                    "\u25b6",
                                    class_name=rx.cond(
                                        SettingsState.expanded_category == "features",
                                        "transform rotate-90 transition-transform",
                                        "transform transition-transform",
                                    ),
                                ),
                                rx.text("Features", class_name="ml-1"),
                                class_name="flex items-center",
                            ),
                            on_click=lambda: SettingsState.toggle_category("features"),
                            class_name="w-full text-left flex items-center py-1 px-2 hover:bg-white/5 rounded",
                        ),
                        class_name="mb-2",
                    ),
                    # Application
                    rx.el.div(
                        rx.el.button(
                            rx.el.div(
                                rx.text(
                                    "\u25b6",
                                    class_name=rx.cond(
                                        SettingsState.expanded_category == "application",
                                        "transform rotate-90 transition-transform",
                                        "transform transition-transform",
                                    ),
                                ),
                                rx.text("Application", class_name="ml-1"),
                                class_name="flex items-center",
                            ),
                            on_click=lambda: SettingsState.toggle_category("application"),
                            class_name="w-full text-left flex items-center py-1 px-2 hover:bg-white/5 rounded",
                        ),
                        class_name="mb-2",
                    ),
                    # Security
                    rx.el.div(
                        rx.el.button(
                            rx.el.div(
                                rx.text(
                                    "\u25b6",
                                    class_name=rx.cond(
                                        SettingsState.expanded_category == "security",
                                        "transform rotate-90 transition-transform",
                                        "transform transition-transform",
                                    ),
                                ),
                                rx.text("Security", class_name="ml-1"),
                                class_name="flex items-center",
                            ),
                            on_click=lambda: SettingsState.toggle_category("security"),
                            class_name="w-full text-left flex items-center py-1 px-2 hover:bg-white/5 rounded",
                        ),
                        class_name="mb-2",
                    ),
                    # Extensions
                    rx.el.div(
                        rx.el.button(
                            rx.el.div(
                                rx.text(
                                    "\u25b6",
                                    class_name=rx.cond(
                                        SettingsState.expanded_category == "extensions",
                                        "transform rotate-90 transition-transform",
                                        "transform transition-transform",
                                    ),
                                ),
                                rx.text("Extensions", class_name="ml-1"),
                                class_name="flex items-center",
                            ),
                            on_click=lambda: SettingsState.toggle_category("extensions"),
                            class_name="w-full text-left flex items-center py-1 px-2 hover:bg-white/5 rounded",
                        ),
                        class_name="mb-2",
                    ),
                    class_name="p-2",
                ),
                class_name="w-64 border-r border-border overflow-y-auto",
            ),
            # Content
            rx.el.div(
                rx.cond(
                    (SettingsState.expanded_category == "workbench")
                    & (SettingsState.expanded_workbench == "appearance"),
                    rx.el.div(
                        # Icon Theme
                        rx.el.div(
                            rx.el.div(
                                rx.icon("settings", class_name="text-muted-foreground", size=18),
                                rx.heading("Icon Theme", class_name="text-lg ml-2"),
                                class_name="flex items-center mb-2",
                            ),
                            rx.text(
                                "Specifies the file icon theme used in the workbench or 'null' to not show any file icons.",
                                class_name="text-sm text-muted-foreground ml-8 mb-3",
                            ),
                            rx.el.div(
                                rx.select(
                                    [
                                        "Standard",
                                    ],
                                    class_name="w-full max-w-md px-3 py-2 bg-pycodium-sidebar-bg border border-border rounded text-white",
                                ),
                                class_name="ml-8",
                            ),
                            class_name="mb-8",
                        ),
                        # Side Bar: Location
                        rx.el.div(
                            rx.el.div(
                                rx.heading("Side Bar: Location", class_name="text-lg ml-8"),
                                class_name="flex items-center mb-2",
                            ),
                            rx.text(
                                "Controls the location of the primary side bar and activity bar. They can either show on the left or right of the workbench. The secondary side bar will show on the opposite side of the workbench.",
                                class_name="text-sm text-muted-foreground ml-8 mb-3",
                            ),
                            rx.el.div(
                                rx.select(
                                    ["right", "left"],
                                    class_name="w-full max-w-md px-3 py-2 bg-pycodium-sidebar-bg border border-border rounded text-white",
                                ),
                                class_name="ml-8",
                            ),
                            class_name="mb-8",
                        ),
                        # Color Theme
                        rx.el.div(
                            rx.el.div(
                                rx.heading("Color Theme", class_name="text-lg ml-8"),
                                class_name="flex items-center mb-2",
                            ),
                            rx.el.div(
                                rx.text(
                                    "Specifies the preferred color theme for light OS appearance when ",
                                ),
                                rx.text(
                                    "Window: Auto Detect Color Scheme",
                                    class_name="text-blue-400",
                                ),
                                rx.text(
                                    " is enabled.",
                                ),
                                class_name="flex flex-row ml-8 mb-3 text-sm text-muted-foreground",
                            ),
                            rx.el.div(
                                rx.select(
                                    [
                                        "Light+ (default light)",
                                        "Dark+ (default dark)",
                                        "Monokai",
                                        "One Dark Pro",
                                    ],
                                    class_name="w-full max-w-md px-3 py-2 bg-pycodium-sidebar-bg border border-border rounded text-white",
                                ),
                                class_name="ml-8",
                            ),
                            class_name="mb-8",
                        ),
                        class_name="p-4",
                    ),
                ),
                class_name="flex-1 overflow-y-auto",
            ),
            class_name="flex flex-1 overflow-hidden",
        ),
        class_name="h-full flex flex-col bg-pycodium-bg text-white",
    )
