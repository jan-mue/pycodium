"""Unit tests for TauriMenuHandler component."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
import reflex as rx
from reflex.utils.imports import ImportVar

from pycodium.components.tauri_menu_handler import (
    MENU_ACTIONS,
    TauriMenuHandler,
    tauri_menu_handler,
)

if TYPE_CHECKING:
    from reflex.components.component import Component


class MenuHandlerTestState(rx.State):
    """A test state for event handler tests."""

    @rx.event
    def on_file_selected(self, path: str) -> None:
        """Handle file selected event.

        Args:
            path: The selected file path.
        """

    @rx.event
    def on_folder_selected(self, path: str) -> None:
        """Handle folder selected event.

        Args:
            path: The selected folder path.
        """

    @rx.event
    def on_save(self) -> None:
        """Handle save event."""

    @rx.event
    def on_save_as(self) -> None:
        """Handle save as event."""

    @rx.event
    def on_close_tab(self) -> None:
        """Handle close tab event."""


def get_all_hooks_str(component: Component) -> str:
    """Get all hooks as a single concatenated string.

    Args:
        component: The component to get hooks from.

    Returns:
        All hooks concatenated as a single string.
    """
    hooks = list(component._get_all_hooks())  # pyright: ignore[reportPrivateUsage]
    return "\n".join(str(hook) for hook in hooks)


@pytest.fixture
def component() -> Component:
    """Create a TauriMenuHandler component with all event handlers.

    Returns:
        A TauriMenuHandler component instance.
    """
    return TauriMenuHandler.create(
        on_file_selected=MenuHandlerTestState.on_file_selected,
        on_folder_selected=MenuHandlerTestState.on_folder_selected,
        on_save=MenuHandlerTestState.on_save,
        on_save_as=MenuHandlerTestState.on_save_as,
        on_close_tab=MenuHandlerTestState.on_close_tab,
    )


@pytest.fixture
def partial_component() -> Component:
    """Create a TauriMenuHandler with only some event handlers.

    Returns:
        A TauriMenuHandler component instance with partial handlers.
    """
    return TauriMenuHandler.create(
        on_file_selected=MenuHandlerTestState.on_file_selected,
        on_save=MenuHandlerTestState.on_save,
    )


class TestTauriMenuHandlerCreate:
    """Tests for TauriMenuHandler component creation."""

    def test_create_with_all_handlers(self, component: Component) -> None:
        """Test that the component can be created with all event handlers."""
        assert isinstance(component, TauriMenuHandler)

    def test_create_with_factory_function(self) -> None:
        """Test that the factory function works correctly."""
        comp = tauri_menu_handler(
            on_file_selected=MenuHandlerTestState.on_file_selected,
            on_save=MenuHandlerTestState.on_save,
        )
        assert isinstance(comp, TauriMenuHandler)

    def test_create_without_handlers(self) -> None:
        """Test that component can be created without any handlers."""
        comp = TauriMenuHandler.create()
        assert isinstance(comp, TauriMenuHandler)


class TestTauriMenuHandlerEventTriggers:
    """Tests for TauriMenuHandler event triggers."""

    def test_event_triggers_registered(self, component: Component) -> None:
        """Test that all event triggers are registered."""
        triggers = component.get_event_triggers()
        expected_triggers = {
            "on_file_selected",
            "on_folder_selected",
            "on_save",
            "on_save_as",
            "on_close_tab",
        }
        for trigger in expected_triggers:
            assert trigger in triggers, f"Missing event trigger: {trigger}"

    def test_event_triggers_in_component(self, component: Component) -> None:
        """Test that event triggers are set in the component."""
        assert "on_file_selected" in component.event_triggers
        assert "on_folder_selected" in component.event_triggers
        assert "on_save" in component.event_triggers
        assert "on_save_as" in component.event_triggers
        assert "on_close_tab" in component.event_triggers


class TestTauriMenuHandlerImports:
    """Tests for TauriMenuHandler imports."""

    def test_imports_contain_react_useeffect(self, component: Component) -> None:
        """Test that imports contain useEffect from React."""
        imports = component._get_all_imports()  # pyright: ignore[reportPrivateUsage]
        assert "react" in imports
        react_imports = imports["react"]
        assert any(
            (imp.tag == "useEffect" if isinstance(imp, ImportVar) else imp == "useEffect") for imp in react_imports
        )

    def test_imports_contain_tauri_dialog(self, component: Component) -> None:
        """Test that imports contain openDialog from Tauri dialog plugin."""
        imports = component._get_all_imports()  # pyright: ignore[reportPrivateUsage]
        assert "@tauri-apps/plugin-dialog" in imports
        dialog_imports = imports["@tauri-apps/plugin-dialog"]
        assert any(
            ((imp.tag == "open" and imp.alias == "openDialog") if isinstance(imp, ImportVar) else imp == "openDialog")
            for imp in dialog_imports
        )


class TestTauriMenuHandlerHooks:
    """Tests for TauriMenuHandler hooks generation."""

    def test_hooks_contain_useeffect(self, component: Component) -> None:
        """Test that hooks contain useEffect call."""
        hooks_str = get_all_hooks_str(component)
        assert "useEffect" in hooks_str

    def test_hooks_setup_window_pycodium_menu(self, component: Component) -> None:
        """Test that hooks set up window.__PYCODIUM_MENU__."""
        hooks_str = get_all_hooks_str(component)
        assert "window.__PYCODIUM_MENU__" in hooks_str

    def test_hooks_cleanup_on_unmount(self, component: Component) -> None:
        """Test that hooks clean up on unmount."""
        hooks_str = get_all_hooks_str(component)
        assert "delete window.__PYCODIUM_MENU__" in hooks_str

    def test_hooks_check_tauri_environment(self, component: Component) -> None:
        """Test that hooks check for Tauri environment before setup."""
        hooks_str = get_all_hooks_str(component)
        assert "window.__TAURI__" in hooks_str

    def test_hooks_contain_open_dialog(self, component: Component) -> None:
        """Test that hooks contain openDialog call for file/folder actions."""
        hooks_str = get_all_hooks_str(component)
        assert "openDialog" in hooks_str

    def test_hooks_contain_action_config(self, component: Component) -> None:
        """Test that hooks contain action configuration object."""
        hooks_str = get_all_hooks_str(component)
        assert "actionConfig" in hooks_str


class TestTauriMenuHandlerActionConfig:
    """Tests for TauriMenuHandler action configuration."""

    def test_action_config_contains_all_actions(self, component: Component) -> None:
        """Test that action config contains all defined actions."""
        hooks_str = get_all_hooks_str(component)
        for action_name in MENU_ACTIONS:
            assert action_name in hooks_str, f"Missing action in config: {action_name}"

    def test_action_config_open_file_dialog_settings(self, component: Component) -> None:
        """Test that open_file action has correct dialog settings."""
        hooks_str = get_all_hooks_str(component)
        # open_file should have directory: false
        assert "directory: false" in hooks_str or "directory:false" in hooks_str

    def test_action_config_open_folder_dialog_settings(self, component: Component) -> None:
        """Test that open_folder action has correct dialog settings."""
        hooks_str = get_all_hooks_str(component)
        # open_folder should have directory: true
        assert "directory: true" in hooks_str or "directory:true" in hooks_str

    def test_action_config_contains_callbacks(self, component: Component) -> None:
        """Test that action config contains callback functions."""
        hooks_str = get_all_hooks_str(component)
        assert "callback:" in hooks_str or "callback :" in hooks_str

    def test_partial_component_only_includes_provided_handlers(self, partial_component: Component) -> None:
        """Test that partial component only includes provided handlers in config."""
        hooks_str = get_all_hooks_str(partial_component)
        # Should include open_file and save
        assert "open_file" in hooks_str
        assert "save:" in hooks_str or '"save"' in hooks_str


class TestTauriMenuHandlerJavaScriptEventHandling:
    """Tests for JavaScript event handling in the generated hooks."""

    def test_hooks_contain_addevents_call(self, component: Component) -> None:
        """Test that hooks contain addEvents call for Reflex event handling."""
        hooks_str = get_all_hooks_str(component)
        # The callback should use Reflex's event queueing mechanism
        # This is embedded in the Var.create(trigger) output
        assert "addEvents" in hooks_str or "queueEvents" in hooks_str or "Event(" in hooks_str

    def test_hooks_handle_async_dialog(self, component: Component) -> None:
        """Test that hooks handle async dialog operations."""
        hooks_str = get_all_hooks_str(component)
        assert "async" in hooks_str
        assert "await" in hooks_str

    def test_hooks_handle_errors(self, component: Component) -> None:
        """Test that hooks have error handling."""
        hooks_str = get_all_hooks_str(component)
        assert "catch" in hooks_str or "try" in hooks_str

    def test_hooks_check_path_before_callback(self, component: Component) -> None:
        """Test that hooks check if path is selected before calling callback."""
        hooks_str = get_all_hooks_str(component)
        # Should check if path exists before calling callback
        assert "if (path)" in hooks_str or "path &&" in hooks_str


class TestMenuActionsConfig:
    """Tests for MENU_ACTIONS configuration."""

    def test_menu_actions_has_required_actions(self) -> None:
        """Test that MENU_ACTIONS contains all required actions."""
        required_actions = ["open_file", "open_folder", "save", "save_as", "close_tab"]
        for action in required_actions:
            assert action in MENU_ACTIONS, f"Missing action: {action}"

    def test_open_file_action_config(self) -> None:
        """Test open_file action configuration."""
        action = MENU_ACTIONS["open_file"]
        assert action.event_trigger_name == "on_file_selected"
        assert action.dialog_config is not None
        assert action.dialog_config["directory"] is False
        assert action.dialog_config["multiple"] is False

    def test_open_folder_action_config(self) -> None:
        """Test open_folder action configuration."""
        action = MENU_ACTIONS["open_folder"]
        assert action.event_trigger_name == "on_folder_selected"
        assert action.dialog_config is not None
        assert action.dialog_config["directory"] is True
        assert action.dialog_config["multiple"] is False

    def test_save_action_config(self) -> None:
        """Test save action configuration."""
        action = MENU_ACTIONS["save"]
        assert action.event_trigger_name == "on_save"
        assert action.dialog_config is None

    def test_save_as_action_config(self) -> None:
        """Test save_as action configuration."""
        action = MENU_ACTIONS["save_as"]
        assert action.event_trigger_name == "on_save_as"
        assert action.dialog_config is None

    def test_close_tab_action_config(self) -> None:
        """Test close_tab action configuration."""
        action = MENU_ACTIONS["close_tab"]
        assert action.event_trigger_name == "on_close_tab"
        assert action.dialog_config is None


class TestTauriMenuHandlerExcludeProps:
    """Tests for TauriMenuHandler _exclude_props functionality."""

    def test_event_triggers_excluded_from_fragment_props(self, component: Component) -> None:
        """Test that event trigger props are excluded from Fragment props."""
        excluded = component._exclude_props()  # pyright: ignore[reportPrivateUsage]
        # All event triggers should be excluded
        for trigger in component.event_triggers:
            assert trigger in excluded, f"Event trigger {trigger} should be excluded from props"


class TestTauriMenuHandlerLibDependencies:
    """Tests for TauriMenuHandler library dependencies."""

    def test_lib_dependencies_includes_tauri_dialog(self) -> None:
        """Test that lib_dependencies includes the Tauri dialog plugin."""
        assert "@tauri-apps/plugin-dialog@2" in TauriMenuHandler.lib_dependencies
