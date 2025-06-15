"""Custom component for resizable panels using react-resizable-panels.

Props are documented here: https://github.com/bvaughn/react-resizable-panels/tree/main/packages/react-resizable-panels
"""

from typing import Literal

import reflex as rx


class ResizablePanels(rx.Component):
    """Base class for ResizablePanels components."""

    library = "react-resizable-panels@3.0.2"


class PanelGroup(ResizablePanels):
    """PanelGroup component."""

    tag = "PanelGroup"

    # Unique id to auto-save the group layout via localStorage
    auto_save_id: rx.Var[str]

    # Group orientation
    direction: rx.Var[Literal["horizontal", "vertical"]]

    on_layout: rx.EventHandler[lambda e0: [e0]]


class Panel(ResizablePanels):
    """Panel component."""

    tag = "Panel"

    # Whether the panel is collapsible
    collapsible: rx.Var[bool]

    # Panel should collapse to this size
    collapsed_size: rx.Var[int]

    # Default size of the panel (should be a number between 1 - 100)
    default_size: rx.Var[int]

    # Maximum size of the panel (should be a number between 1 - 100)
    max_size: rx.Var[int]

    # Minimum size of the panel (should be a number between 1 - 100)
    min_size: rx.Var[int]

    # Event handlers triggered when the panel is collapsed
    on_collapse: rx.EventHandler[list]

    # Event handlers triggered when the panel is expanded
    on_expand: rx.EventHandler[list]

    # Event handlers triggered when the panel is resized
    on_resize: rx.EventHandler[lambda e0: [e0]]

    # Order of the panel within the group
    order: rx.Var[int]


class PanelResizeHandle(ResizablePanels):
    """PanelResizeHandle component."""

    tag = "PanelResizeHandle"


group = PanelGroup.create
panel = Panel.create
handle = PanelResizeHandle.create
