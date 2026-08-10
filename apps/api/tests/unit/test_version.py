"""Unit tests for the version reader (TB105).

Tests must be RED before infrastructure/version.py is created.
REQ-PFB-CONTRACT-01 (version field), design §6.4.
"""

from __future__ import annotations

import re
from importlib.metadata import PackageNotFoundError
from unittest.mock import patch

import pytest

from wheel_vocabulary.infrastructure.version import get_package_version


@pytest.mark.unit
def test_get_version_returns_string() -> None:
    """get_package_version() returns a non-empty semver string."""
    result = get_package_version()
    assert isinstance(result, str)
    assert len(result) > 0
    assert re.match(r"^\d+\.\d+\.\d+", result), f"Not a semver string: {result!r}"


@pytest.mark.unit
def test_get_version_fallback() -> None:
    """When importlib.metadata raises PackageNotFoundError, fallback is '0.0.0'."""
    with patch(
        "wheel_vocabulary.infrastructure.version.metadata_version",
        side_effect=PackageNotFoundError("wheel-vocabulary"),
    ):
        result = get_package_version()
    assert result == "0.0.0"
