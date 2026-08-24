"""Interpreter pin — REQ-003-001, AC-003-01 (Phase 1, task 1.1).

`spacy 3.8.15` declares `thinc<8.4.0,>=8.3.12` and never resolves thinc 9.x;
`apps/api/uv.lock` resolves `thinc==8.3.13`, which publishes wheels for
cp312, cp313 **and** cp314. `spacy 3.8.15` itself publishes wheels for cp312
and cp313 only — no cp314 — making spaCy, not thinc, the narrowest
constraint in the dependency chain. Before this pin, `apps/api/.venv` could
resolve to an interpreter newer than spaCy supports as a prebuilt wheel:
`uv add` would still succeed and then attempt a source build. A green
`uv add` is not evidence of a working install (design §OQ-3).

`requires-python` states what is *supported* (`>=3.12,<3.14`, bounded by
spaCy's wheel matrix). `.python-version` states what is *tested*: it stays
pinned to exactly 3.12, the single interpreter this project runs its suite
against, which matters with a pinned statistical model. The two are allowed
to differ, and do, on purpose.

Pins the interpreter version, `requires-python`'s upper bound, and mypy's
`python_version` so the three cannot drift apart. AC-003-01 scenario 3 (wheel
install, not source build) is not assertable from inside a running
interpreter — the actual install-time behaviour was verified once out of
band via the `uv add` install log, recorded in this slice's apply-progress
artifact. Remediation (verify-report WARNING-5) adds an automated proxy for
the same scenario: `uv.lock` — the pinned resolution `uv sync` reads — is a
static artifact this suite CAN inspect, so the tests below assert the locked
`spacy`/`thinc` entries carry a `cp312` wheel rather than only an `sdist`.

AC-003-01, all three scenarios (scenario 3 via the `uv.lock` proxy below).
"""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path

import pytest

_API_ROOT = Path(__file__).resolve().parents[2]
_PYPROJECT = _API_ROOT / "pyproject.toml"
_UV_LOCK = _API_ROOT / "uv.lock"
_WHEEL_ONLY_PACKAGES = ("spacy", "thinc")


def _pyproject() -> dict[str, object]:
    return tomllib.loads(_PYPROJECT.read_text(encoding="utf-8"))


def _uv_lock() -> dict[str, object]:
    return tomllib.loads(_UV_LOCK.read_text(encoding="utf-8"))


def _locked_package(name: str) -> dict[str, object]:
    lock = _uv_lock()
    packages = lock["package"]
    assert isinstance(packages, list)
    matches = [package for package in packages if package.get("name") == name]
    message = f"expected exactly one locked entry for {name!r}, found {len(matches)}"
    assert len(matches) == 1, message
    return matches[0]


@pytest.mark.unit
def test_the_resolved_interpreter_is_312() -> None:
    """AC-003-01 scenario 1: the venv resolves to the pinned interpreter."""
    assert (sys.version_info.major, sys.version_info.minor) == (3, 12)


@pytest.mark.unit
def test_requires_python_excludes_314_and_above() -> None:
    """AC-003-01 scenario 2: the declared bound cannot silently drift upward."""
    project = _pyproject()["project"]
    assert isinstance(project, dict)

    requires_python = project["requires-python"]

    assert requires_python == ">=3.12,<3.14"


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


# --------------------------------------------------------------------------
# Remediation (verify-report WARNING-5) — AC-003-01 scenario 3, automated.
#
# "Installs from a wheel, not a source build" cannot be observed from inside
# a running interpreter (the module docstring above records that correctly,
# and the human-verified `uv add` install log remains the primary evidence).
# But `apps/api/uv.lock` — the pinned dependency resolution `uv sync` reads
# — is a static, versioned artifact this test CAN inspect: if the locked
# entry for a package carries no wheel matching the pinned interpreter's ABI
# tag, `uv sync` would have to fall back to a source build for it. This is
# the automatable proxy the docstring above said scenario 3 lacked.
# --------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.parametrize("package_name", _WHEEL_ONLY_PACKAGES)
def test_the_locked_resolution_carries_a_cp312_wheel_not_only_an_sdist(
    package_name: str,
) -> None:
    """AC-003-01 scenario 3: `uv.lock` pins at least one prebuilt `cp312`
    wheel for `spacy` and `thinc` — the two packages the module docstring
    identifies as the narrowest constraint in the dependency chain. A locked
    entry with zero matching wheels would force `uv sync` to attempt a
    source build, which is exactly the failure mode this pin exists to
    prevent (design §OQ-3)."""
    package = _locked_package(package_name)
    wheels = package.get("wheels")
    assert isinstance(wheels, list)
    assert wheels, f"{package_name} has no locked wheels at all"

    cp312_wheels = [
        wheel
        for wheel in wheels
        if isinstance(wheel, dict) and "cp312" in str(wheel.get("url", ""))
    ]
    assert cp312_wheels, f"{package_name} has no locked wheel matching cp312"


@pytest.mark.unit
def test_the_locked_spacy_entry_resolves_to_the_pinned_version() -> None:
    """Sanity check on the lock lookup itself: confirms `_locked_package`
    reaches the real, current `spacy` entry rather than a stale or
    mistargeted one that would make the wheel check above vacuous."""
    package = _locked_package("spacy")

    assert package["version"] == "3.8.15"
