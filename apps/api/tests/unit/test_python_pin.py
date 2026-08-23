"""Interpreter pin — REQ-003-001, AC-003-01 (Phase 1, task 1.1).

`thinc 9.1.1` publishes wheels for **cp312 only**, the narrowest constraint
in the dependency chain. Before this pin, `apps/api/.venv` resolved to a
newer interpreter than either package supports as a prebuilt wheel: `uv add`
would still succeed and then attempt a source build. A green `uv add` is not
evidence of a working install (design §OQ-3).

Pins the interpreter version, `requires-python`'s upper bound, and mypy's
`python_version` so the three cannot drift apart. AC-003-01 scenario 3 (wheel
install, not source build) is not assertable from inside a running
interpreter — verified once out of band via the `uv add` install log,
recorded in this slice's apply-progress artifact.

AC-003-01, scenarios 1 and 2.
"""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path

import pytest

_API_ROOT = Path(__file__).resolve().parents[2]
_PYPROJECT = _API_ROOT / "pyproject.toml"


def _pyproject() -> dict[str, object]:
    return tomllib.loads(_PYPROJECT.read_text(encoding="utf-8"))


@pytest.mark.unit
def test_the_resolved_interpreter_is_312() -> None:
    """AC-003-01 scenario 1: the venv resolves to the pinned interpreter."""
    assert (sys.version_info.major, sys.version_info.minor) == (3, 12)


@pytest.mark.unit
def test_requires_python_excludes_313_and_above() -> None:
    """AC-003-01 scenario 2: the declared bound cannot silently drift upward."""
    project = _pyproject()["project"]
    assert isinstance(project, dict)

    requires_python = project["requires-python"]

    assert requires_python == ">=3.12,<3.13"


@pytest.mark.unit
def test_mypy_python_version_agrees_with_the_pinned_runtime() -> None:
    """AC-003-01 scenario 2: the declared bound, the runtime, and mypy agree."""
    tool = _pyproject()["tool"]
    assert isinstance(tool, dict)
    mypy_config = tool["mypy"]
    assert isinstance(mypy_config, dict)

    mypy_python_version = mypy_config["python_version"]

    assert mypy_python_version == "3.12"
    assert mypy_python_version == f"{sys.version_info.major}.{sys.version_info.minor}"
