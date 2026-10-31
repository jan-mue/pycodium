"""Project environment discovery and executable alias regressions."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from pycodium.utils.python_interpreters import discover_python_interpreters

if TYPE_CHECKING:
    from pathlib import Path

    from pytest_mock import MockerFixture


@pytest.fixture(autouse=True)
def discovery_environment(mocker: MockerFixture, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VIRTUAL_ENV", raising=False)
    monkeypatch.delenv("CONDA_PREFIX", raising=False)
    finder = mocker.patch("pycodium.utils.python_interpreters.Finder").return_value
    finder.system_finder.find_all_python_versions.return_value = []
    mocker.patch(
        "pycodium.utils.python_interpreters.subprocess.run", return_value=mocker.Mock(stdout="Python 3.13.0", stderr="")
    )


def create_environment(prefix: Path, executable: str = "bin/python") -> Path:
    path = prefix / executable
    path.parent.mkdir(parents=True)
    path.touch()
    (prefix / "pyvenv.cfg").touch()
    return path


def test_project_venv_precedes_path_interpreters(
    tmp_path: Path, mocker: MockerFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    python = create_environment(tmp_path / "project/.venv")
    other = tmp_path / "unrelated"
    other.mkdir()
    monkeypatch.chdir(other)
    finder = mocker.patch("pycodium.utils.python_interpreters.Finder").return_value
    system_python = tmp_path / "python3"
    system_python.touch()
    finder.system_finder.find_all_python_versions.return_value = [mocker.Mock(path=system_python, version_str="3.12.0")]
    interpreters = discover_python_interpreters(python.parent.parent.parent)
    assert [item["path"] for item in interpreters] == [str(python), str(system_python)]
    assert ".venv" in interpreters[0]["version"]
    finder.find_all_python_versions.assert_not_called()


def test_nested_project_finds_parent_venv(tmp_path: Path) -> None:
    python = create_environment(tmp_path / ".venv")
    child = tmp_path / "src/package"
    child.mkdir(parents=True)
    assert discover_python_interpreters(child)[0]["path"] == str(python)


def test_windows_environment_layout(tmp_path: Path) -> None:
    python = create_environment(tmp_path / ".venv", "Scripts/python.exe")
    assert discover_python_interpreters(tmp_path)[0]["path"] == str(python)


def test_uv_environments_remain_distinct_from_shared_executable(
    tmp_path: Path, mocker: MockerFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    base = tmp_path / "base/python"
    base.parent.mkdir()
    base.touch()
    alias = base.with_name("python3")
    alias.symlink_to(base)
    project_python = create_environment(tmp_path / "project/.venv")
    project_python.unlink()
    project_python.symlink_to(base)
    active_python = create_environment(tmp_path / "active")
    active_python.unlink()
    active_python.symlink_to(base)
    monkeypatch.setenv("VIRTUAL_ENV", str(active_python.parent.parent))
    finder = mocker.patch("pycodium.utils.python_interpreters.Finder").return_value
    finder.system_finder.find_all_python_versions.return_value = [
        mocker.Mock(path=base, version_str="3.13.0"),
        mocker.Mock(path=alias, version_str="3.13.0"),
        mocker.Mock(path=project_python, version_str="3.13.0"),
    ]
    interpreters = discover_python_interpreters(tmp_path / "project")
    assert [item["path"] for item in interpreters] == [str(project_python), str(active_python), str(base)]
