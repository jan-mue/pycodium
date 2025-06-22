"""Models for Monaco editor completion and hover requests."""

from typing import TypedDict


class Position(TypedDict):
    """Position in the editor."""

    line: int
    column: int


class CompletionRequest(TypedDict):
    """Completion request data."""

    text: str
    position: Position
    file_path: str | None


class HoverRequest(TypedDict):
    """Hover request data."""

    text: str
    position: Position
    file_path: str | None


class CompletionItem(TypedDict):
    """Completion item structure."""

    label: str
    kind: int
    insert_text: str
    documentation: str
    detail: str | None
