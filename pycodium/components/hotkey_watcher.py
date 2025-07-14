"""Define a component that listens for key events globally."""

import reflex as rx
from reflex.event import key_event
from reflex.utils import imports
from typing_extensions import override


class GlobalHotkeyWatcher(rx.Fragment):
    """A component that listens for key events globally.

    Copied from https://reflex.dev/docs/api-reference/browser-javascript/#using-react-hooks
    """

    on_key_down: rx.EventHandler[key_event]

    @override
    def add_imports(self) -> imports.ImportDict:
        """Add the imports for the component."""
        return {
            "react": [imports.ImportVar(tag="useEffect")],
        }

    @override
    def add_hooks(self) -> list[str | rx.Var[str]]:
        """Add the hooks for the component."""
        return [
            """
            useEffect(() => {
                const handle_key = %s;
                document.addEventListener("keydown", handle_key, false);
                return () => {
                    document.removeEventListener("keydown", handle_key, false);
                }
            })
            """  # noqa: UP031
            % str(rx.Var.create(self.event_triggers["on_key_down"]))
        ]
