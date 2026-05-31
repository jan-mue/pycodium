"""Constants for the PyCodium project."""

from pathlib import Path

PROJECT_ROOT_DIR = Path(__file__).parent.parent

# Environment variable for passing initial path from CLI to backend subprocess
INITIAL_PATH_ENV_VAR = "PYCODIUM_INITIAL_PATH"
