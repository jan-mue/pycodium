"""Component that listens for Tauri menu events and handles file/folder dialogs.

This component bridges Tauri's native menu events to Reflex state handlers.
When menu items are clicked, the Python backend evaluates JavaScript that calls
window.__PYCODIUM_MENU__, which triggers the appropriate action (opening dialogs, etc.).
"""

from typing import Any

import reflex as rx
from reflex.constants.compiler import Hooks
from reflex.utils import imports
from reflex.vars.base import Var, VarData
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
    def add_hooks(self) -> list[str | Var[Any]]:
        """Add hooks to set up the Tauri menu handler.

        Returns:
            The hooks to add to the component.
        """
        hooks: list[str | Var[Any]] = []

        # Build handler map from event triggers using Var.create
        action_handlers: dict[str, tuple[Var[Any], bool]] = {}

        if "on_file_selected" in self.event_triggers:
            action_handlers["open_file"] = (
                Var.create(self.event_triggers["on_file_selected"]),
                True,  # needs dialog
            )

        if "on_folder_selected" in self.event_triggers:
            action_handlers["open_folder"] = (
                Var.create(self.event_triggers["on_folder_selected"]),
                True,  # needs dialog
            )

        if "on_save" in self.event_triggers:
            action_handlers["save"] = (
                Var.create(self.event_triggers["on_save"]),
                False,  # no dialog
            )

        if "on_save_as" in self.event_triggers:
            action_handlers["save_as"] = (
                Var.create(self.event_triggers["on_save_as"]),
                False,  # no dialog
            )

        if "on_close_tab" in self.event_triggers:
            action_handlers["close_tab"] = (
                Var.create(self.event_triggers["on_close_tab"]),
                False,  # no dialog
            )

        # Build switch cases
        cases = []
        for action, (handler_var, needs_dialog) in action_handlers.items():
            if needs_dialog:
                is_directory = "true" if action == "open_folder" else "false"
                title = "Open Folder" if action == "open_folder" else "Open File"
                case = f"""
                    case "{action}":
                        try {{
                            const path = await openDialog({{
                                multiple: false,
                                directory: {is_directory},
                                title: "{title}"
                            }});
                            if (path) {{
                                ({handler_var!s})(path);
                            }}
                        }} catch (err) {{
                            console.error("Failed to open dialog:", err);
                        }}
                        break;
"""
            else:
                case = f"""
                    case "{action}":
                        try {{
                            ({handler_var!s})();
                        }} catch (err) {{
                            console.error("Failed to handle {action}:", err);
                        }}
                        break;
"""
            cases.append(case)

        switch_body = "".join(cases)

        hook_expr = f"""
useEffect(() => {{
    if (typeof window === 'undefined' || window.__TAURI__ === undefined) return;

    window.__PYCODIUM_MENU__ = async (payload) => {{
        const {{ action }} = payload;
        switch (action) {{{switch_body}
            default:
                console.warn("Unknown menu action:", action);
        }}
    }};

    return () => {{
        delete window.__PYCODIUM_MENU__;
    }};
}}, []);
"""

        hooks.append(
            Var(
                hook_expr,
                _var_data=VarData(position=Hooks.HookPosition.POST_TRIGGER),
            )
        )

        return hooks


tauri_menu_handler = TauriMenuHandler.create
