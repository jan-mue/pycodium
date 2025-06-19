"""Models for tabs in the application."""

from __future__ import annotations

from typing import TYPE_CHECKING

import reflex as rx

if TYPE_CHECKING:
    import asyncio


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
    on_not_active: asyncio.Event
    is_special: bool = False
    special_component: str | None = None
