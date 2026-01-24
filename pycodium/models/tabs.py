"""Models for tabs in the application."""

from __future__ import annotations

import asyncio  # noqa: TC003

from pydantic import BaseModel


class Tab(BaseModel):
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
