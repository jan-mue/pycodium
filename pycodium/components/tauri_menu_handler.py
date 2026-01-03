"""Component that listens for Tauri menu events and handles file/folder dialogs.

This component bridges Tauri's native menu events to Reflex state handlers.
When menu items are clicked, the Python backend evaluates JavaScript that calls
window.__PYCODIUM_MENU__, which triggers the appropriate action (opening dialogs, etc.).
"""

import dataclasses
from typing import Any

import reflex as rx
from reflex.utils import imports
from reflex.vars.base import Var
from typing_extensions import override


@dataclasses.dataclass
class MenuAction:
    """Configuration for a menu action."""

    event_trigger_name: str
    dialog_config: dict[str, Any] | None = None


# Define action configurations in Python
MENU_ACTIONS: dict[str, MenuAction] = {
    "open_file": MenuAction(
        event_trigger_name="on_file_selected",
        dialog_config={"multiple": False, "directory": False, "title": "Open File"},
    ),
    "open_folder": MenuAction(
        event_trigger_name="on_folder_selected",
        dialog_config={"multiple": False, "directory": True, "title": "Open Folder"},
    ),
    "save": MenuAction(event_trigger_name="on_save"),
    "save_as": MenuAction(event_trigger_name="on_save_as"),
    "close_tab": MenuAction(event_trigger_name="on_close_tab"),
}


class TauriMenuHandler(rx.Fragment):
    """A component that listens for Tauri menu events and handles file/folder dialogs.

    This component:
    1. Sets up a global window.__PYCODIUM_MENU__ function that receives menu actions
    2. Uses the Tauri dialog plugin to open native file/folder picker dialogs
    3. Calls back to Reflex event handlers with the selected paths
    """

    lib_dependencies: list[str] = ["@tauri-apps/plugin-dialog@2"]

    on_file_selected: rx.EventHandler[rx.event.passthrough_event_spec(str)]
    on_folder_selected: rx.EventHandler[rx.event.passthrough_event_spec(str)]
    on_save: rx.EventHandler[rx.event.no_args_event_spec]
    on_save_as: rx.EventHandler[rx.event.no_args_event_spec]
    on_close_tab: rx.EventHandler[rx.event.no_args_event_spec]

    @override
    def _exclude_props(self) -> list[str]:
        """Exclude event handler props from being passed to Fragment.

        Returns:
            List of prop names to exclude from the Fragment.
        """
        return [*super()._exclude_props(), *self.event_triggers.keys()]

    @override
    def add_imports(self) -> imports.ImportDict:
        """Add the imports for the component.

        Returns:
            The imports for the component.
        """
        return {
            "react": [imports.ImportVar(tag="useEffect")],
            "@tauri-apps/plugin-dialog": [imports.ImportVar(tag="open", alias="openDialog")],
        }

    def _build_action_config_js(self) -> str:
        """Build the JavaScript action configuration object.

        Returns:
            JavaScript object literal defining action configurations.
        """
        entries = []
        for action_name, config in MENU_ACTIONS.items():
            trigger = self.event_triggers.get(config.event_trigger_name)
            if trigger is None:
                continue

            # Convert the event trigger to a Var that uses addEvents/queueEvents
            callback_var = Var.create(trigger)

            dialog_config = config.dialog_config
            if dialog_config is not None:
                dialog_js = (
                    f"{{ multiple: {str(dialog_config['multiple']).lower()}, "
                    f"directory: {str(dialog_config['directory']).lower()}, "
                    f'title: "{dialog_config["title"]}" }}'
                )
                entry = f"{action_name}: {{ dialog: {dialog_js}, callback: {callback_var!s} }}"
            else:
                entry = f"{action_name}: {{ callback: {callback_var!s} }}"

            entries.append(entry)

        return "{\n            " + ",\n            ".join(entries) + "\n        }"

    @override
    def add_hooks(self) -> list[str | rx.Var[Any]]:
        """Add hooks to set up the Tauri menu handler.

        Returns:
            The hooks to add to the component.
        """
        action_config = self._build_action_config_js()

        return [
            f"""
useEffect(() => {{
    if (typeof window === 'undefined' || window.__TAURI__ === undefined) {{
        return;
    }}

    const actionConfig = {action_config};

    window.__PYCODIUM_MENU__ = async (payload) => {{
        const {{ action }} = payload;
        const config = actionConfig[action];

        if (!config) {{
            console.warn("Unknown menu action:", action);
            return;
        }}

        try {{
            if (config.dialog) {{
                const path = await openDialog(config.dialog);
                if (path) {{
                    config.callback(path);
                }}
            }} else {{
                config.callback();
            }}
        }} catch (err) {{
            console.error(`Failed to handle ${{action}}:`, err);
        }}
    }};

    return () => {{
        delete window.__PYCODIUM_MENU__;
    }};
}}, []);
"""
        ]


tauri_menu_handler = TauriMenuHandler.create
