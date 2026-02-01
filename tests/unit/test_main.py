from __future__ import annotations

from typing import TYPE_CHECKING

from inline_snapshot import snapshot
from pytauri import AppHandle, RunEvent
from reflex.constants import LogLevel
from reflex.utils import exec  # noqa: A004

from pycodium import __version__
from pycodium.main import app

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path
    from typing import Unpack

    from pytauri import App, BuilderArgs, Context
    from pytauri.ffi.lib import RunEventType
    from pytest_mock import MockerFixture
    from typer.testing import CliRunner


def test_cli_prints_version(runner: CliRunner) -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.stdout == __version__ + "\n"


def test_cli_starts_ide(runner: CliRunner, mocker: MockerFixture) -> None:
    mock_reset = mocker.patch("pycodium.main.reset_disk_state_manager")
    mock_run_concurrent = mocker.patch("pycodium.main.processes.run_concurrently_context")
    mock_wait_for_port = mocker.patch("pycodium.main.wait_for_port")
    mock_handle_port = mocker.patch("pycodium.main.processes.handle_port")
    mock_handle_port.return_value = 8000
    mocker.patch("pycodium.main.context_factory")
    mock_builder_factory = mocker.patch("pycodium.main.builder_factory")
    mock_manager_get_window = mocker.patch("pycodium.main.Manager.get_webview_window")
    mock_init_dialog_plugin = mocker.patch("pycodium.main.init_dialog_plugin")
    mock_init_menu = mocker.patch("pycodium.main.init_menu")
    mock_window = mocker.MagicMock()
    mock_manager_get_window.return_value = mock_window

    mock_builder = mocker.MagicMock()

    def mock_build(context: Context, **kwargs: Unpack[BuilderArgs]) -> App:  # noqa: ARG001
        mock_app_handle = mocker.MagicMock()
        assert "setup" in kwargs
        setup = kwargs["setup"]
        setup(mock_app_handle)

        mock_tauri_app = mocker.MagicMock()

        def mock_run_return(callback: Callable[[AppHandle, RunEventType], None] | None = None) -> int:
            if callback is not None:
                callback(mock_app_handle, RunEvent.Exit())
            return 0

        mock_tauri_app.run_return = mock_run_return
        return mock_tauri_app

    mock_builder.build = mock_build
    mock_builder_factory.return_value = mock_builder

    mock_terminate = mocker.patch("pycodium.main.terminate_or_kill_process_on_port")

    result = runner.invoke(app)
    assert result.exit_code == 0

    mock_reset.assert_called_once()
    mock_run_concurrent.assert_called_once_with((exec.run_backend_prod, "0.0.0.0", 8000, LogLevel.WARNING, True))
    mock_wait_for_port.assert_called_with(8000)
    mock_init_dialog_plugin.assert_called_once()
    mock_manager_get_window.assert_called_once()
    mock_init_menu.assert_called_once()
    mock_window.set_title.assert_called_once_with(snapshot("PyCodium IDE"))
    mock_window.show.assert_called_once()
    mock_window.set_focus.assert_called_once()
    mock_terminate.assert_called_once_with(8000)


def test_cli_with_existing_path(runner: CliRunner, mocker: MockerFixture, tmp_path: Path) -> None:
    """Test CLI with an existing path argument sets the environment variable."""
    mocker.patch("pycodium.main.run_app_with_tauri")
    test_file = tmp_path / "test.py"
    test_file.write_text("print('hello')")

    result = runner.invoke(app, [str(test_file)])

    assert result.exit_code == 0


def test_cli_with_nonexistent_path(runner: CliRunner, mocker: MockerFixture) -> None:
    """Test CLI with a non-existent path logs warning but continues."""
    mock_run_app = mocker.patch("pycodium.main.run_app_with_tauri")

    result = runner.invoke(app, ["/nonexistent/path/to/file.py"])

    assert result.exit_code == 0
    mock_run_app.assert_called_once()


def test_cli_window_not_found(runner: CliRunner, mocker: MockerFixture) -> None:
    """Test that error is logged when main window is not found."""
    mocker.patch("pycodium.main.reset_disk_state_manager")
    mocker.patch("pycodium.main.processes.run_concurrently_context")
    mocker.patch("pycodium.main.wait_for_port")
    mock_handle_port = mocker.patch("pycodium.main.processes.handle_port")
    mock_handle_port.return_value = 8000
    mocker.patch("pycodium.main.context_factory")
    mock_builder_factory = mocker.patch("pycodium.main.builder_factory")
    mock_manager_get_window = mocker.patch("pycodium.main.Manager.get_webview_window", return_value=None)
    mocker.patch("pycodium.main.init_dialog_plugin")
    mock_logger = mocker.patch("pycodium.main.logger")

    mock_builder = mocker.MagicMock()

    def mock_build(context: Context, **kwargs: Unpack[BuilderArgs]) -> App:  # noqa: ARG001
        mock_app_handle = mocker.MagicMock()
        assert "setup" in kwargs
        setup = kwargs["setup"]
        setup(mock_app_handle)

        mock_tauri_app = mocker.MagicMock()
        mock_tauri_app.run_return = mocker.MagicMock(return_value=0)
        return mock_tauri_app

    mock_builder.build = mock_build
    mock_builder_factory.return_value = mock_builder

    result = runner.invoke(app)
    assert result.exit_code == 0
    mock_manager_get_window.assert_called_once()
    mock_logger.error.assert_called_with("Could not find main window")


def test_cli_backend_termination_exception(runner: CliRunner, mocker: MockerFixture) -> None:
    """Test that exceptions during backend termination are handled gracefully."""
    mocker.patch("pycodium.main.reset_disk_state_manager")
    mocker.patch("pycodium.main.processes.run_concurrently_context")
    mocker.patch("pycodium.main.wait_for_port")
    mock_handle_port = mocker.patch("pycodium.main.processes.handle_port")
    mock_handle_port.return_value = 8000
    mocker.patch("pycodium.main.context_factory")
    mock_builder_factory = mocker.patch("pycodium.main.builder_factory")
    mock_manager_get_window = mocker.patch("pycodium.main.Manager.get_webview_window")
    mocker.patch("pycodium.main.init_dialog_plugin")
    mocker.patch("pycodium.main.init_menu")
    mock_window = mocker.MagicMock()
    mock_manager_get_window.return_value = mock_window

    mock_terminate = mocker.patch(
        "pycodium.main.terminate_or_kill_process_on_port", side_effect=RuntimeError("Termination failed")
    )

    mock_builder = mocker.MagicMock()

    def mock_build(context: Context, **kwargs: Unpack[BuilderArgs]) -> App:  # noqa: ARG001
        mock_app_handle = mocker.MagicMock()
        assert "setup" in kwargs
        setup = kwargs["setup"]
        setup(mock_app_handle)

        mock_tauri_app = mocker.MagicMock()

        def mock_run_return(callback: Callable[[AppHandle, RunEventType], None] | None = None) -> int:
            if callback is not None:
                callback(mock_app_handle, RunEvent.Exit())
            return 0

        mock_tauri_app.run_return = mock_run_return
        return mock_tauri_app

    mock_builder.build = mock_build
    mock_builder_factory.return_value = mock_builder

    result = runner.invoke(app)
    assert result.exit_code == 0
    mock_terminate.assert_called_once()


def test_cli_nonzero_exit_code(runner: CliRunner, mocker: MockerFixture) -> None:
    """Test that non-zero exit code from Tauri is propagated."""
    mocker.patch("pycodium.main.reset_disk_state_manager")
    mocker.patch("pycodium.main.processes.run_concurrently_context")
    mocker.patch("pycodium.main.wait_for_port")
    mock_handle_port = mocker.patch("pycodium.main.processes.handle_port")
    mock_handle_port.return_value = 8000
    mocker.patch("pycodium.main.context_factory")
    mock_builder_factory = mocker.patch("pycodium.main.builder_factory")
    mock_manager_get_window = mocker.patch("pycodium.main.Manager.get_webview_window")
    mocker.patch("pycodium.main.init_dialog_plugin")
    mocker.patch("pycodium.main.init_menu")
    mock_window = mocker.MagicMock()
    mock_manager_get_window.return_value = mock_window

    mock_builder = mocker.MagicMock()

    def mock_build(context: Context, **kwargs: Unpack[BuilderArgs]) -> App:  # noqa: ARG001
        mock_app_handle = mocker.MagicMock()
        assert "setup" in kwargs
        setup = kwargs["setup"]
        setup(mock_app_handle)

        mock_tauri_app = mocker.MagicMock()
        mock_tauri_app.run_return = mocker.MagicMock(return_value=1)
        return mock_tauri_app

    mock_builder.build = mock_build
    mock_builder_factory.return_value = mock_builder

    result = runner.invoke(app)
    assert result.exit_code == 1
