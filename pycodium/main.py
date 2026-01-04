"""Main entry point for running the PyCodium IDE via its CLI."""

import logging
import os
import sys
from pathlib import Path
from typing import Annotated

import typer
from pytauri import AppHandle, Manager, RunEvent, builder_factory, context_factory
from pytauri.ffi.lib import RunEventType
from pytauri_plugins.dialog import init as init_dialog_plugin
from reflex import constants
from reflex.config import environment, get_config
from reflex.state import reset_disk_state_manager
from reflex.utils import exec, processes  # noqa: A004

from pycodium import __version__
from pycodium.constants import PROJECT_ROOT_DIR, set_initial_path
from pycodium.menu import init_menu
from pycodium.utils.processes import terminate_or_kill_process_on_port, wait_for_port

# TODO: configure logging
logger = logging.getLogger(__name__)
app = typer.Typer()


@app.command()
def run(
    path: Annotated[Path | None, typer.Argument()] = None,
    show_version: Annotated[bool, typer.Option("--version", "-v", help="Show version and exit")] = False,
) -> None:
    """Run the PyCodium IDE."""
    if show_version:
        print(__version__)
        return

    # Set the initial path for the state to read on startup
    if path is not None:
        resolved_path = path.resolve()
        if resolved_path.exists():
            set_initial_path(resolved_path)
            logger.info(f"Opening IDE with path: {resolved_path}")
        else:
            logger.warning(f"Path does not exist: {path}")
    else:
        logger.info("Opening IDE with no initial path")

    # TODO: run the frontend in dev mode when the package is installed in editable mode
    run_app_with_tauri()


def run_app_with_tauri(
    window_title: str = "PyCodium IDE",
    backend_port: int | None = None,
    backend_host: str | None = None,
) -> None:
    """Run the Reflex app in a Tauri window assuming the frontend is already exported.

    Args:
        window_title: The title of the Tauri window
        backend_port: The port for the backend server
        backend_host: The host for the backend server
    """
    os.chdir(PROJECT_ROOT_DIR)
    config = get_config()

    backend_host = backend_host or config.backend_host

    environment.REFLEX_ENV_MODE.set(constants.Env.PROD)
    environment.REFLEX_COMPILE_CONTEXT.set(constants.CompileContext.RUN)
    environment.REFLEX_BACKEND_ONLY.set(True)
    environment.REFLEX_SKIP_COMPILE.set(True)

    reset_disk_state_manager()

    auto_increment_backend = not bool(backend_port or config.backend_port)
    backend_port = processes.handle_port(
        "backend",
        (backend_port or config.backend_port or constants.DefaultPorts.BACKEND_PORT),
        auto_increment=auto_increment_backend,
    )

    # Apply the new ports to the config.
    if backend_port != config.backend_port:
        config._set_persistent(backend_port=backend_port)  # type: ignore[reportPrivateUsage]

    # Reload the config to make sure the env vars are persistent.
    get_config(reload=True)

    logger.info(f"Starting Reflex app on port {backend_port}")
    commands = [(exec.run_backend_prod, backend_host, backend_port, config.loglevel.subprocess_level(), True)]
    with processes.run_concurrently_context(*commands):  # type: ignore[reportArgumentType]

        def app_setup(app_handle: AppHandle) -> None:
            """Setup hook for Tauri application."""
            # Register the dialog plugin for native file/folder dialogs
            app_handle.plugin(init_dialog_plugin())

            window = Manager.get_webview_window(app_handle, "main")
            wait_for_port(backend_port)
            if window:
                init_menu(app_handle, window)
                window.set_title(window_title)
                window.show()
                window.set_focus()
            else:
                logger.error("Could not find main window")

        def on_run_event(_app_handle: AppHandle, event: RunEventType) -> None:
            """Handle Tauri run events for cleanup on exit.

            Note: This callback must not raise exceptions (undefined behavior in PyTauri).
            """
            if isinstance(event, RunEvent.Exit):
                try:
                    logger.info("Received Exit event, terminating backend...")
                    terminate_or_kill_process_on_port(backend_port)
                except Exception:
                    logger.exception("Error during backend termination")

        tauri_app = builder_factory().build(
            context_factory(PROJECT_ROOT_DIR),
            invoke_handler=None,
            setup=app_setup,
        )
        logger.info("Tauri app running...")
        exit_code = tauri_app.run_return(on_run_event)  # blocks until the application exits
        if exit_code != 0:
            logger.error(f"Tauri app exited with code {exit_code}")
            sys.exit(exit_code)
    logger.info("Application shutdown complete.")


if __name__ == "__main__":
    app()
