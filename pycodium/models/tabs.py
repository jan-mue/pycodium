"""Models for tabs in the application."""

from __future__ import annotations

import reflex as rx


class Tab(rx.Base):
    """A class representing a generic tab."""

    id: str
    title: str


class EditorTab(Tab):
    """A class representing an editor tab."""

    language: str
    content: str
    encoding: str
    path: str
    is_special: bool = False
    special_component: str | None = None
