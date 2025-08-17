"""Main entry point for running the PyCodium IDE via its CLI."""

import logging
import os
from pathlib import Path
from typing import Annotated

import typer
import webview
from reflex import constants
from reflex.config import environment, get_config
from reflex.state import reset_disk_state_manager
from reflex.utils import exec, processes  # noqa: A004

from pycodium import __version__
from pycodium.constants import PROJECT_ROOT_DIR
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
    logger.info(f"Opening IDE with path: {path}")
    # TODO: run the frontend in dev mode when the package is installed in editable mode
    run_app_with_pywebview()
    # TODO: actually open path in editor


def run_app_with_pywebview(
    window_title: str = "PyCodium IDE",
    window_width: int = 1300,
    window_height: int = 800,
    frontend_path: Path = PROJECT_ROOT_DIR / constants.Dirs.WEB / constants.Dirs.STATIC / "index.html",
    backend_port: int | None = None,
    backend_host: str | None = None,
) -> None:
    """Run the Reflex app in a PyWebView window assuming the frontend is already exported.

    Args:
        window_title: The title of the PyWebView window
        window_width: The width of the PyWebView window
        window_height: The height of the PyWebView window
        frontend_path: The path to the exported frontend
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
        wait_for_port(backend_port)

        def on_closing():
            logger.info("Window closing: shutting down backend...")
            terminate_or_kill_process_on_port(backend_port)

        window = webview.create_window(
            title=window_title, url=str(frontend_path), width=window_width, height=window_height
        )
        window.events.closing += on_closing  # type: ignore[reportOptionalMemberAccess]
        webview.start()

    logger.info("Application shutdown complete.")


if __name__ == "__main__":
    app()
