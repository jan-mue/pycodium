"""Constants for the PyCodium project."""

from pathlib import Path

PROJECT_ROOT_DIR = Path(__file__).parent.parent

# Module-level variable for initial path passed from CLI
_initial_path: Path | None = None


def set_initial_path(path: Path | None) -> None:
    """Set the initial path to open when the IDE starts.

    Args:
        path: The path to open, or None for no initial path.
    """
    global _initial_path  # noqa: PLW0603
    _initial_path = path


def get_initial_path() -> Path | None:
    """Get the initial path to open when the IDE starts.

    Returns:
        The initial path, or None if not set.
    """
    return _initial_path
