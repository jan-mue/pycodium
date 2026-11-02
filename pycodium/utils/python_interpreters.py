"""Discover Python interpreters relevant to the opened project."""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path

from pythonfinder import Finder  # pyright: ignore[reportMissingTypeStubs]

logger = logging.getLogger(__name__)


def discover_python_interpreters(project_root: Path, current_interpreter: str = "") -> list[dict[str, str]]:
    """Prefer project environments, then active environments and PATH interpreters."""
    interpreters: list[dict[str, str]] = []
    seen: set[Path] = set()

    def add_interpreter(path: Path, version: str = "") -> None:
        if not path.is_file():
            return
        prefix = path.parent.parent
        is_environment = (prefix / "pyvenv.cfg").is_file() or (prefix / "conda-meta").is_dir()
        # uv environments can share a base executable while having different packages.
        key = prefix.resolve() if is_environment else path.resolve()
        if key in seen:
            return
        if not version:
            try:
                result = subprocess.run(  # noqa: S603
                    [str(path), "--version"], capture_output=True, text=True, timeout=2, check=True
                )
            except (OSError, subprocess.SubprocessError):
                logger.warning("Cannot inspect Python interpreter %s", path, exc_info=True)
                return
            version = result.stdout.strip() or result.stderr.strip()
        if is_environment:
            version = f"{version} ({prefix.name})"
        seen.add(key)
        interpreters.append({"path": str(path), "version": version})

    def add_environment(prefix: Path) -> None:
        for executable in (prefix / "bin/python", prefix / "Scripts/python.exe"):
            add_interpreter(executable)

    for root in (project_root, *project_root.parents):
        for name in (".venv", "venv", ".env", "env"):
            add_environment(root / name)
        if interpreters:
            break

    for variable in ("VIRTUAL_ENV", "CONDA_PREFIX"):
        if prefix := os.environ.get(variable):
            add_environment(Path(prefix))
    if current_interpreter:
        add_interpreter(Path(current_interpreter))

    try:
        for info in Finder().system_finder.find_all_python_versions():
            if info.path:
                add_interpreter(info.path, f"Python {info.version_str}")
    except OSError:
        logger.warning("Cannot discover Python interpreters on PATH", exc_info=True)
    if not interpreters:
        add_interpreter(Path(sys.executable))
    return interpreters
