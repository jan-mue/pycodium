"""Models for file paths."""

from __future__ import annotations

import reflex as rx


class FilePath(rx.Base):
    """A class representing a file path."""

    name: str
    sub_paths: list[FilePath] = []
    is_dir: bool = True
    loaded: bool = False  # Track if directory contents have been fetched (for lazy loading)
