"""Models for file paths."""

from __future__ import annotations

from pydantic import BaseModel


class FilePath(BaseModel):
    """A class representing a file path."""

    name: str
    sub_paths: list[FilePath] = []
    is_dir: bool = True
    loaded: bool = False  # Track if directory contents have been fetched (for lazy loading)
