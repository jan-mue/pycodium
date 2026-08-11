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
    """Completion item structure.

    Monaco definition: https://microsoft.github.io/monaco-editor/typedoc/interfaces/languages.CompletionItem.html
    """

    label: str
    kind: int
    insert_text: str
    documentation: str
    detail: str | None


class DeclarationRequest(TypedDict):
    """Declaration request data."""

    text: str
    position: dict[str, int]
    file_path: str


class SignatureHelpRequest(TypedDict):
    """Signature help request data."""

    text: str
    position: Position
    file_path: str | None


class ReferenceRequest(TypedDict):
    """Reference request data."""

    text: str
    position: Position
    file_path: str | None


class RenameRequest(TypedDict):
    """Rename request data."""

    text: str
    position: Position
    file_path: str | None
    new_name: str


class PrepareRenameRequest(TypedDict):
    """Prepare rename request data."""

    text: str
    position: Position
    file_path: str | None
