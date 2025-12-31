"""Component that listens for Tauri menu events and handles file/folder dialogs.

This component bridges Tauri's native menu events to Reflex state handlers.
When menu items are clicked, the Python backend evaluates JavaScript that calls
window.__PYCODIUM_MENU__, which triggers the appropriate action (opening dialogs, etc.).
"""

import reflex as rx
from reflex.utils import imports
from typing_extensions import override


class TauriMenuHandler(rx.Fragment):
    """A component that listens for Tauri menu events and handles file/folder dialogs.

    This component:
    1. Sets up a global window.__PYCODIUM_MENU__ function that receives menu actions
    2. Uses the Tauri dialog plugin to open native file/folder picker dialogs
    3. Calls back to Reflex event handlers with the selected paths
    """

    # Add the Tauri dialog plugin as a dependency (without using library= which conflicts with Fragment)
    lib_dependencies: list[str] = ["@tauri-apps/plugin-dialog@2"]

    # Event handler called when a file is selected from the Open File dialog
    on_file_selected: rx.EventHandler[rx.event.passthrough_event_spec(str)]

    # Event handler called when a folder is selected from the Open Folder dialog
    on_folder_selected: rx.EventHandler[rx.event.passthrough_event_spec(str)]

    # Event handler called when save action is triggered
    on_save: rx.EventHandler[rx.event.no_args_event_spec]

    # Event handler called when save as action is triggered
    on_save_as: rx.EventHandler[rx.event.no_args_event_spec]

    # Event handler called when close tab action is triggered
    on_close_tab: rx.EventHandler[rx.event.no_args_event_spec]

    @override
    def add_imports(self) -> imports.ImportDict:
        """Add the imports for the component."""
        return {
            "react": [imports.ImportVar(tag="useEffect")],
            "@tauri-apps/plugin-dialog": [imports.ImportVar(tag="open", alias="openDialog")],
        }

    @override
    def add_hooks(self) -> list[str | rx.Var[str]]:
        """Add the hooks for the component."""
        on_file_selected = rx.Var.create(self.event_triggers["on_file_selected"])
        on_folder_selected = rx.Var.create(self.event_triggers["on_folder_selected"])
        on_save = rx.Var.create(self.event_triggers["on_save"])
        on_save_as = rx.Var.create(self.event_triggers["on_save_as"])
        on_close_tab = rx.Var.create(self.event_triggers["on_close_tab"])

        return [
            f"""
            useEffect(() => {{
                // Check if we're running in Tauri
                const isTauri = window.__TAURI__ !== undefined;

                if (!isTauri) {{
                    console.log("Not running in Tauri, menu handler disabled");
                    return;
                }}

                // Set up the global menu handler function
                const setupMenuHandler = () => {{
                    try {{
                        // Set up the global menu handler function
                        window.__PYCODIUM_MENU__ = async (payload) => {{
                            const {{ action }} = payload;
                            console.log("Menu action received:", action);

                            switch (action) {{
                                case "open_file":
                                    try {{
                                        const filePath = await openDialog({{
                                            multiple: false,
                                            directory: false,
                                            title: "Open File"
                                        }});
                                        if (filePath) {{
                                            const handler = {on_file_selected!s};
                                            handler(filePath);
                                        }}
                                    }} catch (err) {{
                                        console.error("Failed to open file dialog:", err);
                                    }}
                                    break;

                                case "open_folder":
                                    try {{
                                        const folderPath = await openDialog({{
                                            multiple: false,
                                            directory: true,
                                            title: "Open Folder"
                                        }});
                                        if (folderPath) {{
                                            const handler = {on_folder_selected!s};
                                            handler(folderPath);
                                        }}
                                    }} catch (err) {{
                                        console.error("Failed to open folder dialog:", err);
                                    }}
                                    break;

                                case "save":
                                    try {{
                                        const handler = {on_save!s};
                                        handler();
                                    }} catch (err) {{
                                        console.error("Failed to handle save:", err);
                                    }}
                                    break;

                                case "save_as":
                                    try {{
                                        const handler = {on_save_as!s};
                                        handler();
                                    }} catch (err) {{
                                        console.error("Failed to handle save as:", err);
                                    }}
                                    break;

                                case "close_tab":
                                    try {{
                                        const handler = {on_close_tab!s};
                                        handler();
                                    }} catch (err) {{
                                        console.error("Failed to handle close tab:", err);
                                    }}
                                    break;

                                default:
                                    console.warn("Unknown menu action:", action);
                            }}
                        }};

                        console.log("Tauri menu handler initialized");
                    }} catch (err) {{
                        console.error("Failed to setup menu handler:", err);
                    }}
                }};

                setupMenuHandler();

                // Cleanup
                return () => {{
                    delete window.__PYCODIUM_MENU__;
                }};
            }}, [])
            """
        ]


tauri_menu_handler = TauriMenuHandler.create
